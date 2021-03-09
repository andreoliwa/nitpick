.. _tool_nitpick:

The [tool.nitpick] section
==========================

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

Local style
-----------

Using a file in your home directory:

.. code-block:: toml

    [tool.nitpick]
    style = "~/some/path/to/another-style.toml"

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
