============
Contributing
============

.. todo::

    Improve the contributing guidelines.

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given.

Bug reports
===========

When `reporting a bug <https://github.com/andreoliwa/flake8-nitpick/issues>`_ please include:

    * Your operating system name and version.
    * Any details about your local setup that might be helpful in troubleshooting.
    * Detailed steps to reproduce the bug.

Documentation improvements
==========================

flake8-nitpick could always use more documentation, whether as part of the
official docs, in docstrings, or even on the web in blog posts,
articles, and such.

Feature requests and feedback
=============================

The best way to send feedback is to file an issue at https://github.com/andreoliwa/flake8-nitpick/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that code contributions are welcome :)

Development
===========

To set up `flake8-nitpick` for local development:

1. Fork `flake8-nitpick <https://github.com/andreoliwa/flake8-nitpick>`_
   (look for the "Fork" button).
2. Clone your fork locally::

    git clone git@github.com:your_name_here/flake8-nitpick.git

3. Create a branch for local development::

    git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

4. Install the pre-commit hooks:

    pre-commit install

5. When you're done making changes, run those commands::

    black . && isort -y
    pre-commit run --all-files
    pytest
    make html

5. Commit your changes and push your branch to GitHub::

    git add .
    git commit -m "Your detailed description of your changes."
    git push origin name-of-your-bugfix-or-feature

6. Submit a pull request through the GitHub website.

7. If your pull request is accepted, all your commits will be squashed into one.

Pull Request Guidelines
-----------------------

If you need some code review or feedback while you're developing the code just make the pull request.

For merging, you should:

1. Include passing tests (run ``pytest``) [1]_.
2. Update documentation when there's new API, functionality etc.
3. Add yourself to ``AUTHORS.rst``.

.. [1] If you don't have all the necessary python versions available locally you can rely on Travis - it will
       `run the tests <https://travis-ci.com/andreoliwa/flake8-nitpick/pull_requests>`_ for each change you add in the pull request.

       It will be slower though ...

Tips
----

To run tests::

    pytest
