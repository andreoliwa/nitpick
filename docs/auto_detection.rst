.. include:: targets.rst

.. _auto_detection:

Auto-detection
==============

Root dir of the project
-----------------------

Nitpick_ tries to find the root dir of the project using some hardcoded assumptions.

#. Starting from the current working directory, it will search for files that are usually in the root of a Python project:

    - ``pyproject.toml``
    - ``setup.py``
    - ``setup.cfg``
    - ``requirements*.txt``
    - ``Pipfile`` (Pipenv_)
    - ``app.py`` and ``wsgi.py`` (`Flask CLI`_)
    - ``autoapp.py``

#. If none of these root files were found, search for ``manage.py``.
   On Django_ projects, it can be in another dir inside the root dir (:issue:`21`).
#. If multiple roots are found, get the top one in the dir tree.

Main Python file
----------------

After finding the `root dir of the project`_, Nitpick searches for a
main Python file.
Every project must have at least one ``*.py`` file, otherwise flake8_ won't even work.

Those are the Python files that are considered:

- ``setup.py``
- ``app.py`` and ``wsgi.py`` (`Flask CLI`_)
- ``autoapp.py``
- ``manage.py``
- any ``*.py`` file
