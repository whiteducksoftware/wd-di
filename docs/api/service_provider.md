# ServiceProvider & Scope API

This document describes the `ServiceProvider` and `Scope` classes from `wd.di.container`, which are responsible for resolving registered services.

## `ServiceProvider`

The `ServiceProvider` is created from a `ServiceCollection` and is used to retrieve instances of registered services.

### Initialization

Typically obtained by calling `build_service_provider()` on a `ServiceCollection` instance.

```python
# services is an instance of ServiceCollection
provider = services.build_service_provider()
```

It is initialized with a dictionary of `ServiceDescriptor` objects.

### Methods

- **`get_service(service_type: Type[T]) -> T`**
  Retrieves an instance of the specified `service_type`.
  - `service_type`: The type of the service to resolve.
  - **Returns:** An instance of the requested service.
  - **Raises:**
    - `Exception`: If the service is not registered.
    - `Exception`: If a circular dependency is detected during resolution.
    - `Exception`: If a scoped service is requested from the root provider (use `create_scope()` first).
    - `Exception`: If an unknown service lifetime is encountered.
    - `Exception`: If a service descriptor has no implementation type or factory.
    - `Exception`: If a `NameError` occurs during dependency resolution (often due to forward references in circular dependencies).

  The behavior depends on the service's registered lifetime:
    - **Singleton:** Returns the same instance for all requests. The instance is created on the first request.
    - **Transient:** Returns a new instance for every request.
    - **Scoped:** Cannot be resolved directly from the root `ServiceProvider`. A `Scope` must be created first.

- **`create_scope() -> "Scope"`**
  Creates a new `Scope` object.
A scope is a way to manage services with a scoped lifetime. Scoped services resolved within the same scope will be the same instance, while different scopes will have different instances.
  - **Returns:** A new `Scope` instance.

## `Scope`

A `Scope` is a specialized `ServiceProvider` that manages scoped service instances and their disposal.

### Initialization

Typically obtained by calling `create_scope()` on a `ServiceProvider` instance.

```python
with provider.create_scope() as scope:
    my_scoped_service = scope.get_service(MyScopedService)
    # ... use my_scoped_service ...
# my_scoped_service (if disposable) is disposed here
```

### Methods

Inherits `get_service(service_type: Type[T]) -> T` from `ServiceProvider` with modified behavior for scoped services:
  - **Scoped:** Returns an instance that is unique to this scope. The instance is created on the first request within this scope and reused for subsequent requests within the same scope.
  - **Singleton:** Returns the same instance as the root provider.
  - **Transient:** Returns a new instance for every request (same as root provider).

- **`dispose()`**
  Disposes of all scoped instances created by this scope that have a `dispose()` or `close()` method.
  This method is automatically called when the scope is exited if used as a context manager.

### Context Manager Protocol

`Scope` objects can be used as context managers (`with` statement). The `dispose()` method is automatically called upon exiting the context.

```python
# provider is an instance of ServiceProvider
with provider.create_scope() as scope:
    service = scope.get_service(MyScopedService)
    # ...
# scope.dispose() is called automatically here
```

## Circular Dependency Detection

Both `ServiceProvider` and `Scope` implement circular dependency detection using `contextvars.ContextVar`. If a service directly or indirectly depends on itself during resolution, an `Exception` is raised detailing the resolution stack. 