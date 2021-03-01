.. include:: targets.rst

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

Nitpick_ could always use more documentation, whether as part of the
official docs, in docstrings, or even on the web in blog posts,
articles, and such.

Development
===========

To set up Nitpick_ for local development:

1. Fork Nitpick_ (look for the "Fork" button).

2. Clone your fork locally::

    cd ~/Code
    git clone git@github.com:your_name_here/nitpick.git
    cd nitpick

3. Install Poetry_ globally using `the recommended way <https://github.com/python-poetry/poetry/#installation>`_.

4. Install Invoke_. You can use pipx_ to install it globally: ``pipx install invoke``.

5. Install packages::

    invoke install

6. Create a branch for local development::

    git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

7. When you're done making changes, run tests and checks locally with::

    # Quick tests and checks
    make
    # Or use this to simulate a full CI build with tox
    invoke ci-build

8. Commit your changes and push your branch to GitHub::

    git add .

    # For a feature:
    git commit -m "feat: short description of your feature"
    # For a bug fix:
    git commit -m "fix: short description of what you fixed"

    git push origin name-of-your-bugfix-or-feature

9. Submit a pull request through the GitHub website.

10. If your pull request is accepted, all your commits will be squashed into one, and the `Conventional Commits Format <https://www.conventionalcommits.org/>`_ will be used on the commit message.

Pull Request Guidelines
-----------------------

If you need some code review or feedback while you're developing the code just make the pull request.

For merging, you should:

1. Include passing tests (run ``invoke test``) [1]_.
2. Update documentation when there's new API, functionality etc.
3. Add yourself to ``AUTHORS.rst``.

.. [1] If you don't have all the necessary python versions available locally you can rely on GitHub Workflows: `tests will run <https://github.com/andreoliwa/nitpick/actions/workflows/python.yaml>`_ for each change you add in the pull request.

       It will be slower though ...
