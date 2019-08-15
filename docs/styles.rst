.. _styles:

Styles
======

Configure your own style file
-----------------------------

Change your project config on ``pyproject.toml``, and configure your own style like this:

.. code-block::

    [tool.nitpick]
    style = "/path/to/your-style-file.toml"

You can set ``style`` with any local file or URL. E.g.: you can use the raw URL of a `GitHub Gist <https://gist.github.com>`_.

Using a file in your home directory:

.. code-block::

    [tool.nitpick]
    style = "~/some/path/to/another-style.toml"

You can also use multiple styles and mix local files and URLs:

.. code-block::

    [tool.nitpick]
    style = ["/path/to/first.toml", "/another/path/to/second.toml", "https://example.com/on/the/web/third.toml"]

The order is important: each style will override any keys that might be set by the previous .toml file.
If a key is defined in more than one file, the value from the last file will prevail.

Default search order for a style file
-------------------------------------

1. A file or URL configured in the ``pyproject.toml`` file, ``[tool.nitpick]`` section, ``style`` key, as described above.

2. Any ``nitpick-style.toml`` file found in the current directory (the one in which ``flake8`` runs from) or above.

3. If no style is found, then `the default style file from GitHub <https://raw.githubusercontent.com/andreoliwa/nitpick/v0.20.0/nitpick-style.toml>`_ is used.

Style file syntax
-----------------

A style file contains basically the configuration options you want to enforce in all your projects.

They are just the config to the tool, prefixed with the name of the config file.

E.g.: To `configure the black formatter <https://github.com/python/black#configuration-format>`_ with a line length of 120, you use this in your ``pyproject.toml``:

.. code-block::

    [tool.black]
    line-length = 120

To enforce that all your projects use this same line length, add this to your ``nitpick-style.toml`` file:

.. code-block::

    ["pyproject.toml".tool.black]
    line-length = 120

It's the same exact section/key, just prefixed with the config file name (``"pyproject.toml".``)

The same works for ``setup.cfg``.

To `configure mypy <https://mypy.readthedocs.io/en/latest/config_file.html#config-file-format>`_ to ignore missing imports in your project:

.. code-block::

    [mypy]
    ignore_missing_imports = true

To enforce all your projects to ignore missing imports, add this to your ``nitpick-style.toml`` file:

.. code-block::

    ["setup.cfg".mypy]
    ignore_missing_imports = true
