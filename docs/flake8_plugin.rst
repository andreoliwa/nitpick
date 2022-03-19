.. include:: targets.rst

.. note::

  Try running Nitpick with the new :ref:`cli` instead of a flake8 plugin.

  In the future, there are plans to :issue:`make flake8 an optional dependency <166>`.

.. _flake8_plugin:

Flake8_ plugin
==============

Nitpick_ is not a proper flake8_ plugin; it piggybacks on flake8's messaging system though.

Flake8 lints Python files; Nitpick "lints" configuration (text) files instead.

To act like a flake8 plugin, Nitpick does the following:

1. Find `any Python file in your project <Main Python file_>`_;
2. Use the first Python file found and ignore other Python files in the project.
3. Check the style file and compare with the configuration/text files.
4. Report violations on behalf of that Python file, and not on the configuration file that's actually wrong.

So, if you have a violation on ``setup.cfg``, it will be reported like this::

  ./tasks.py:0:1: NIP323 File setup.cfg: [flake8]max-line-length is 80 but it should be like this:
  [flake8]
  max-line-length = 120

Notice the ``tasks.py`` at the beginning of the line, and not ``setup.cfg``.

.. note::

  To run Nitpick as a Flake8 plugin, the project must have *at least one* Python file*.

  If your project is not a Python project, creating a ``dummy.py`` file on the root of the project is enough.

Pre-commit hook and flake8
--------------------------

Currently, the default pre-commit_ hook uses flake8_ in an `unconventional and not recommended way <https://github.com/pre-commit/pre-commit.com/pull/353#issuecomment-632224465>`_.

:gitref:`It calls flake8 directly <.pre-commit-hooks.yaml#L5>`::

  flake8 --select=NIP

This current default pre-commit hook (called ``nitpick``) is a placeholder for the future, :issue:`when flake8 will be only an optional dependency <166>`.

Why ``always_run: true``?
~~~~~~~~~~~~~~~~~~~~~~~~~

This in intentional, because `Nitpick is not a conventional flake8 plugin <flake8_plugin_>`_.

Since flake8 only lints Python files, the pre-commit hook will only run when a Python file is modified.
It won't run when a config/text changes.

An example: suppose you're using a remote Nitpick style (`like the style from WeMake <https://github.com/wemake-services/wemake-python-styleguide/blob/master/styles/nitpick-style.toml>`_).

At the moment, their style currently checks ``setup.cfg`` only.

Suppose they change or add an option on their `isort.toml <https://github.com/wemake-services/wemake-python-styleguide/blob/master/styles/isort.toml>`_ file.

If the nitpick pre-commit hook had ``always_run: false`` and ``pass_filenames: true``, your local ``setup.cfg`` would only be verified:

1. If a Python file was changed.
2. If you ran ``pre-commit run --all-files``.

So basically the pre-commit hook would be useless to guarantee that your config files would always match the remote style... which is precisely the purpose of Nitpick.

.. note::

  To avoid this, use the :gitref:`other pre-commit hooks <.pre-commit-hooks.yaml#L10>`, the ones that call the Nitpick CLI directly instead of running ``flake8``.

Root dir of the project
-----------------------

You should run Nitpick_ in the *root dir* of your project.

A directory is considered a root dir if it contains one of the following files:

  - ``.pre-commit-config.yaml`` (pre-commit_)
  - ``pyproject.toml``
  - ``setup.py``
  - ``setup.cfg``
  - ``requirements*.txt``
  - ``Pipfile`` (Pipenv_)
  - ``tox.ini`` (tox_)
  - ``package.json`` (JavaScript, NodeJS)
  - ``Cargo.*`` (Rust)
  - ``go.mod``, ``go.sum`` (Golang)
  - ``app.py`` and ``wsgi.py`` (`Flask CLI`_)
  - ``autoapp.py`` (Flask_)
  - ``manage.py`` (Django_)

Main Python file
----------------

On the `root dir of the project`_ Nitpick searches for a main Python file.
Every project must have at least one ``*.py`` file, otherwise flake8_ won't even work.

Those are the Python files that are considered:

- ``setup.py``
- ``app.py`` and ``wsgi.py`` (`Flask CLI`_)
- ``autoapp.py``
- ``manage.py``
- any ``*.py`` file
