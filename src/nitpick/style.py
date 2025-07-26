"""Style parsing and merging."""

from __future__ import annotations

import os
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import timedelta
from enum import auto
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, Iterable, Iterator, Sequence, cast

import attr
import click
import requests
import tomlkit
from flatten_dict import flatten, unflatten
from furl import furl
from identify import identify
from loguru import logger
from more_itertools import always_iterable, peekable
from requests import Session
from requests_cache import CachedSession
from slugify import slugify
from strenum import LowercaseStrEnum
from toml import TomlDecodeError

from nitpick import compat, fields
from nitpick.blender import SEPARATOR_FLATTEN, TomlDoc, custom_reducer, custom_splitter, search_json
from nitpick.constants import (
    CACHE_DIR_NAME,
    CACHE_EXPIRATION_DEFAULTS,
    DOT,
    GIT_AT_REFERENCE,
    GITHUB_COM,
    GITHUB_COM_API,
    GITHUB_COM_QUERY_STRING_TOKEN,
    GITHUB_COM_RAW,
    JMEX_NITPICK_STYLES_INCLUDE,
    MERGED_STYLE_TOML,
    NITPICK_STYLE_TOML,
    PROJECT_NAME,
    PROJECT_OWNER,
    PYTHON_PYPROJECT_TOML,
    REGEX_CACHE_UNIT,
    TOML_EXTENSION,
    WRITE_STYLE_MAX_ATTEMPTS,
    CachingEnum,
    Flake8OptionEnum,
)
from nitpick.exceptions import Deprecation, QuitComplainingError, pretty_exception
from nitpick.generic import glob_files, url_to_python_path
from nitpick.plugins.info import FileInfo
from nitpick.schemas import BaseStyleSchema, NitpickSectionSchema, flatten_marshmallow_errors
from nitpick.violations import Fuss, Reporter, StyleViolations

try:
    # DeprecationWarning: The dpath.util package is being deprecated.
    # All util functions have been moved to dpath package top level.
    from dpath import merge as dpath_merge
except ImportError:  # pragma: no cover
    from dpath.util import merge as dpath_merge

GITHUB_API_SESSION = Session()  # Dedicated session to reuse connections


if TYPE_CHECKING:
    from marshmallow import Schema

    from nitpick.core import Project
    from nitpick.plugins.base import NitpickPlugin
    from nitpick.typedefs import JsonDict


@lru_cache
def builtin_resources_root() -> Path:
    """Built-in resources root."""
    return Path(str(compat.files("nitpick.resources")))


@lru_cache
def repo_root() -> Path:
    """Repository root, 3 levels up from the resources root."""
    return builtin_resources_root().parent.parent.parent


def builtin_styles() -> Iterable[Path]:
    """List the built-in styles."""
    yield from builtin_resources_root().glob("**/*.toml")


@lru_cache
def github_default_branch(api_url: str, *, token: str | None = None) -> str:
    """Get the default branch from the GitHub repo using the API.

    For now, for URLs without an authorization token embedded, the request is
    not authenticated on GitHub, so it might hit a rate limit with:
    ``requests.exceptions.HTTPError: 403 Client Error: rate limit exceeded for url``

    This function is using ``lru_cache()`` as a simple memoizer, trying to avoid this rate limit error.
    """
    headers = {"Authorization": f"token {token}"} if token else None
    response = GITHUB_API_SESSION.get(api_url, headers=headers)
    response.raise_for_status()

    return response.json()["default_branch"]


def parse_cache_option(cache_option: str) -> tuple[CachingEnum, timedelta | int]:
    """Parse the cache option provided on pyproject.toml.

    If no cache is provided or is invalid, the default is *one hour*.
    """
    clean_cache_option = cache_option.strip().upper() if cache_option else ""
    try:
        caching = CachingEnum[clean_cache_option]
        logger.info(f"Simple cache option: {caching.name}")
    except KeyError:
        caching = CachingEnum.EXPIRES

    expires_after = CACHE_EXPIRATION_DEFAULTS[caching]
    if caching is CachingEnum.EXPIRES and clean_cache_option:
        for match in REGEX_CACHE_UNIT.finditer(clean_cache_option):
            plural_unit = match.group("unit").lower() + "s"
            number = int(match.group("number"))
            logger.info(f"Cache option with unit: {number} {plural_unit}")
            expires_after = timedelta(**{plural_unit: number})
            break
        else:
            logger.warning(f"Invalid cache option: {clean_cache_option}. Defaulting to 1 hour")

    return caching, expires_after


