# create_service_collection()

This function is a helper to create a new `ServiceCollection` instance.

```python
from wd.di import create_service_collection

services = create_service_collection()
```

## Function Signature

`create_service_collection() -> ServiceCollection`

- **Returns:** A new, empty `ServiceCollection` instance.

## Purpose

Provides a convenient way to instantiate a `ServiceCollection` without directly calling its constructor. This can be useful for brevity or if future versions of `ServiceCollection` might require different initialization parameters. 