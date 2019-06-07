============
Contributing
============

Contributions are welcome, and they are greatly appreciated!
Every little bit helps, and credit will always be given.

Check the `projects on GitHub <https://github.com/andreoliwa/nitpick/projects>`_, you might help coding a planned feature.

Bug reports or feature requests
===============================

* First, search the `GitHub issue tracker <https://github.com/andreoliwa/nitpick/issues>`_ to see if your bug/feature is already there.
* If nothing is found, just `add a new issue and follow the instructions there <https://github.com/andreoliwa/nitpick/issues/new/choose>`_.

Documentation improvements
==========================

nitpick could always use more documentation, whether as part of the
official docs, in docstrings, or even on the web in blog posts,
articles, and such.

Development
===========

To set up ``nitpick`` for local development:

1. Fork `nitpick <https://github.com/andreoliwa/nitpick>`_
   (look for the "Fork" button).

2. Clone your fork locally::

    cd ~/Code
    git clone git@github.com:your_name_here/nitpick.git
    cd nitpick

3. `Install Poetry globally using the recommended way <https://github.com/sdispater/poetry#installation>`_.

4. Create your virtualenv with pyenv (or some other tool you prefer)::

    pyenv virtualenv 3.6.8 nitpick
    pyenv activate nitpick

5. Install packages::

    poetry install

    # Output:
    # Installing dependencies from lock file
    # ...

6. Install the pre-commit hooks::

    pre-commit install

    # Output:
    # pre-commit installed at .git/hooks/pre-commit

7. Create a branch for local development::

    git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

7. When you're done making changes, run those linting/testing commands::

    black . && isort -y && pre-commit run --all-files && pytest

8. Commit your changes and push your branch to GitHub::

    git add .
    git commit -m "Your detailed description of your changes."
    git push origin name-of-your-bugfix-or-feature

9. Submit a pull request through the GitHub website.

10. If your pull request is accepted, all your commits will be squashed into one,
    and the `Angular Convention will be used on the commit message <https://github.com/conventional-changelog/conventional-changelog/tree/0e05028f70bbd3109e1a4b16262a9450153060de/packages/conventional-changelog-angular#angular-convention>`_.

Pull Request Guidelines
-----------------------

If you need some code review or feedback while you're developing the code just make the pull request.

For merging, you should:

1. Include passing tests (run ``pytest``) [1]_.
2. Update documentation when there's new API, functionality etc.
3. Add yourself to ``AUTHORS.rst``.

.. [1] If you don't have all the necessary python versions available locally you can rely on Travis - it will
       `run the tests <https://travis-ci.com/andreoliwa/nitpick/pull_requests>`_ for each change you add in the pull request.

       It will be slower though ...
