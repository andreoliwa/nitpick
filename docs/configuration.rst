.. _configuration:

Configuration
=============

:ref:`the-style-file` for your project should be configured in the ``[tool.nitpick]`` section of your ``pyproject.toml`` file.

You can configure your own style like this:

.. code-block:: toml

    [tool.nitpick]
    style = "/path/to/your-style-file.toml"

You can set ``style`` with any local file or URL.

Remote style
------------

Use the URL of the remote file. If it's hosted on GitHub, use the raw GitHub URL:

.. code-block:: toml

    [tool.nitpick]
    style = "https://raw.githubusercontent.com/andreoliwa/nitpick/v0.25.0/nitpick-style.toml"

You can also use the raw URL of a `GitHub Gist <https://gist.github.com>`_:

.. code-block:: toml

    [tool.nitpick]
    style = "https://gist.githubusercontent.com/andreoliwa/f4fccf4e3e83a3228e8422c01a48be61/raw/ff3447bddfc5a8665538ddf9c250734e7a38eabb/remote-style.toml"

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

You can also use multiple styles and mix local files and URLs:

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
