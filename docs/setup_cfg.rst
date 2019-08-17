.. _setup_cfg:

File: setup.cfg
===============

Comma separated values
----------------------

On ``setup.cfg``, some keys are lists of multiple values separated by commas, like ``flake8.ignore``.

On the style file, it's possible to indicate which key/value pairs should be treated as multiple values instead of an exact string.
Multiple keys can be added.

.. code-block::

    [nitpick.files."setup.cfg"]
    comma_separated_values = ["flake8.ignore", "isort.some_key", "another_section.another_key"]
