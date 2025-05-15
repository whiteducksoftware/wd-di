# ServiceLifetime API

This enumeration defines the possible lifetimes for services registered with the DI container.

```python
from wd.di.lifetimes import ServiceLifetime
```

## Enum Members

- **`ServiceLifetime.TRANSIENT`**
  - Value: `1`
  - Services registered with this lifetime are created each time they are requested from the `ServiceProvider` or `Scope`.

- **`ServiceLifetime.SINGLETON`**
  - Value: `2`
  - Services registered with this lifetime are created only once. The same instance is returned for all subsequent requests from any `ServiceProvider` or `Scope` within the same root container.

- **`ServiceLifetime.SCOPED`**
  - Value: `3`
  - Services registered with this lifetime are created once per `Scope`. Within the same scope, the same instance is returned. Different scopes will have different instances.
  Scoped services cannot be resolved from the root `ServiceProvider` and must be resolved from a `Scope` created via `ServiceProvider.create_scope()`. 