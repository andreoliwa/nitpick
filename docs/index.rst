.. include:: targets.rst

Nitpick
=======

.. image:: https://img.shields.io/pypi/v/nitpick.svg
    :target: https://pypi.org/project/nitpick/
    :alt: PyPI
.. image:: https://github.com/andreoliwa/nitpick/actions/workflows/python.yaml/badge.svg
    :target: https://github.com/andreoliwa/nitpick/actions/workflows/python.yaml
    :alt: GitHub Workflow
.. image:: https://readthedocs.org/projects/nitpick/badge/?version=latest
    :target: https://nitpick.rtfd.io/en/latest/?badge=latest
    :alt: Documentation Status
.. image:: https://coveralls.io/repos/github/andreoliwa/nitpick/badge.svg
    :target: https://coveralls.io/github/andreoliwa/nitpick
    :alt: Coveralls
.. image:: https://api.codeclimate.com/v1/badges/61e0cdc48e24e76a0460/maintainability
    :target: https://codeclimate.com/github/andreoliwa/nitpick
    :alt: Maintainability
.. image:: https://api.codeclimate.com/v1/badges/61e0cdc48e24e76a0460/test_coverage
    :target: https://codeclimate.com/github/andreoliwa/nitpick
    :alt: Test Coverage
.. image:: https://img.shields.io/pypi/pyversions/nitpick.svg
    :target: https://pypi.org/project/nitpick/
    :alt: Supported Python versions
.. image:: https://img.shields.io/pypi/l/nitpick.svg
    :target: https://pypi.org/project/nitpick/
    :alt: Project License
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black
    :alt: Code style: black
.. image:: https://img.shields.io/badge/renovate-enabled-brightgreen.svg
    :target: https://renovatebot.com
    :alt: Renovate
.. image:: https://img.shields.io/badge/%20%20%F0%9F%93%A6%F0%9F%9A%80-semantic--release-e10079.svg
    :target: https://github.com/semantic-release/semantic-release
    :alt: semantic-release

Command-line tool and flake8_ plugin to enforce the same settings across multiple language-independent projects.

Useful if you maintain multiple projects and are tired of copying/pasting the same INI/TOML/YAML/JSON keys and values over and over, in all of them.

The CLI now has a ``nitpick fix`` command that modifies configuration files directly (pretty much like black_ and isort_ do with Python files).
See :ref:`cli` for more info.

Many more features are planned for the future, check `the roadmap <https://github.com/andreoliwa/nitpick/projects/1>`_.

.. note::

    This project is still a work in progress, so the API is not fully defined:

        - :ref:`the-style-file` syntax might have changes before the 1.0 stable release;
        - The numbers in the ``NIP*`` error codes might change; don't fully rely on them;
        - See also :ref:`breaking-changes`.

.. toctree::
   :caption: Contents:

   quickstart
   styles
   configuration
   library
   nitpick_section
   cli
   flake8_plugin
   plugins
   troubleshooting
   contributing
   authors

.. toctree::
   :maxdepth: 1
   :caption: API Reference:

   source/modules

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

To Do List
==========

.. todolist::
