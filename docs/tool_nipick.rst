.. _tool_nitpick:

The ``[tool.nitpick]`` section
==============================

:ref:`the-style-file` for your project should be configured in the ``[tool.nitpick]`` section of your ``pyproject.toml`` file.

You can configure your own style like this:

.. code-block:: toml

    [tool.nitpick]
    style = "/path/to/your-style-file.toml"

You can set ``style`` with any local file or URL. E.g.: you can use the raw URL of a `GitHub Gist <https://gist.github.com>`_.

Using a file in your home directory:

.. code-block:: toml

    [tool.nitpick]
    style = "~/some/path/to/another-style.toml"

You can also use multiple styles and mix local files and URLs:

.. code-block:: toml

    [tool.nitpick]
    style = [
        "/path/to/first.toml",
        "/another/path/to/second.toml",
        "https://example.com/on/the/web/third.toml"
    ]

The order is important: each style will override any keys that might be set by the previous ``.toml`` file.
If a key is defined in more than one file, the value from the last file will prevail.
