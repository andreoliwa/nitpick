.. include:: targets.rst

.. _installation_guide:

Installation guide
==================

Quick setup
-----------

To try the package, simply install it (in a virtualenv or globally, wherever) and run ``flake8``:

.. code-block:: shell

    $ pip install -U nitpick
    $ flake8

Nitpick_ will download and use the opinionated `default style file`_.

You can use it as a template to :ref:`configure-your-own-style`.

Run as a pre-commit hook (recommended)
--------------------------------------

If you use pre-commit_ on your project (you should), add this to the ``.pre-commit-config.yaml`` in your repository:

.. code-block:: yaml

    repos:
      - repo: https://github.com/andreoliwa/nitpick
        rev: v0.21.4
        hooks:
          - id: nitpick

To install the ``pre-commit`` and ``commit-msg`` Git hooks:

.. code-block:: shell

    pre-commit install --install-hooks
    pre-commit install -t commit-msg

To start checking all your code against the default rules:

.. code-block:: shell

    pre-commit run --all-files
