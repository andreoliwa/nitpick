.. include:: targets.rst

Styles
======

.. _the-style-file:

The style file
--------------

A "`Nitpick`_ code style" is a TOML_ file with the settings that should be present in config files from other tools.

Example of a style:

.. code-block:: toml

    ["pyproject.toml".tool.black]
    line-length = 120

    ["pyproject.toml".tool.poetry.dev-dependencies]
    pylint = "*"

    ["setup.cfg".flake8]
    ignore = "D107,D202,D203,D401"
    max-line-length = 120
    inline-quotes = "double"

    ["setup.cfg".isort]
    line_length = 120
    multi_line_output = 3
    include_trailing_comma = true
    force_grid_wrap = 0
    combine_as_imports = true

This example style will assert that:

- ... black_, isort_ and flake8_ have a line length of 120;
- ... flake8_ and isort_ are configured with the above options in ``setup.cfg``;
- ... Pylint_ is present as a Poetry_ dev dependency in ``pyproject.toml``.

.. _configure-your-own-style:

Configure your own style
------------------------

After creating your own TOML_ file with your style, add it to your ``pyproject.toml`` file. See :ref:`the [tool.nitpick] section <tool_nitpick>` for details.

You can also check :ref:`some pre-configured examples <examples>`, and copy/paste/change configuration from them.

Default search order for a style
--------------------------------

1. A file or URL configured in the ``pyproject.toml`` file, ``[tool.nitpick]`` section, ``style`` key, as described in :ref:`tool_nitpick`.

2. Any `nitpick-style.toml`_ file found in the current directory (the one in which flake8_ runs from) or above.

3. If no style is found, then the `default style file`_ from GitHub is used.

Style file syntax
-----------------

A style file contains basically the configuration options you want to enforce in all your projects.

They are just the config to the tool, prefixed with the name of the config file.

E.g.: To configure the black_ formatter with a line length of 120, you use this in your ``pyproject.toml``:

.. code-block:: toml

    [tool.black]
    line-length = 120

To enforce that all your projects use this same line length, add this to your `nitpick-style.toml`_ file:

.. code-block:: toml

    ["pyproject.toml".tool.black]
    line-length = 120

It's the same exact section/key, just prefixed with the config file name (``"pyproject.toml".``)

The same works for ``setup.cfg``.

To `configure mypy <https://mypy.readthedocs.io/en/latest/config_file.html#config-file-format>`_ to ignore missing imports in your project, this is needed on ``setup.cfg``:

.. code-block:: ini

    [mypy]
    ignore_missing_imports = true

To enforce all your projects to ignore missing imports, add this to your `nitpick-style.toml`_ file:

.. code-block:: toml

    ["setup.cfg".mypy]
    ignore_missing_imports = true

.. _breaking-changes:

Breaking style changes
----------------------

.. warning::

    Below are the breaking changes in the style before the API is stable.
    If your style was working in a previous version and now it's not, check below.

``missing_message`` key was removed
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``missing_message`` was removed. Use ``[nitpick.files.present]`` now.

Before:

.. code-block:: toml

    [nitpick.files."pyproject.toml"]
    missing_message = "Install poetry and run 'poetry init' to create it"

Now:

.. code-block:: toml

    [nitpick.files.present]
    "pyproject.toml" = "Install poetry and run 'poetry init' to create it"
