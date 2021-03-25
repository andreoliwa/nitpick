.. include:: targets.rst

Quickstart
==========

Install / Basic usage
---------------------

To try the package, simply install it (in a virtualenv or globally) and run flake8_ on a project with at least one Python (``.py``) file:

.. code-block:: shell

    # Install with pip:
    pip install -U nitpick

    # Add to your project with Poetry:
    poetry add --dev nitpick

    # On macOS, install with Homebrew:
    brew install andreoliwa/formulae/nitpick

    # Run nitpick directly to modify your files
    nitpick run

    # Or run with flake8 to only check for errors
    flake8 .

Nitpick_ will download and use the opinionated `default style file`_.

You can use it as a template to :ref:`configure-your-own-style`.

Run as a pre-commit hook (recommended)
--------------------------------------

If you use pre-commit_ on your project (you should), add this to the ``.pre-commit-config.yaml`` in your repository:

.. code-block:: yaml

    repos:
      - repo: https://github.com/andreoliwa/nitpick
        rev: v0.26.0
        hooks:
          - id: nitpick

To install the ``pre-commit`` and ``commit-msg`` Git hooks:

.. code-block:: shell

    pre-commit install --install-hooks
    pre-commit install -t commit-msg

To start checking all your code against the default rules:

.. code-block:: shell

    pre-commit run --all-files

Apply changes to files
----------------------

Nitpick_ includes a CLI to apply your style on the configuration files:

.. code-block:: shell

    nitpick run

Read more details here: :ref:`cli`.
