"""Support for ``py`` schemes."""
from dataclasses import dataclass
from itertools import chain
from typing import Tuple
from urllib.parse import urlparse

from nitpick.style.fetchers.base import StyleFetcher

try:
    from importlib.abc import Traversable  # type: ignore[attr-defined]
    from importlib.resources import files  # type: ignore[attr-defined]
except ImportError:
    from importlib_resources import files
    from importlib_resources.abc import Traversable


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

        import_path = ".".join(chain((package_name,), resource_path[:-1]))
        resource_name = resource_path[-1]

        return cls(import_path=import_path, resource_name=resource_name)

    @property
    def raw_content_url(self) -> Traversable:
        """Raw path of resource file."""
        return files(self.import_path).joinpath(self.resource_name)


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
        return package_url.raw_content_url.read_text()
