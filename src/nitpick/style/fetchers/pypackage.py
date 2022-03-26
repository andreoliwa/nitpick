"""Support for ``py`` schemes."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable, cast

import attr
import tomlkit
from furl import furl

from nitpick import PROJECT_NAME, compat
from nitpick.constants import DOT
from nitpick.style.fetchers import Scheme
from nitpick.style.fetchers.base import StyleFetcher


@lru_cache()
def builtin_resources_root() -> Path:
    """Built-in resources root."""
    return compat.files("nitpick.resources")


@lru_cache()
def repo_root() -> Path:
    """Repository root, 3 levels up from the resources root."""
    return builtin_resources_root().parent.parent.parent


def builtin_styles() -> Iterable[Path]:
    """List the built-in styles."""
    yield from builtin_resources_root().glob("**/*.toml")


@dataclass(frozen=True)
class PythonPackageURL:
    """Represent a resource file in installed Python package."""

    import_path: str
    resource_name: str

    @classmethod
    def from_furl(cls, url: furl) -> PythonPackageURL:
        """Create an instance from a parsed URL in any accepted format.

        See the code for ``test_parsing_python_package_urls()`` for more examples.

        """
        package_name = url.host
        resource_path = url.path.segments
        if resource_path and resource_path[-1] == "":
            # strip trailing slash
            *resource_path, _ = resource_path

        *resource_path, resource_name = resource_path
        return cls(import_path=DOT.join([package_name, *resource_path]), resource_name=resource_name)

    @property
    def content_path(self) -> Path:
        """Raw path of resource file."""
        return compat.files(self.import_path) / self.resource_name


@dataclass(frozen=True)
class PythonPackageFetcher(StyleFetcher):  # pylint: disable=too-few-public-methods
    """
    Fetch a style from an installed Python package.

    URL schemes:
    - ``py://import/path/of/style/file/<style_file_name>``
    - ``pypackage://import/path/of/style/file/<style_file_name>``

    E.g. ``py://some_package/path/nitpick.toml``.
    """

    protocols: tuple[str, ...] = (Scheme.PY, Scheme.PYPACKAGE)  # type: ignore

    def _normalize_scheme(self, scheme: str) -> str:
        # Always use the shorter py:// scheme name in the canonical URL.
        return cast(str, Scheme.PY)

    def fetch(self, url: furl) -> str:
        """Fetch the style from a Python package."""
        package_url = PythonPackageURL.from_furl(url)
        return package_url.content_path.read_text(encoding="UTF-8")


@attr.mutable(kw_only=True)
class BuiltinStyle:  # pylint: disable=too-few-public-methods
    """A built-in style file in TOML format."""

    py_url: furl
    py_url_without_ext: furl
    path_from_repo_root: str
    path_from_resources_root: str

    pypackage_url: PythonPackageURL = attr.field(init=False)
    identify_tag: str = attr.field(init=False)
    name: str = attr.field(init=False)
    url: str = attr.field(init=False)
    files: list[str] = attr.field(init=False)

    @classmethod
    def from_path(cls, resource_path: Path) -> BuiltinStyle:
        """Create a built-in style from a resource path."""

        without_suffix = resource_path.with_suffix("")
        src_path = builtin_resources_root().parent.parent
        package_path = resource_path.relative_to(src_path)
        from_resources_root = without_suffix.relative_to(builtin_resources_root())

        root, *path_remainder = package_path.parts
        path_remainder_without_suffix = (*path_remainder[:-1], without_suffix.parts[-1])

        bis = BuiltinStyle(
            py_url=furl(scheme=Scheme.PY, host=root, path=path_remainder),
            py_url_without_ext=furl(scheme=Scheme.PY, host=root, path=path_remainder_without_suffix),
            path_from_repo_root=resource_path.relative_to(repo_root()).as_posix(),
            path_from_resources_root=from_resources_root.as_posix(),
        )
        bis.pypackage_url = PythonPackageURL.from_furl(bis.py_url)
        bis.identify_tag = from_resources_root.parts[0]

        toml_dict = tomlkit.loads(bis.pypackage_url.content_path.read_text(encoding="UTF-8"))

        keys = list(toml_dict.keys())
        keys.remove(PROJECT_NAME)
        bis.files = keys

        try:
            # Intentionally break the doc generation when styles don't have [nitpick.meta]name
            meta = toml_dict["nitpick"]["meta"]
            bis.name = meta["name"]
            bis.url = meta.get("url")
        except KeyError as err:
            raise SyntaxError(f"Style file missing [nitpick.meta] information: {bis}") from err
        return bis