@dataclass()
class StyleManager:  # pylint: disable=too-many-instance-attributes
    """Include styles recursively from one another."""

    project: Project
    offline: bool
    cache_option: str

    _cache_dir: Path = field(init=False)
    _fixed_name_classes: set = field(init=False)

    def __post_init__(self) -> None:
        """Initialize dependant fields."""
        self._merged_styles: JsonDict = {}
        self._already_included: set[str] = set()
        self._dynamic_schema_class: type = BaseStyleSchema
        self._style_fetcher_manager = StyleFetcherManager(self.offline, self.cache_dir, self.cache_option)
        self._config_validator = ConfigValidator(self.project)
        self.rebuild_dynamic_schema()

    def __hash__(self):
        """Calculate hash on hashable items so lru_cache knows how to cache data from this class."""
        return hash((self.project, self.offline, self.cache_option))

    @property
    def cache_dir(self) -> Path:
        """Clear the cache directory (on the project root or on the current directory)."""
        try:
            path = self._cache_dir
        except AttributeError:
            self._cache_dir = path = self.project.root / CACHE_DIR_NAME / PROJECT_NAME
            # TODO: fix: check if the merged style file is still needed
            #  if not, this line can be removed
            path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def get_default_style_url(github=False) -> furl:
        """Return the URL of the default style/preset."""
        if github:
            from nitpick import __version__  # pylint: disable=import-outside-toplevel  # noqa: PLC0415

            return GitHubURL(PROJECT_OWNER, PROJECT_NAME, f"v{__version__}", (NITPICK_STYLE_TOML,)).long_protocol_url

        return furl(scheme=Scheme.PY, host=PROJECT_NAME, path=["resources", "presets", PROJECT_NAME])

    def find_initial_styles(self, configured_styles: Sequence[str], base: str | None = None) -> Iterator[Fuss]:
        """Find the initial style(s) and include them.

        base is the URL for the source of the initial styles, and is used to
        resolve relative references. If omitted, defaults to the project root.
        """
        project_root = self.project.root
        base_url = furl(base or project_root.resolve().as_uri())

        if configured_styles:
            chosen_styles = configured_styles
            config_file = base_url.path.segments[-1] if base else PYTHON_PYPROJECT_TOML
            logger.info(f"Using styles configured in {config_file}: {', '.join(chosen_styles)}")
        else:
            paths = glob_files(project_root, [NITPICK_STYLE_TOML])
            if paths:
                chosen_styles = [sorted(paths)[0].expanduser().resolve().as_uri()]
                log_message = "Using local style found climbing the directory tree"
            else:
                yield Reporter().make_fuss(StyleViolations.NO_STYLE_CONFIGURED)
                return
            logger.info(f"{log_message}: {chosen_styles[0]}")

        yield from self.include_multiple_styles(
            self._style_fetcher_manager.normalize_url(ref, base_url) for ref in chosen_styles
        )

    def include_multiple_styles(self, chosen_styles: Iterable[furl]) -> Iterator[Fuss]:
        """Include a list of styles (or just one) into this style tree."""
        for style_url in chosen_styles:
            yield from self._include_style(style_url)

    def _include_style(self, style_url: furl) -> Iterator[Fuss]:
        if style_url.url in self._already_included:
            return
        self._already_included.add(style_url.url)

        file_contents = self._style_fetcher_manager.fetch(style_url)
        if file_contents is None:
            return

        # generate a 'human readable' version of the URL; a relative path for local files
        # and the URL otherwise.
        display_name = style_url.url
        if style_url.scheme == "file":
            path = url_to_python_path(style_url)
            with suppress(ValueError):
                path = path.relative_to(self.project.root)
            display_name = str(path)

        read_toml_dict = self._read_toml(file_contents, display_name)

        # normalize sub-style URIs, before merging
        sub_styles = [
            self._style_fetcher_manager.normalize_url(ref, style_url)
            for ref in always_iterable(search_json(read_toml_dict, JMEX_NITPICK_STYLES_INCLUDE, []))
        ]
        if sub_styles:
            read_toml_dict.setdefault("nitpick", {}).setdefault("styles", {})["include"] = [
                str(url) for url in sub_styles
            ]

        toml_dict, validation_errors = self._config_validator.validate(read_toml_dict)

        if validation_errors:
            yield Reporter(FileInfo(self.project, display_name)).make_fuss(
                StyleViolations.INVALID_CONFIG, flatten_marshmallow_errors(validation_errors)
            )

        dpath_merge(self._merged_styles, flatten(toml_dict, custom_reducer(SEPARATOR_FLATTEN)))

        yield from self.include_multiple_styles(sub_styles)

    def _read_toml(self, file_contents: str, display_name: str) -> JsonDict:
        toml = TomlDoc(string=file_contents)
        try:
            read_toml_dict = toml.as_object
        # TODO: refactor: replace by TOMLKitError when using tomlkit only in the future:
        except TomlDecodeError as err:
            # If the TOML itself could not be parsed, we can't go on
            raise QuitComplainingError(
                Reporter(FileInfo(self.project, display_name)).make_fuss(
                    StyleViolations.INVALID_TOML, exception=pretty_exception(err)
                )
            ) from err
        return read_toml_dict

    def merge_toml_dict(self) -> JsonDict:
        """Merge all included styles into a TOML (actually JSON) dictionary."""
        merged_dict = unflatten(self._merged_styles, custom_splitter(SEPARATOR_FLATTEN))
        # TODO: fix: check if the merged style file is still needed
        merged_style_path: Path = self.cache_dir / MERGED_STYLE_TOML
        toml = TomlDoc(obj=merged_dict)

        attempt = 1
        while attempt < WRITE_STYLE_MAX_ATTEMPTS:
            try:
                merged_style_path.write_text(toml.reformatted)
                break
            except OSError:
                attempt += 1

        return merged_dict

    @staticmethod
    def file_field_pair(filename: str, base_file_class: type[NitpickPlugin]) -> dict[str, fields.Field]:
        """Return a schema field with info from a config file class."""
        unique_filename_with_underscore = slugify(filename, separator="_")

        kwargs = {"data_key": filename}
        if base_file_class.validation_schema:
            file_field = fields.Nested(base_file_class.validation_schema, **kwargs)
        else:
            # For some files (e.g.: TOML/ INI files), there is no strict schema;
            # it can be anything they allow.
            # It's out of Nitpick's scope to validate those files.
            file_field = fields.Dict(fields.String, **kwargs)
        return {unique_filename_with_underscore: file_field}

    def load_fixed_name_plugins(self) -> set[type[NitpickPlugin]]:
        """Separate classes with fixed file names from classes with dynamic files names."""
        try:
            fixed_name_classes = self._fixed_name_classes
        except AttributeError:
            fixed_name_classes = self._fixed_name_classes = {
                plugin_class
                for plugin_class in self.project.plugin_manager.hook.plugin_class()  # pylint: disable=no-member
                if plugin_class.filename
            }
        return fixed_name_classes

    def rebuild_dynamic_schema(self) -> None:
        """Rebuild the dynamic Marshmallow schema when needed, adding new fields that were found on the style."""
        new_files_found: dict[str, fields.Field] = {}

        fixed_name_classes = self.load_fixed_name_plugins()

        for subclass in fixed_name_classes:
            new_files_found.update(self.file_field_pair(subclass.filename, subclass))

        # Only recreate the schema if new fields were found.
        if new_files_found:
            self._dynamic_schema_class = type("DynamicStyleSchema", (self._dynamic_schema_class,), new_files_found)

    def _find_subclasses(self, data, handled_tags, new_files_found):
        for possible_file in data:
            found_subclasses = []
            for file_tag in identify.tags_from_filename(possible_file):
                handler_subclass = handled_tags.get(file_tag)
                if handler_subclass:
                    found_subclasses.append(handler_subclass)

            for found_subclass in found_subclasses:
                new_files_found.update(self.file_field_pair(possible_file, found_subclass))


