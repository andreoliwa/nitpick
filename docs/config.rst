.. _config:

Config
======

Files that should exist
-----------------------

To enforce that certain files should exist in the project, you can add them to the style file as a dictionary of "file name" and "extra message".

Use an empty string to not display any extra message.

.. code-block::

    [nitpick.files.present]
    ".editorconfig" = ""
    "CHANGELOG.md" = "A project should have a changelog"

Files that should be deleted
----------------------------

To enforce that certain files should not exist in the project, you can add them to the style file.

.. code-block::

    [nitpick.files.absent]
    "some_file.txt" = "This is an optional extra string to display after the warning"
    "another_file.env" = ""

Multiple files can be configured as above.
The message is optional.
