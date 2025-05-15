# ServiceCollection API

The `ServiceCollection` class is the primary entry point for registering services in the WD-DI framework. It provides methods to define how services are created and their lifetimes.

```python
from wd.di import ServiceCollection
```

## Initialization

```python
services = ServiceCollection()
```
Creates a new, empty service collection.

## Methods

### `add_transient_factory(service_type: Type, factory: Callable[["ServiceProvider"], Any])`
Registers a service with a transient lifetime using a factory function.
- `service_type`: The type of the service to register.
- `factory`: A callable that accepts a `ServiceProvider` instance and returns an instance of the service. A new instance is created each time the service is requested.

### `add_singleton_factory(service_type: Type, factory: Callable[["ServiceProvider"], Any])`
Registers a service with a singleton lifetime using a factory function.
- `service_type`: The type of the service to register.
- `factory`: A callable that accepts a `ServiceProvider` instance and returns an instance of the service. The factory is called only once; subsequent requests return the same instance.

### `add_transient(service_type: Type, implementation_type: Optional[Type] = None)`
Registers a service with a transient lifetime.
- `service_type`: The type of the service to register.
- `implementation_type` (optional): The concrete type that implements the service. If `None`, `service_type` is used as the implementation. A new instance of `implementation_type` is created each time the service is requested.

### `add_singleton(service_type: Type, implementation_type: Optional[Type] = None)`
Registers a service with a singleton lifetime.
- `service_type`: The type of the service to register.
- `implementation_type` (optional): The concrete type that implements the service. If `None`, `service_type` is used as the implementation. A single instance of `implementation_type` is created and reused for all subsequent requests.

### `add_scoped(service_type: Type, implementation_type: Optional[Type] = None)`
Registers a service with a scoped lifetime.
- `service_type`: The type of the service to register.
- `implementation_type` (optional): The concrete type that implements the service. If `None`, `service_type` is used as the implementation. A new instance is created once per scope. (Note: Scope management is typically handled by `ServiceProvider.create_scope()`).

### `add_instance(service_type: Type, instance: Any)`
Registers an already-constructed object as a singleton.
- `service_type`: The type to register the instance against.
- `instance`: The pre-existing object to be used as the singleton instance.
The method internally uses `add_singleton_factory` by wrapping the instance in a trivial factory (`lambda _: instance`).

### `build_service_provider() -> ServiceProvider`
Creates a `ServiceProvider` from the registered services. The `ServiceProvider` is used to resolve service instances.
- Returns: A new `ServiceProvider` instance.

### `configure(options_type: Type[T], *, section: Optional[str] = None) -> None`
Configures options binding from an `IConfiguration` provider.
- `options_type`: The type of the options class to bind.
- `section` (optional): The configuration section name to bind from. If `None`, the root of the configuration is used.
This method registers an `Options[options_type]` as a singleton, which, when resolved, will provide a populated instance of `options_type`. Requires `IConfiguration` to be registered.

### `create_application_builder()`
This method is attached dynamically from `wd.di.middleware_di`.
Creates and returns a `MiddlewareBuilder` instance, associating it with this service collection. This is used to construct middleware pipelines.
- Returns: A `MiddlewareBuilder` instance.

## Decorator Registration Methods

These methods provide a decorator-based syntax for registering services.

### `@singleton(service_type: Optional[Type] = None)`
Decorator to register a class as a singleton.
- `service_type` (optional): The interface or base type to register the decorated class against. If `None`, the class is registered against its own type.
Example:
```python
@services.singleton()
class MyService: ...

@services.singleton(IMyService)
class MyServiceImpl(IMyService): ...
```

### `@transient(service_type: Optional[Type] = None)`
Decorator to register a class as transient.
- `service_type` (optional): The interface or base type to register the decorated class against. If `None`, the class is registered against its own type.
Example:
```python
@services.transient()
class MyService: ...

@services.transient(IMyService)
class MyServiceImpl(IMyService): ...
```

### `@scoped(service_type: Optional[Type] = None)`
Decorator to register a class as scoped.
- `service_type` (optional): The interface or base type to register the decorated class against. If `None`, the class is registered against its own type.
Example:
```python
@services.scoped()
class MyService: ...

@services.scoped(IMyService)
class MyServiceImpl(IMyService): ...
``` 