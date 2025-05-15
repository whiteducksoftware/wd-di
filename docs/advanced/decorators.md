# Service Decorators

The dependency injection container supports a powerful decorator pattern that allows you to wrap, intercept, or modify service instances *after* they are created but *before* they are returned to the caller or cached by their lifetime manager. This is an implementation of the [Decorator design pattern](https://en.wikipedia.org/wiki/Decorator_pattern) applied to services managed by the DI container.

Decorators are registered against a specific service type and are applied in the reverse order of their registration (the last decorator registered is the outermost).

## Use Cases

Service decorators are useful for a variety of cross-cutting concerns, such as:

*   **Caching:** Wrap a service with a caching layer.
*   **Logging/Auditing:** Log method calls to a service or audit actions.
*   **Transaction Management:** Start and commit/rollback transactions around service method calls.
*   **Retries/Circuit Breakers:** Add resilience to service operations.
*   **Data Validation/Transformation:** Validate input or transform output of service methods.
*   **Feature Toggling:** Conditionally alter behavior by applying different decorators.

## Registering Decorators

You register decorators using the `decorate` method on the `ServiceCollection`:

```python
from wd.di import ServiceCollection, ServiceProvider

# 1. Define your service interface and implementation
class IDataService:
    def get_data(self, item_id: str) -> str:
        raise NotImplementedError

class RealDataService(IDataService):
    def get_data(self, item_id: str) -> str:
        print(f"RealDataService: Fetching data for {item_id}")
        return f"Data for {item_id}"

# 2. Define your decorator(s)
class LoggingDecorator(IDataService):
    def __init__(self, inner: IDataService, provider: ServiceProvider):
        self._inner = inner
        self._provider = provider # Example: if decorator needs other services
        print("LoggingDecorator: Initialized")

    def get_data(self, item_id: str) -> str:
        print(f"LoggingDecorator: Before calling get_data for {item_id}")
        result = self._inner.get_data(item_id)
        print(f"LoggingDecorator: After calling get_data for {item_id}, result: {result}")
        return result

# 3. Define a decorator factory
# A decorator factory is a callable that takes two arguments:
# - The current ServiceProvider instance.
# - The "inner" service instance that is being decorated.
# It must return the decorated instance.
def logging_decorator_factory(provider: ServiceProvider, inner_service: IDataService) -> IDataService:
    return LoggingDecorator(inner_service, provider)

# 4. Configure services
services = ServiceCollection()
services.add_transient(IDataService, RealDataService)

# 5. Apply the decorator
services.decorate(IDataService, logging_decorator_factory)

# 6. Build and use
provider = services.build_service_provider()
data_service = provider.get_service(IDataService)
data_service.get_data("item123")

# Output would be:
# LoggingDecorator: Initialized
# LoggingDecorator: Before calling get_data for item123
# RealDataService: Fetching data for item123
# LoggingDecorator: After calling get_data for item123, result: Data for item123
```

### Decorator Factories

A **decorator factory** is a callable with the signature:

```python
Callable[[ServiceProvider, InnerServiceType], OuterServiceType]
```

*   `ServiceProvider`: The current service provider, which can be used by the decorator to resolve other dependencies if needed.
*   `InnerServiceType`: The instance of the service being wrapped.
*   `OuterServiceType`: The (potentially) wrapped instance that will be returned. Often, this is the same type as `InnerServiceType`, but it can be different if the decorator changes the interface (though this should be done with care).

### Order of Application

If multiple decorators are registered for the same service type, they are applied sequentially. The `ServiceDescriptor` stores them in a list. When an instance is created:
1.  The base instance (from `implementation_type` or `factory`) is created.
2.  The decorators are applied in **reverse order of registration**. This means the decorator registered *last* becomes the *outermost* wrapper, and the decorator registered *first* becomes the *innermost* wrapper (closest to the original service instance).

```python
services.decorate(IMyService, inner_decorator_factory) # Applied first (becomes inner)
services.decorate(IMyService, outer_decorator_factory) # Applied second (becomes outer)

# Execution flow: outer_decorator -> inner_decorator -> actual_service
```

## Advanced: Decorators with Parameters

Sometimes, your decorator itself might need configuration. You can achieve this by creating a decorator factory *function* that takes parameters and *returns* the actual decorator factory callable:

```python
class RetryingDataServiceDecorator(IDataService):
    def __init__(self, inner: IDataService, max_retries: int):
        self._inner = inner
        self._max_retries = max_retries

    def get_data(self, item_id: str) -> str:
        attempts = 0
        while True:
            try:
                return self._inner.get_data(item_id)
            except Exception as e:
                attempts += 1
                if attempts >= self._max_retries:
                    print(f"RetryingDecorator: Max retries ({self._max_retries}) reached. Failing.")
                    raise
                print(f"RetryingDecorator: Attempt {attempts} failed. Retrying...")
                # In a real scenario, you might add a delay here

# Factory that creates the decorator factory
def create_retrying_decorator_factory(max_retries: int):
    def actual_decorator_factory(provider: ServiceProvider, inner: IDataService) -> IDataService:
        return RetryingDataServiceDecorator(inner, max_retries)
    return actual_decorator_factory

# Usage:
services.add_transient(IDataService, RealDataService)
retry_factory_with_config = create_retrying_decorator_factory(max_retries=3)
services.decorate(IDataService, retry_factory_with_config)

provider = services.build_service_provider()
service = provider.get_service(IDataService)
# service.get_data("test") will now have retry logic
```

## Circular Decorator Detection

The container includes a mechanism to detect circular decorator applications at runtime. If a decorator, during its application to a service, causes itself to be re-applied to the *same service instance resolution*, a `CircularDecoratorError` will be raised. This helps prevent infinite loops during service construction.

For example, if `DecoratorA` for `IServiceX` internally tries to resolve `IServiceX` again in a way that re-triggers the application of `DecoratorA` to the same `IServiceX` instance being formed, a cycle is detected. 