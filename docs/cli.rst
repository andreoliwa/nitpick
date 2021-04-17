.. include:: targets.rst

.. _cli:

Command-line interface
======================

.. note::

    The CLI is experimental, still under active development.

Nitpick_ has a CLI to apply changes to files automatically.

1. It doesn't work for all the plugins yet. Currently, it works for:

  - :ref:`iniplugin` (like ``setup.cfg``, ``tox.ini``, ``.editorconfig``, ``.pylintrc``, and any other ``.ini``)
  - :ref:`tomlplugin`

2. It tries to preserve the comments and the formatting of the original file.
3. Some changes still have to be done manually; Nitpick_ cannot guess how to make certain changes automatically.
4. On the CLI, the "apply mode" is the default: changes to files will be made automatically, when possible.
5. The flake8_ plugin only checks the files and doesn't make changes. This is the default for now; once the CLI becomes more stable, the "apply mode" will become the default.

If you use Git, you can review the files before committing.

The available commands are described below.

.. auto-generated-from-here

.. _cli_cmd:

Main options
------------


.. code-block::

    Usage: nitpick [OPTIONS] COMMAND [ARGS]...

      Enforce the same settings across multiple language-independent projects.

    Options:
      -p, --project DIRECTORY  Path to project root
      --offline                Offline mode: no style will be downloaded (no HTTP
                               requests at all)

      --help                   Show this message and exit.

    Commands:
      init  Create a configuration file if it doesn't exist already.
      ls    List of files configured in the Nitpick style.
      run   Apply suggestions to configuration files.

.. _cli_cmd_run:

``run``: Apply style to files
-----------------------------

At the end of execution, this command displays:

- the number of fixed violations;
- the number of violations that have to be changed manually.


.. code-block::

    Usage: nitpick run [OPTIONS] [FILES]...

      Apply suggestions to configuration files.

      You can use partial and multiple file names in the FILES argument.

    Options:
      -c, --check    Don't modify the configuration files, just print the
                     difference. Return code 0 means nothing would change. Return
                     code 1 means some files would be modified.

      -v, --verbose  Verbose logging
      --help         Show this message and exit.

.. _cli_cmd_ls:

``ls``: List configures files
-----------------------------


.. code-block::

    Usage: nitpick ls [OPTIONS] [FILES]...

      List of files configured in the Nitpick style.

      Display existing files in green and absent files in red. You can use
      partial and multiple file names in the FILES argument.

    Options:
      --help  Show this message and exit.

.. _cli_cmd_init:

``init``: Initialise a configuration file
-----------------------------------------


.. code-block::

    Usage: nitpick init [OPTIONS]

      Create a configuration file if it doesn't exist already.

    Options:
      --help  Show this message and exit.