@dataclass(repr=True)  # TODO: refactor: use attrs instead
class ConfigValidator:
    """Validate a nitpick configuration."""

    project: Project

    def validate(self, config_dict: dict) -> tuple[dict, dict]:
        """Validate an already parsed toml file."""
        validation_errors = {}
        toml_dict = {}
        for key, value_dict in config_dict.items():
            info = FileInfo.create(self.project, key)
            toml_dict[info.path_from_root] = value_dict
            validation_errors.update(self._validate_item(key, info, value_dict))
        return toml_dict, validation_errors

    def _validate_item(self, key, info, value_dict):
        validation_errors = {}
        if key == PROJECT_NAME:
            schemas = [NitpickSectionSchema]
        else:
            schemas = peekable(self._get_validation_schemas_for_file(info))
            if not schemas:
                validation_errors[key] = [BaseStyleSchema.error_messages["unknown"]]
        valid_schema, all_errors = self._validate_schemas(info, schemas, value_dict)
        if not valid_schema:
            Deprecation.jsonfile_section(all_errors)
            validation_errors.update(all_errors)

        return validation_errors

    def _get_validation_schemas_for_file(self, info):
        for plugin_class in self.project.plugin_manager.hook.can_handle(info=info):  # pylint: disable=no-member
            yield plugin_class.validation_schema

    def _validate_schemas(self, info, schemas, value_dict):
        all_errors = {}
        for schema in schemas:
            errors = self._validate_schema(schema, info.path_from_root, value_dict)
            if not errors:
                # When multiple schemas match a file type, exit when a valid schema is found
                return True, {}

            all_errors.update(errors)

        return False, all_errors

    @staticmethod
    def _validate_schema(schema: type[Schema], path_from_root: str, original_data: JsonDict) -> dict[str, list[str]]:
        """Validate the schema for the file."""
        if not schema:
            return {}

        inherited_schema = schema is not BaseStyleSchema
        data_to_validate = original_data if inherited_schema else {path_from_root: None}
        local_errors = schema().validate(data_to_validate)
        if local_errors and inherited_schema:
            local_errors = {path_from_root: local_errors}
        return local_errors


