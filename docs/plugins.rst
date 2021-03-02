.. include:: targets.rst
.. _plugins:

Plugins
=======

Nitpick uses plugins to handle configuration files.

There are plans to add plugins that handle certain file types, specific files, and user plugins.
Check `the roadmap <https://github.com/andreoliwa/nitpick/projects/1>`_.

Below are the currently included plugins.

.. auto-generated-from-here

.. _pyprojecttomlplugin:

pyproject.toml
--------------

Enforce config on `pyproject.toml (PEP 518) <https://www.python.org/dev/peps/pep-0518/#file-format>`_.

See also `the [tool.poetry] section of the pyproject.toml file
<https://github.com/python-poetry/poetry/blob/master/docs/docs/pyproject.md>`_.

Example: :ref:`the Python 3.8 default <default-python-3-8>`.
There are many other examples in :ref:`defaults`.

.. _precommitplugin:

.pre-commit-config.yaml
-----------------------

Enforce configuration for `.pre-commit-config.yaml <https://pre-commit.com/#pre-commit-configyaml---top-level>`_.

Example: :ref:`the default pre-commit hooks <default-pre-commit-hooks>`.

.. _iniplugin:

INI files
---------

Enforce config on INI files.

Examples of ``.ini`` files handled by this plugin:

- `setup.cfg <setup-cfg>`_
- `.editorconfig <EditorConfig>`_

Example of Nitpick styles enforcing values on INI files: :ref:`flake8 configuration <default-flake8>`.

.. _jsonplugin:

JSON files
----------

Enforce configurations for any JSON file.

Add the configurations for the file name you wish to check.
Example: :ref:`the default config for package.json <default-package-json>`.

.. _textplugin:

Text files
----------

Enforce configuration on text files.

To check if ``some.txt`` file contains the lines ``abc`` and ``def`` (in any order):

.. code-block:: toml

    [["some.txt".contains]]
    line = "abc"

    [["some.txt".contains]]
    line = "def"
