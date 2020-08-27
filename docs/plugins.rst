.. include:: targets.rst
.. _plugins:

Plugins
=======

Below are the currently included plugins.

.. auto-generated-from-here

.. _setupcfgplugin:

setup.cfg
---------

Checker for the `setup.cfg <https://docs.python.org/3/distutils/configfile.html>`_ config file.

Example: :ref:`flake8 configuration <default-flake8>`.

.. _pyprojecttomlplugin:

pyproject.toml
--------------

Checker for `pyproject.toml <https://github.com/python-poetry/poetry/blob/master/docs/docs/pyproject.md>`_.

See also `PEP 518 <https://www.python.org/dev/peps/pep-0518/>`_.

Example: :ref:`the Python 3.7 default <default-python-3-7>`.
There are many other examples in :ref:`defaults`.

.. _precommitplugin:

.pre-commit-config.yaml
-----------------------

Checker for the `.pre-commit-config.yaml <https://pre-commit.com/#pre-commit-configyaml---top-level>`_ file.

Example: :ref:`the default pre-commit hooks <default-pre-commit-hooks>`.

.. _jsonplugin:

JSON files
----------

Checker for any JSON file.

Add the configurations for the file name you wish to check.
Example: :ref:`the default config for package.json <default-package-json>`.

.. _textplugin:

Text files
----------

Checker for text files.

To check if ``some.txt`` file contains the lines ``abc`` and ``def`` (in any order):

.. code-block:: toml

    [["some.txt".contains]]
    line = "abc"

    [["some.txt".contains]]
    line = "def"