class Scheme(LowercaseStrEnum):
    """URL schemes."""

    # keep-sorted start
    FILE = auto()
    GH = auto()
    GITHUB = auto()
    HTTP = auto()
    HTTPS = auto()
    PY = auto()
    PYPACKAGE = auto()
    # keep-sorted end


@dataclass()
class StyleFetcherManager:
    """Manager that controls which fetcher to be used given a protocol."""

    offline: bool
    cache_dir: Path
    cache_option: str

    session: CachedSession = field(init=False)
    fetchers: dict[str, StyleFetcher] = field(init=False)
    schemes: tuple[str] = field(init=False)

    def __post_init__(self):
        """Initialize dependant properties."""
        caching, expire_after = parse_cache_option(self.cache_option)
        # honour caching headers on the response when an expiration time has
        # been set meaning that the server can dictate cache expiration
        # overriding the local expiration time. This may need to become a
        # separate configuration option in future.
        cache_control = caching is CachingEnum.EXPIRES
        self.session = CachedSession(
            str(self.cache_dir / "styles"), expire_after=expire_after, cache_control=cache_control
        )
        self.fetchers = fetchers = _get_fetchers(self.session)

        # used to test if a string URL is relative or not. These strings
        # *include the colon*.
        protocols = {prot for fetcher in fetchers.values() for prot in fetcher.protocols}
        self.schemes = tuple(f"{prot}:" for prot in protocols)

    def normalize_url(self, url: str | furl, base: furl) -> furl:
        """Normalize a style URL.

        The URL is made absolute against base, then passed to individual fetchers
        to produce a canonical version of the URL.
        """
        if isinstance(url, str) and not url.startswith(self.schemes):
            url = self._fetcher_for(base).preprocess_relative_url(url)
        absolute = base.copy().join(url)
        return self._fetcher_for(absolute).normalize(absolute)

    def fetch(self, url: furl) -> str | None:
        """Determine which fetcher to be used and fetch from it.

        Returns None when offline is True and the fetcher would otherwise
        require a connection.
        """
        fetcher = self._fetcher_for(url)
        if self.offline and fetcher.requires_connection:
            return None

        return fetcher.fetch(url)

    def _fetcher_for(self, url: furl) -> StyleFetcher:
        """Determine which fetcher to be used.

        Try a fetcher by domain first, then by protocol scheme.
        """
        fetcher = self.fetchers.get(url.host) if url.host else None
        if not fetcher:
            fetcher = self.fetchers.get(url.scheme)
        if not fetcher:
            msg = f"URL protocol {url.scheme!r} is not supported"
            raise RuntimeError(msg)
        return fetcher


