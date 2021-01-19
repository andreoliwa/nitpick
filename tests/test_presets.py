"""Presets."""


# FIXME[AA]: suggested presets and building blocks dir tree:
#  presets/
#    py38/
#      readthedocs.toml
#      package.toml
#    py39/
#      mkdocs.toml
#      cli.toml
#    generic.toml
#    we-make-style-guide.toml (this file contains [nitpick.styles]include=http://path/to/remote/wemake-style)
#  styles/
#    pre-commit/
#      general.toml
#      main.toml
#      ...
#    black.toml
#    flake8.toml
#    isort.toml
#    ...

# FIXME[AA]: docs: encourage people to share their styles: "if you have a style, create a pull request and add it here"
#  "why not a separate repo with styles? to make versioning easier,
#  because the default nitpick preset is tied to the release (the version is part of the preset URL)
#  if styles were in a separate repo, they would have to be kept in sync and bumped at the same time.


def test_use_default_when_none_supplied():
    """If [tool.nitpick]preset is empty, use the default existing nitpick-style.toml."""
    # FIXME[AA]:


def test_local_preset_style():
    """Test local presets and styles."""
    # .toml suffix is optional

    # [tool.nitpick]
    # preset = "/absolute/path/to/preset"
    # preset = "/absolute/path/to/preset.toml"
    # preset = "relative/path/to/preset.toml"
    # preset = "relative/path/to/preset"
    # preset = "./relative/path/to/preset.toml"
    # preset = "./relative/path/to/preset"

    # Preset().resolve_path()

    # FIXME[AA]: test both [tool.nitpick]preset= and [nitpick.styles]include=


def test_remote_http_preset_style():
    """Test downloading remote presets and styles."""
    # .toml suffix is optional

    # [tool.nitpick]
    # preset = "http://example.com/path/to/preset.toml"
    # preset = "http://example.com/path/to/preset"
    # preset = "https://example.com/path/to/preset.toml"
    # preset = "https://example.com/path/to/preset"
    # FIXME[AA]: store both remote presets and styles locally under .cache/nitpick (already with joblib or not?)


def test_include_and_exclude_styles():
    """Test including and excluding styles from a preset."""
    # [tool.nitpick]
    # presets = ["http://example.com/path/to/remote"]
    # presets = ["/absolute/path/to/local1.toml"]
    # presets = ["relative/local2.toml"]
    # exclude = ["unwanted_style"]
    # exclude = ["unwanted_style.toml"]
    # exclude = ["subdir/unwanted_style.toml", "path/to/yet/another_unwanted_style"]

    # http://example.com/path/to/preset.toml:
    style = """
    [[nitpick.style]]
    presets = [
        "some-style",
        "subdir/unwanted_style"
    ]
    exclude_files = ["something"]
    exclude_keys = ["setup.cfg"]

    # or
    add = []
    remove = []

    [[nitpick.style]]
    presets = [
        "another-style",
        "path/to/yet/another_unwanted_style",
        "../../relative/parent/style.toml"
    ]
    """
    assert style

    # [nitpick.styles]include= can be present in any .toml file, be it a preset or a style building block

    # FIXME[AA]: assert that include_sub_style("full/path/to/unwanted_style.toml") is not called


def test_expand():
    """Test expanding a preset into a full TOML file."""
    # Preset()
    # def expand(self)
    # def include_sub_style(resolved_parent_path_or_url, relative_style_path)
    # def read_contents(self)
    #   for each style in [nitpick.styles]include:
    #     include_sub_style("/resolved/parent/path/", "relative/style")
    # generate an expanded preset .toml file under .cache/nitpick (already with joblib or not?)
    # use tomlkit to generate exact TOML

    style = """
    [nitpick.styles]
    include = [
        "style-without-extension",
        "style-with-extension.toml",
        "relative/path/to/style1",
        "relative/path/to/style2.toml",
        "http://example.com/path/remote1",
        "http://example.com/path/remote2.toml",
        "/tmp_path_fixture/absolute/sub/local1",
        "/tmp_path_fixture/absolute/sub/local2.toml"
    ]
    """
    assert style
    # FIXME[AA]: check if the expanded TOML file has the expected contents
