.. include:: targets.rst

Quickstart
==========

Install
-------

Install in an isolated environment with pipx_::

    # Latest PyPI release
    pipx install nitpick

    # Development branch from GitHub
    pipx install git+https://github.com/andreoliwa/nitpick

On macOS/Linux, install the latest release with Homebrew_::

    brew install andreoliwa/formulae/nitpick

    # Development branch from GitHub
    brew install andreoliwa/formulae/nitpick --HEAD

On Arch Linux, install with yay::

    yay -Syu nitpick

Add to your project with Poetry_::

    poetry add --dev nitpick

Or install it with pip::

    pip install -U nitpick

Run
---

To fix and modify your files directly::

    nitpick fix

To check for errors only::

    nitpick check

Nitpick is also a flake8_ plugin, so you can run this on a project with at least one Python (``.py``) file::

    flake8 .

Nitpick_ will download and use the opinionated `default style file`_.

You can use it as a template to :ref:`configure-your-own-style`.

Run as a pre-commit hook
------------------------

If you use pre-commit_ on your project, add this to the ``.pre-commit-config.yaml`` in your repository:

.. code-block:: yaml

    repos:
      - repo: https://github.com/andreoliwa/nitpick
        rev: v0.27.0
        hooks:
          - id: nitpick

To install the ``pre-commit`` and ``commit-msg`` Git hooks:

.. code-block:: shell

    pre-commit install --install-hooks
    pre-commit install -t commit-msg

To start checking all your code against the default rules:

.. code-block:: shell

    pre-commit run --all-files

Modify files directly
---------------------

Nitpick_ includes a CLI to apply your style and modify the configuration files directly:

.. code-block:: shell

    nitpick fix

Read more details here: :ref:`cli`.
