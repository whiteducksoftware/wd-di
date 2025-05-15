# Middleware DI API

This section describes components related to integrating middleware with the Dependency Injection system, primarily from `wd.di.middleware_di`.

## `create_application_builder(services: ServiceCollection) -> ApplicationBuilder`

Creates an `ApplicationBuilder` instance, associating it with a `ServiceCollection`.
This function is also available as a method on `ServiceCollection` instances: `services.create_application_builder()`.

```python
from wd.di import create_service_collection

services = create_service_collection()
app_builder = services.create_application_builder()
# or
# from wd.di.middleware_di import create_application_builder
# app_builder = create_application_builder(services)
```

- `services: ServiceCollection`: The service collection to associate with the application builder.
- **Returns:** An `ApplicationBuilder` instance.

## `ApplicationBuilder`

Provides a way to configure and build an application, including its middleware pipeline, using a `ServiceCollection`.

### Initialization

Typically obtained via `create_application_builder(services)` or `services.create_application_builder()`.

```python
class ApplicationBuilder:
    def __init__(self, services: ServiceCollection):
        self._services = services
```

### Methods

- **`configure_middleware(configure: Callable[["MiddlewareBuilder"], None]) -> "ApplicationBuilder"`**
  Configures the middleware pipeline for the application.
  - `configure`: A callable that receives a `MiddlewareBuilder` instance and should use it to register middleware.
  - Returns the `ApplicationBuilder` instance for chaining.
  Inside this method, a `MiddlewareBuilder` is created, passed to the `configure` callable, and then the resulting `MiddlewarePipeline` is registered as a singleton service.

- **`build() -> ServiceProvider`**
  Builds the final `ServiceProvider` for the application from the associated `ServiceCollection`.
  - Returns: A `ServiceProvider` instance that can be used to resolve services, including the configured `MiddlewarePipeline`.

## `MiddlewareBuilder`

Used by `ApplicationBuilder` to configure and build a `MiddlewarePipeline`. Users typically interact with this via the `configure` callable passed to `ApplicationBuilder.configure_middleware`.

### Initialization

Instantiated by `ApplicationBuilder`.

```python
class MiddlewareBuilder:
    def __init__(self, services: ServiceCollection):
        self._services = services
        self._pipeline = MiddlewarePipeline()
```

### Methods

- **`use(middleware: Callable[[T, TNext], Any]) -> "MiddlewareBuilder"`**
  Adds a middleware function to the pipeline.
  - `middleware`: A callable `(context, next_func) -> Any`.
  - Returns the `MiddlewareBuilder` instance for chaining.

- **`use_middleware(middleware_type: type) -> "MiddlewareBuilder"`**
  Adds a middleware class (that implements `IMiddleware`) to the pipeline. The middleware type will be registered as a transient service in the `ServiceCollection` if not already registered (with special handling for `LoggingMiddleware` to ensure it can be default constructed or receive dependencies).
  The middleware instance is resolved from the service provider *per execution* of this middleware in the pipeline.
  - `middleware_type`: The class of the middleware to add.
  - Returns the `MiddlewareBuilder` instance for chaining.

- **`build() -> MiddlewarePipeline`**
  Builds and returns the configured `MiddlewarePipeline`.
  - Returns: The `MiddlewarePipeline` instance. 