.. include:: targets.rst

.. _configuration:

Configuration
=============

:ref:`the-style-file` for your project should be configured in the ``[tool.nitpick]`` section of the configuration file.

Possible configuration files (in order of precedence):

.. auto-generated-start-config-file

1. ``.nitpick.toml``
2. ``pyproject.toml``

.. auto-generated-end-config-file

The first file found will be used; the other files will be ignored.

Run the ``nipick init`` CLI command to create a config file (:ref:`cli_cmd_init`).

To configure your own style, you can either use ``nitpick init``:

.. code-block:: sh

    $ nitpick init /path/to/your-style-file.toml

or edit your configuration file and set the ``style`` option:

.. code-block:: toml

    [tool.nitpick]
    style = "/path/to/your-style-file.toml"

You can set ``style`` with any local file or URL.

Remote style
------------

Use the URL of the remote file.

If it's hosted on GitHub, use any of the following formats:

GitHub URL scheme (``github://`` or ``gh://``) pinned to a specific version:

.. code-block:: toml

    [tool.nitpick]
    style = "github://andreoliwa/nitpick@v0.33.1/nitpick-style.toml"
    # or
    style = "gh://andreoliwa/nitpick@v0.33.1/nitpick-style.toml"

The ``@`` syntax is used to get a Git reference (commit, tag, branch).
It is similar to the syntax used by ``pip`` and ``pipx``:

- `pip install - VCS Support - Git <https://pip.pypa.io/en/stable/topics/vcs-support/#git>`_;
- `pypa/pipx: Installing from Source Control <https://pypa.github.io/pipx/#installing-from-source-control>`_.

If no Git reference is provided, the default GitHub branch will be used (for Nitpick, it's ``develop``):

.. code-block:: toml

    [tool.nitpick]
    style = "github://andreoliwa/nitpick/nitpick-style.toml"
    # or
    style = "gh://andreoliwa/nitpick/nitpick-style.toml"

    # It has the same effect as providing the default branch explicitly:
    style = "github://andreoliwa/nitpick@develop/nitpick-style.toml"
    # or
    style = "gh://andreoliwa/nitpick@develop/nitpick-style.toml"

A regular GitHub URL also works. The corresponding raw URL will be used.

.. code-block:: toml

    [tool.nitpick]
    style = "https://github.com/andreoliwa/nitpick/blob/v0.33.1/nitpick-style.toml"

Or use the raw GitHub URL directly:

.. code-block:: toml

    [tool.nitpick]
    style = "https://raw.githubusercontent.com/andreoliwa/nitpick/v0.33.1/nitpick-style.toml"

You can also use the raw URL of a `GitHub Gist <https://gist.github.com>`_:

.. code-block:: toml

    [tool.nitpick]
    style = "https://gist.githubusercontent.com/andreoliwa/f4fccf4e3e83a3228e8422c01a48be61/raw/ff3447bddfc5a8665538ddf9c250734e7a38eabb/remote-style.toml"

If your style is on a private GitHub repo, you can provide the token directly on the URL.
Or you can use an environment variable to avoid keeping secrets in plain text.

.. code-block:: toml

    [tool.nitpick]
    # A literal token
    style = "github://p5iCG5AJuDgY@some-user/a-private-repo@some-branch/nitpick-style.toml"

    # Or reading the secret value from the MY_AUTH_KEY env var
    style = "github://$MY_AUTH_KEY@some-user/a-private-repo@some-branch/nitpick-style.toml"

.. note::

    A literal token cannot start with a ``$``.
    All tokens must not contain any ``@`` or ``:`` characters.

Style inside Python package
---------------------------

The style file can be fetched from an installed Python package.

Example of a use case: you create a custom flake8 extension and you also want to distribute a (versioned) Nitpick style bundled as a resource inside the Python package (:issue:`check out this issue: Get style file from python package · Issue #202 <202#issuecomment-703345486>`).

Python package URL scheme is ``pypackage://`` or ``py://``:

.. code-block:: toml

    [tool.nitpick]
    style = "pypackage://some_python_package/styles/nitpick-style.toml"
    # or
    style = "py://some_python_package/styles/nitpick-style.toml"

Thanks to `@isac322 <https://github.com/isac322>`_ for this feature.

Cache
-----

Remote styles can be cached to avoid unnecessary HTTP requests.
The cache can be configured with the ``cache`` key; see the examples below.

By default, remote styles will be cached for **one hour**.
This default will also be used if the ``cache`` key has an invalid value.

Expiring after a predefined time
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The cache can be set to expire after a defined time unit.
Use the format ``cache = "<integer> <time unit>"``.
*Time unit* can be one of these (plural or singular, it doesn't matter):

- ``minutes`` / ``minute``
- ``hours`` / ``hour``
- ``days`` / ``day``
- ``weeks`` / ``week``

To cache for 15 minutes:

.. code-block:: toml

    [tool.nitpick]
    style = "https://example.com/remote-style.toml"
    cache = "15 minutes"

To cache for 1 day:

.. code-block:: toml

    [tool.nitpick]
    style = "https://example.com/remote-style.toml"
    cache = "1 day"

Forever
~~~~~~~

With this option, once the style(s) are cached, they never expire.

.. code-block:: toml

    [tool.nitpick]
    style = "https://example.com/remote-style.toml"
    cache = "forever"

Never
~~~~~

With this option, the cache is never used.
The remote style file(s) are always looked-up and a HTTP request is always executed.

.. code-block:: toml

    [tool.nitpick]
    style = "https://example.com/remote-style.toml"
    cache = "never"

Clearing
~~~~~~~~

The cache files live in a subdirectory of your project: ``/path/to/your/project/.cache/nitpick/``.
To clear the cache, simply remove this directory.

Local style
-----------

Using a file in your home directory:

.. code-block:: toml

    [tool.nitpick]
    style = "~/some/path/to/another-style.toml"

Using a relative path from another project in your hard drive:

.. code-block:: toml

    [tool.nitpick]
    style = "../another-project/another-style.toml"

.. _multiple_styles:

Multiple styles
---------------

You can also use multiple styles and mix local files and URLs.

Example of usage: the ``[tool.nitpick]`` table on :gitref:`Nitpick's own pyproject.toml <pyproject.toml#L1-L7>`.

.. code-block:: toml

    [tool.nitpick]
    style = [
        "/path/to/first.toml",
        "/another/path/to/second.toml",
        "https://example.com/on/the/web/third.toml"
    ]

.. note::

  The order is important: each style will override any keys that might be set by the previous ``.toml`` file.

  If a key is defined in more than one file, the value from the last file will prevail.

Override a remote style
-----------------------

You can use a remote style as a starting point, and override settings on your local style file.

Use ``./`` to indicate the local style:

.. code-block:: toml

    [tool.nitpick]
    style = [
        "https://example.com/on/the/web/remote-style.toml",
        "./my-local-style.toml",
    ]

For Windows users: even though the path separator is a backslash, use the example above as-is.
The "dot-slash" is a convention for Nitpick_ to know this is a local style file.
