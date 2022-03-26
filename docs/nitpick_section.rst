.. _nitpick_section:

The [nitpick] section
=====================

The [nitpick] section in :ref:`the style file <the-style-file>` contains global settings for the style.

Those are settings that either don't belong to any specific config file, or can be applied to all config files.

Minimum version
---------------

Show an upgrade message to the developer if Nitpick's version is below ``minimum_version``:

.. code-block:: toml

    [nitpick]
    minimum_version = "0.10.0"

[nitpick.files]
---------------

Files that should exist
^^^^^^^^^^^^^^^^^^^^^^^

To enforce that certain files should exist in the project, you can add them to the style file as a dictionary of "file name" and "extra message".

Use an empty string to not display any extra message.

.. code-block:: toml

    [nitpick.files.present]
    ".editorconfig" = ""
    "CHANGELOG.md" = "A project should have a changelog"

Files that should be deleted
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To enforce that certain files should not exist in the project, you can add them to the style file.

.. code-block:: toml

    [nitpick.files.absent]
    "some_file.txt" = "This is an optional extra string to display after the warning"
    "another_file.env" = ""

Multiple files can be configured as above.
The message is optional.

Comma separated values
^^^^^^^^^^^^^^^^^^^^^^

On ``setup.cfg``, some keys are lists of multiple values separated by commas, like ``flake8.ignore``.

On the style file, it's possible to indicate which key/value pairs should be treated as multiple values instead of an exact string.
Multiple keys can be added.

.. code-block:: toml

    [nitpick.files."setup.cfg"]
    comma_separated_values = ["flake8.ignore", "isort.some_key", "another_section.another_key"]

[nitpick.styles]
----------------

Styles can include other styles. Just provide a list of styles to include.

Example of usage: :gitref:`Nitpick's default style <nitpick-style.toml>`.

.. code-block:: toml

    [nitpick.styles]
    include = ["styles/python37", "styles/poetry"]

The styles will be merged following the sequence in the list. The ``.toml``
extension for each referenced file can be onitted.

Relative references are resolved relative to the URI of the style doument they
are included in according to the `normal rules of RFC 3986 <https://www.rfc-editor.org/rfc/rfc3986.html#section-5.2>`_.

E.g. for a style file located at
``gh://$GITHUB_TOKEN@foo_dev/bar_project@branchname/styles/foobar.toml`` the following
strings all reference the exact same canonical location to include:

.. code-block:: toml

    [nitpick.styles]
    include = [
      "foobar.toml",
      "../styles/foobar.toml",
      "/bar_project@branchname/styles/foobar.toml",
      "//$GITHUB_TOKEN@foo_dev/bar_project@branchname/styles/foobar.toml",
    ]

For style files on the local filesystem, the canonical path
(after symbolic links have been resolved) of the style file is used as the
base.

If a key/value pair appears in more than one sub-style, it will be overridden; the last declared key/pair will prevail.