@dataclass(frozen=True)
class StyleFetcher:
    """Base class of all fetchers, it encapsulates get/fetch from a specific source."""

    requires_connection: ClassVar[bool] = False

    # only set when requires_connection is True
    session: CachedSession | None = None
    protocols: tuple[str, ...] = ()
    domains: tuple[str, ...] = ()

    def __post_init__(self):
        """Validate that session has been passed in for requires_connection == True."""
        if self.requires_connection and self.session is None:
            msg = "session is required"
            raise ValueError(msg)

    def preprocess_relative_url(self, url: str) -> str:  # pylint: disable=no-self-use
        """Preprocess a relative URL.

        Only called for urls that lack a scheme (at the very least), being resolved
        against a base URL that matches this specific fetcher.
        """
        return url

    def _normalize_url_path(self, url: furl) -> furl:  # pylint: disable=no-self-use
        """Normalize the path component of a URL."""
        if not url.path.segments[-1].endswith(TOML_EXTENSION):
            url = url.copy()
            url.path.segments[-1] = f"{url.path.segments[-1]}{TOML_EXTENSION}"
        return url

    def _normalize_scheme(self, scheme: str) -> str:  # pylint: disable=no-self-use
        """Normalize the scheme component of a URL."""
        return scheme

    def normalize(self, url: furl) -> furl:
        """Normalize a URL.

        Produces a canonical URL, meant to be used to uniquely identify a style resource.

        - The base name has .toml appended if not already ending in that extension
        - Individual fetchers can further normalize the path and scheme.
        """
        new_scheme = self._normalize_scheme(url.scheme)
        if new_scheme != url.scheme:
            url = url.copy().set(scheme=new_scheme)
        return self._normalize_url_path(url)

    def fetch(self, url: furl) -> str:
        """Fetch a style from a specific fetcher."""
        raise NotImplementedError


def _get_fetchers(session: CachedSession) -> dict[str, StyleFetcher]:
    def _factory(klass: type[StyleFetcher]) -> StyleFetcher:
        return klass(session) if klass.requires_connection else klass()

    fetchers = (_factory(FileFetcher), _factory(HttpFetcher), _factory(GitHubFetcher), _factory(PythonPackageFetcher))
    return dict(_fetchers_to_pairs(fetchers))


def _fetchers_to_pairs(fetchers: Iterable[StyleFetcher]) -> Iterator[tuple[str, StyleFetcher]]:
    for fetcher in fetchers:
        for protocol in fetcher.protocols:
            yield protocol, fetcher
        for domain in fetcher.domains:
            yield domain, fetcher


@dataclass(frozen=True)
class FileFetcher(StyleFetcher):  # pylint: disable=too-few-public-methods
    """Fetch a style from a local file."""

    protocols: tuple[str, ...] = (Scheme.FILE,)  # type: ignore[assignment]

    def preprocess_relative_url(self, url: str) -> str:
        """Preprocess a relative URL.

        Only called for urls that lack a scheme (at the very least), being resolved
        against a base URL that matches this specific fetcher.

        Relative paths are file paths; any ~ home reference is expanded at this point.
        """
        # We have to expand ~ values before trying to resolve a path as a file URL
        path = Path(url).expanduser()
        # return absolute paths as URLs as on Windows they could otherwise not resolve
        # cleanly against a file:// base. Relative paths should use POSIX conventions.
        return path.as_uri() if path.is_absolute() else path.as_posix()

    def _normalize_url_path(self, url: furl) -> furl:
        local_path = url_to_python_path(super()._normalize_url_path(url))
        return furl(local_path.resolve().as_uri())

    def fetch(self, url: furl) -> str:
        """Fetch a style from a local file."""
        return url_to_python_path(url).read_text(encoding="UTF-8")


