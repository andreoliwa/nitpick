==============
flake8-nitpick
==============

.. image:: https://img.shields.io/pypi/v/flake8-nitpick.svg
        :target: https://pypi.python.org/pypi/flake8-nitpick

.. image:: https://pyup.io/repos/github/andreoliwa/flake8-nitpick/shield.svg
     :target: https://pyup.io/repos/github/andreoliwa/flake8-nitpick/
     :alt: Updates

Flake8 plugin to reuse the same lint configuration across multiple Python projects.

A "nitpick code style" is a `TOML <https://github.com/toml-lang/toml>`_ file with settings that should be present in config files from other tools. E.g.:

- ``pyproject.toml`` and ``setup.cfg`` (used by `flake8 <http://flake8.pycqa.org/>`_, `black <https://black.readthedocs.io/>`_, `isort <https://isort.readthedocs.io/>`_, `mypy <https://mypy.readthedocs.io/>`_);
- ``.pylintrc`` (used by `pylint <https://pylint.readthedocs.io/>`_ config);
- more files to come.

Quick setup
-----------

Simply install the package (in a virtualenv or globally, wherever) and run ``flake8``:

.. code-block:: console

    $ pip install -U flake8-nitpick
    $ flake8

You will see warnings if your project configuration is different than `the default style file <https://raw.githubusercontent.com/andreoliwa/flake8-nitpick/master/nitpick-style.toml>`_.

Configure your own style file
-----------------------------

Change your project config on ``pyproject.toml``, and configure your own style like this:

.. code-block:: ini

    [tool.nitpick]
    style = "https://raw.githubusercontent.com/andreoliwa/flake8-nitpick/master/nitpick-style.toml"

You can set ``style`` with any local file or URL. E.g.: you can use the raw URL of a `GitHub Gist <https://gist.github.com>`_.

Default search order for a style file
-------------------------------------

1. A file or URL configured in the ``pyproject.toml`` file, ``[tool.nitpick]`` section, ``style`` key, as `described above <Configure your own style file>`_.

2. Any ``nitpick-style.toml`` file found in the current directory (the one in which ``flake8`` runs from) or above.

3. If no style is found, then `the default style file from GitHub <https://raw.githubusercontent.com/andreoliwa/flake8-nitpick/master/nitpick-style.toml>`_ is used.

Style file syntax
-----------------

A style file contains basically the configuration options you want to enforce in all your projects.

They are just the config to the tool, prefixed with the name of the config file.

E.g.: To `configure the black formatter <https://github.com/ambv/black#configuration-format>`_ with a line length of 120, you use this in your ``pyproject.toml``:

.. code-block:: ini

    [tool.black]
    line-length = 120

To enforce that all your projects use this same line length, add this to your ``nitpick-style.toml`` file:

.. code-block:: ini

    ["pyproject.toml".tool.black]
    line-length = 120

It's the same exact section/key, just prefixed with the config file name (``"pyproject.toml".``)

The same works for ``setup.cfg``.
To `configure mypy <https://mypy.readthedocs.io/en/latest/config_file.html#config-file-format>`_ to ignore missing imports in your project:

.. code-block:: ini

    [mypy]
    ignore_missing_imports = true

To enforce all your projects to ignore missing imports, add this to your ``nitpick-style.toml`` file:

.. code-block:: ini

    ["setup.cfg".mypy]
    ignore_missing_imports = true

Absent files
------------

To enforce that certain files should not exist in the project, you can add them to the style file.

.. code-block:: ini

    [[files.absent]]
    file = "myfile1.txt"

    [[files.absent]]
    file = "another_file.env"
    message = "This is an optional extra string to display after the warning"

Multiple files can be configured as above.
The ``message`` is optional.
