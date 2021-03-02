.. include:: targets.rst

.. _troubleshooting:

Troubleshooting
===============

Crash on multi-threading
------------------------

On macOS, flake8_ might raise this error when calling ``requests.get(url)``:

.. code-block:: shell

    objc[93329]: +[__NSPlaceholderDate initialize] may have been in progress in another thread when fork() was called.
    objc[93329]: +[__NSPlaceholderDate initialize] may have been in progress in another thread when fork() was called. We cannot safely call it or ignore it in the fork() child process. Crashing instead. Set a breakpoint on objc_initializeAfterForkError to debug.

To solve this issue, add this environment variable to ``.bashrc`` (or the initialization file for your favorite shell):

.. code-block:: shell

    export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES

Thanks to `this StackOverflow answer <https://stackoverflow.com/questions/50168647/multiprocessing-causes-python-to-crash-and-gives-an-error-may-have-been-in-progr/52230415#52230415>`_.

ModuleNotFoundError: No module named 'nitpick.plugins.XXX'
----------------------------------------------------------

When upgrading to new versions, old plugins might be renamed in `setuptools entry points <https://setuptools.readthedocs.io/en/latest/userguide/entry_point.html>`_.

But they might still be present in the `entry_points.txt plugin metadata <https://setuptools.readthedocs.io/en/latest/deprecated/python_eggs.html#entry-points-txt-entry-point-plugin-metadata>`_ in your virtualenv.

.. code-block::

    $ rg nitpick.plugins.setup ~/Library/Caches/pypoetry/
    /Users/john.doe/Library/Caches/pypoetry/virtualenvs/nitpick-UU_pZ5zs-py3.6/lib/python3.6/site-packages/nitpick-0.24.1.dist-info/entry_points.txt
    11:setup_cfg=nitpick.plugins.setup_cfg

Remove and recreate the virtualenv; this should fix it.

During development, you can run ``invoke clean --venv install --dry``.
It will display the commands that would be executed; remove ``--dry`` to actually run them.

:ref:`Read this page on how to install Invoke <development>`.
