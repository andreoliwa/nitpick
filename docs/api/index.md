# API Reference

This section contains the API documentation for Nitpick's Python modules.

## Main Modules

- [CLI](cli.md) - Command-line interface
- [Plugins](plugins.md) - Plugin system and built-in plugins

## Using the API

Nitpick can be used as a library in your Python code. The main entry point is the `Nitpick` class.

```python
from nitpick.core import Nitpick

# Initialize Nitpick
nit = Nitpick.singleton().init()

# Run checks
violations = nit.run()
```

For more details, see the module documentation below.
