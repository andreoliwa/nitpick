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

Styles can include other styles. Just provide a list of styles to include:

.. code-block:: toml

    [nitpick.styles]
    include = ["styles/python37", "styles/poetry"]

The styles will be merged following the sequence in the list.

If a key/value pair appears in more than one sub-style, it will be overridden; the last declared key/pair will prevail.

.. _nitpick-jsonfile:

[nitpick.JSONFile]
------------------

Configure the list of filenames that should be checked by the :py:class:`nitpick.plugins.json.JSONFile` class.
See :ref:`the default package.json style <default-package-json>` for an example of usage.
