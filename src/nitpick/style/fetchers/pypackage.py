"""Support for ``py`` schemes."""
from dataclasses import dataclass
from functools import lru_cache
from itertools import chain
from pathlib import Path
from typing import Iterable, Tuple
from urllib.parse import urlparse

import attr

from nitpick import compat
from nitpick.constants import DOT, SLASH
from nitpick.style.fetchers.base import StyleFetcher


@lru_cache()
def builtin_resources_path() -> Path:
    """Path to the built-in resources."""
    return compat.files("nitpick.resources")


def builtin_styles() -> Iterable[Path]:
    """List the built-in styles."""
    yield from builtin_resources_path().glob("**/*.toml")


@dataclass(unsafe_hash=True)
class PythonPackageURL:
    """Represent a resource file in installed Python package."""

    import_path: str
    resource_name: str

    @classmethod
    def parse_url(cls, url: str) -> "PythonPackageURL":
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

    protocols: Tuple[str, ...] = ("py", "pypackage")

    def _do_fetch(self, url):
        package_url = PythonPackageURL.parse_url(url)
        return package_url.raw_content_url.read_text(encoding="UTF-8")


@attr.mutable(kw_only=True)
class BuiltinStyle:  # pylint: disable=too-few-public-methods
    """A built-in style file in TOML format."""

    url: str
    path_from_root: str
    pypackage_url: PythonPackageURL = attr.field(init=False)
    identify_tag: str = attr.field(init=False)

    @classmethod
    def from_path(cls, resource_path: Path) -> "BuiltinStyle":
        """Create a built-in style from a resource path."""
        full_path_without_extension = str(resource_path.with_suffix(""))
        bis = BuiltinStyle(
            url=full_path_without_extension.replace(str(builtin_resources_path().parent.parent), "py:/"),
            path_from_root=full_path_without_extension.replace(str(builtin_resources_path()), "").lstrip("/"),
        )
        bis.pypackage_url = PythonPackageURL.parse_url(bis.url)
        bis.identify_tag = bis.path_from_root.split(SLASH)[0]
        return bis
