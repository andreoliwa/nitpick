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
