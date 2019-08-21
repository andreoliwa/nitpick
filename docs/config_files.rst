.. _config_files:

Configuration files
===================

Below are the currently supported configuration files.

.. auto-generated-from-here

.. _pyprojecttomlfile:

pyproject.toml
--------------

Checker for the `pyproject.toml <https://poetry.eustace.io/docs/pyproject/>`_ config file.

See also `PEP 518 <https://www.python.org/dev/peps/pep-0518/>`_.

Example: :ref:`the Python 3.7 default <default-python-3-7>`.
There are many other examples in :ref:`defaults`.

.. _setupcfgfile:

setup.cfg
---------

Checker for the `setup.cfg <https://docs.python.org/3/distutils/configfile.html>`_ config file.

Example: :ref:`flake8 configuration <default-flake8>`.

.. _precommitfile:

.pre-commit-config.yaml
-----------------------

Checker for the `.pre-commit-config.yaml <https://pre-commit.com/#pre-commit-configyaml---top-level>`_ file.

Example: :ref:`the default pre-commit hooks <default-pre-commit-hooks>`.

.. _jsonfile:

JSON files
----------

Checker for any JSON file.

First, configure the list of files to be checked in the :ref:`[nitpick.JsonFile] section <nitpick-jsonfile>`.

Then add the configuration for the file name you just declared.

Example: :ref:`the default config for package.json <default-package-json>`.