@dataclass(frozen=True)
class GitHubURL:
    """Represent a GitHub URL, created from a URL or from its parts."""

    owner: str
    repository: str
    git_reference: str
    path: tuple[str, ...] = ()
    auth_token: str | None = None
    query_params: tuple[tuple[str, str], ...] | None = None

    @property
    def default_branch(self) -> str:
        """Default GitHub branch."""
        return github_default_branch(self.api_url.url, token=self.token)  # function is memoized

    @property
    def token(self) -> str | None:
        """Token encoded in this URL.

        If present and it starts with a ``$``, it will be replaced with the
        value of the environment corresponding to the remaining part of the
        string.
        """
        token = self.auth_token
        if token is not None and token.startswith("$"):
            token = os.getenv(token[1:])
        return token

    @property
    def authorization_header(self) -> dict[str, str] | None:
        """Authorization header encoded in this URL."""
        token = self.token
        return {"Authorization": f"token {token}"} if token else None

    @property
    def git_reference_or_default(self) -> str:
        """Return the Git reference if informed, or return the default branch."""
        return self.git_reference or self.default_branch

    @property
    def url(self) -> furl:
        """Default URL built from attributes."""
        return furl(
            scheme=Scheme.HTTPS,
            host=GITHUB_COM,
            path=[self.owner, self.repository, "blob", self.git_reference_or_default, *self.path],
            query_params=self.query_params,
        )

    @property
    def raw_content_url(self) -> furl:
        """Raw content URL for this path."""
        return furl(
            scheme=Scheme.HTTPS,
            host=GITHUB_COM_RAW,
            path=[self.owner, self.repository, self.git_reference_or_default, *self.path],
            query_params=self.query_params,
        )

    @classmethod
    def from_furl(cls, url: furl) -> GitHubURL:
        """Create an instance from a parsed URL in any accepted format.

        See the code for ``test_parsing_github_urls()`` for more examples.
        """
        auth_token = url.username or url.args.get(GITHUB_COM_QUERY_STRING_TOKEN)
        query_params = tuple((key, value) for key, value in url.args.items() if key != GITHUB_COM_QUERY_STRING_TOKEN)

        if url.scheme in GitHubFetcher.protocols:
            owner = url.host
            repo_with_git_reference, *path = url.path.segments
            repo, _, git_reference = repo_with_git_reference.partition(GIT_AT_REFERENCE)
        else:  # github.com URL (raw.githubusercontent.com is handled by the HTTP fetcher)
            # Skip the 'blob' component in the github.com URL.
            owner, repo, _, git_reference, *path = url.path.segments

        if path and not path[-1]:
            # strip trailing slashes
            *path, _ = path

        return cls(owner, repo, git_reference, tuple(path), auth_token, query_params)

    @property
    def api_url(self) -> furl:
        """API URL for this repo."""
        return furl(scheme=Scheme.HTTPS, host=GITHUB_COM_API, path=["repos", self.owner, self.repository])

    @property
    def short_protocol_url(self) -> furl:
        """Short protocol URL (``gh``)."""
        return self._build_url(cast("str", Scheme.GH))

    @property
    def long_protocol_url(self) -> furl:
        """Long protocol URL (``github``)."""
        return self._build_url(cast("str", Scheme.GITHUB))

    def _build_url(self, scheme: str) -> furl:
        if self.git_reference and self.git_reference != self.default_branch:
            at_reference = f"{GIT_AT_REFERENCE}{self.git_reference}"
        else:
            at_reference = ""
        return furl(scheme=scheme, host=self.owner, path=[f"{self.repository}{at_reference}", *self.path])


@dataclass(frozen=True)
class HttpFetcher(StyleFetcher):
    """Fetch a style from an http/https server."""

    requires_connection = True

    protocols: tuple[str, ...] = (Scheme.HTTP, Scheme.HTTPS)  # type: ignore[assignment]

    def fetch(self, url: furl) -> str:
        """Fetch the style from a web location."""
        try:
            contents = self._download(url)
        except requests.ConnectionError as err:
            logger.exception(f"Request failed with {err}")
            click.secho(
                f"The URL {url} could not be downloaded. Either your network is unreachable or the URL is broken."
                f" Check the URL, fix your connection, or use "
                f" {Flake8OptionEnum.OFFLINE.as_flake8_flag()} / {Flake8OptionEnum.OFFLINE.as_envvar()}=1",
                fg="red",
                err=True,
            )
            return ""
        return contents

    def _download(self, url: furl, **kwargs) -> str:
        logger.info(f"Downloading style from {url}")
        if self.session is None:
            msg = "No session provided to fetcher"
            raise RuntimeError(msg)
        response = self.session.get(url.url, **kwargs)
        response.raise_for_status()
        return response.text


