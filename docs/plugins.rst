.. include:: targets.rst

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

Style example: :ref:`Python 3.8 version constraint <example-python-3-8>`.
There are :ref:`many other examples here <examples>`.

.. _precommitplugin:

.pre-commit-config.yaml
-----------------------

Enforce configuration for `.pre-commit-config.yaml <https://pre-commit.com/#pre-commit-configyaml---top-level>`_.

Style example: :ref:`the default pre-commit hooks <example-pre-commit-hooks>`.

.. _iniplugin:

INI files
---------

Enforce config on INI files.

Examples of ``.ini`` files handled by this plugin:

- `setup.cfg <https://docs.python.org/3/distutils/configfile.html>`_
- `.editorconfig <https://editorconfig.org/>`_
- `tox.ini <https://github.com/tox-dev/tox>`_
- `.pylintrc <https://pylint.readthedocs.io/en/latest/user_guide/run.html#command-line-options>`_

Style examples enforcing values on INI files: :ref:`flake8 configuration <example-flake8>`.

.. _jsonplugin:

JSON files
----------

Enforce configurations for any JSON file.

Add the configurations for the file name you wish to check.
Style example: :ref:`the default config for package.json <example-package-json>`.

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
