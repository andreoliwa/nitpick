"""Support for ``py`` schemes."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from itertools import chain
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

import attr
import tomlkit

from nitpick import PROJECT_NAME, compat
from nitpick.constants import DOT, SLASH
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


@dataclass(unsafe_hash=True)
class PythonPackageURL:
    """Represent a resource file in installed Python package."""

    import_path: str
    resource_name: str

    @classmethod
    def parse_url(cls, url: str) -> PythonPackageURL:
        """Create an instance by parsing a URL string in any accepted format.

        See the code for ``test_parsing_python_package_urls()`` for more examples.
        """
        parsed_url = urlparse(url)
        package_name = parsed_url.netloc
        resource_path = parsed_url.path.strip("/").split("/")

        import_path = DOT.join(chain((package_name,), resource_path[:-1]))
        resource_name = resource_path[-1]

        return cls(import_path=import_path, resource_name=resource_name)

    @property
    def raw_content_url(self) -> compat.Traversable:
        """Raw path of resource file."""
        return compat.files(self.import_path).joinpath(self.resource_name)


@dataclass(repr=True, unsafe_hash=True)
class PythonPackageFetcher(StyleFetcher):  # pylint: disable=too-few-public-methods
    """
    Fetch a style from an installed Python package.

    URL schemes:
    - ``py://import/path/of/style/file/<style_file_name>``
    - ``pypackage://import/path/of/style/file/<style_file_name>``

    E.g. ``py://some_package/path/nitpick.toml``.
    """

    protocols: tuple[str, ...] = ("py", "pypackage")

    def _do_fetch(self, url):
        package_url = PythonPackageURL.parse_url(url)
        return package_url.raw_content_url.read_text(encoding="UTF-8")


@attr.mutable(kw_only=True)
class BuiltinStyle:  # pylint: disable=too-few-public-methods
    """A built-in style file in TOML format."""

    py_url: str
    py_url_without_ext: str
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
        path_without_ext = str(resource_path.with_suffix(""))
        bis = BuiltinStyle(
            py_url=str(resource_path).replace(str(builtin_resources_root().parent.parent), "py:/"),
            py_url_without_ext=path_without_ext.replace(str(builtin_resources_root().parent.parent), "py:/"),
            path_from_repo_root=str(resource_path).replace(str(repo_root()), "").lstrip(SLASH),
            path_from_resources_root=path_without_ext.replace(str(builtin_resources_root()), "").lstrip(SLASH),
        )
        bis.pypackage_url = PythonPackageURL.parse_url(bis.py_url)
        bis.identify_tag = bis.path_from_resources_root.split(SLASH)[0]

        # FIXME: windows debugging
        from icecream import ic

        ic(bis.pypackage_url.raw_content_url)
        toml_dict = tomlkit.loads(bis.pypackage_url.raw_content_url.read_text(encoding="UTF-8"))

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