@dataclass(frozen=True)
class GitHubFetcher(HttpFetcher):  # pylint: disable=too-few-public-methods
    """Fetch styles from GitHub repositories."""

    protocols: tuple[str, ...] = (Scheme.GH, Scheme.GITHUB)  # type: ignore[assignment,has-type]
    domains: tuple[str, ...] = (GITHUB_COM,)

    def _normalize_scheme(self, scheme: str) -> str:  # pylint: disable=no-self-use
        # Use github:// instead of gh:// in the canonical URL
        return Scheme.GITHUB if scheme == Scheme.GH else scheme  # type: ignore[return-value]

    def _download(self, url: furl, **kwargs) -> str:
        github_url = GitHubURL.from_furl(url)
        kwargs.setdefault("headers", github_url.authorization_header)
        return super()._download(github_url.raw_content_url, **kwargs)


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
        if resource_path and not resource_path[-1]:
            # strip trailing slash
            *resource_path, _ = resource_path

        *resource_path, resource_name = resource_path
        return cls(import_path=DOT.join([package_name, *resource_path]), resource_name=resource_name)

    @property
    def content_path(self) -> Path:
        """Raw path of resource file."""
        return Path(str(compat.files(self.import_path))) / self.resource_name


@dataclass(frozen=True)
class PythonPackageFetcher(StyleFetcher):  # pylint: disable=too-few-public-methods
    """Fetch a style from an installed Python package.

    URL schemes:
    - ``py://import/path/of/style/file/<style_file_name>``
    - ``pypackage://import/path/of/style/file/<style_file_name>``

    E.g. ``py://some_package/path/nitpick.toml``.
    """

    protocols: tuple[str, ...] = (Scheme.PY, Scheme.PYPACKAGE)  # type: ignore[assignment]

    def _normalize_scheme(self, scheme: str) -> str:  # noqa: ARG002
        # Always use the shorter py:// scheme name in the canonical URL.
        return cast("str", Scheme.PY)

    def fetch(self, url: furl) -> str:
        """Fetch the style from a Python package."""
        package_url = PythonPackageURL.from_furl(url)
        return package_url.content_path.read_text(encoding="UTF-8")


@attr.mutable(kw_only=True)
class BuiltinStyle:  # pylint: disable=too-few-public-methods
    """A built-in style file in TOML format."""

    formatted: str
    path_from_resources_root: str

    identify_tag: str = attr.field(init=False)
    name: str = attr.field(init=False)
    url: str = attr.field(init=False)
    files: list[str] = attr.field(init=False)

    @classmethod
    def from_path(cls, resource_path: Path, library_dir: Path | None = None) -> BuiltinStyle:
        """Create a style from its path."""
        without_suffix = resource_path.with_suffix("")
        if library_dir:
            # Style in a directory
            from_resources_root = without_suffix.relative_to(library_dir)
            bis = BuiltinStyle(
                formatted=str(without_suffix),
                path_from_resources_root=from_resources_root.as_posix(),
            )
        else:
            # Style from the built-in library
            package_path = resource_path.relative_to(builtin_resources_root().parent.parent)
            from_resources_root = without_suffix.relative_to(builtin_resources_root())
            root, *path_remainder = package_path.parts
            path_remainder_without_suffix = (*path_remainder[:-1], without_suffix.parts[-1])
            bis = BuiltinStyle(
                formatted=furl(scheme=Scheme.PY, host=root, path=path_remainder_without_suffix).url,
                path_from_resources_root=from_resources_root.as_posix(),
            )
        bis.identify_tag = from_resources_root.parts[0]
        toml_dict = tomlkit.loads(resource_path.read_text(encoding="UTF-8"))

        keys = list(toml_dict.keys())
        keys.remove(PROJECT_NAME)
        bis.files = keys

        try:
            # Intentionally break the doc generation when styles don't have [nitpick.meta]name
            meta = toml_dict["nitpick"]["meta"]  # pylint: disable=invalid-sequence-index
            bis.name = meta["name"]
            bis.url = meta.get("url")
        except KeyError as err:
            msg = f"Style file missing [nitpick.meta] information: {bis}"
            raise SyntaxError(msg) from err
        return bis
