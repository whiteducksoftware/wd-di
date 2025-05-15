# Middleware API

This section describes the middleware components available in `wd.di.middleware`.

```python
from wd.di.middleware import (
    IMiddleware,
    MiddlewarePipeline,
    LoggingMiddleware,
    ValidationMiddleware,
    CachingMiddleware,
    ExceptionHandlerMiddleware,
)
```

## `IMiddleware`

An abstract base class defining the interface for middleware components.

```python
class IMiddleware(ABC):
    @abstractmethod
    async def invoke(self, context: T, next: TNext) -> Any:
        """Process the context and call the next middleware in the pipeline."""
        pass
```

- `context: T`: The context object being processed by the pipeline.
- `next: TNext`: A callable that invokes the next middleware in the pipeline.

## `MiddlewarePipeline`

Manages the registration and execution of a sequence of middleware components.

### Initialization
```python
pipeline = MiddlewarePipeline()
```

### Methods

- **`use(middleware: TMiddleware[T]) -> "MiddlewarePipeline"`**
  Adds a middleware function to the pipeline.
  - `middleware`: A callable matching `TMiddleware[T]` (i.e., `Callable[[T, TNext], Any]`).
  - Returns the `MiddlewarePipeline` instance for chaining.

- **`use_middleware(middleware_class: type, instance: Optional[Any] = None) -> "MiddlewarePipeline"`**
  Adds a middleware class (that implements `IMiddleware`) to the pipeline.
  - `middleware_class`: The class of the middleware to add.
  - `instance` (optional): A pre-existing instance of the middleware class. If not provided, a new instance will be created.
  - Returns the `MiddlewarePipeline` instance for chaining.

- **`async execute(context: T) -> Any`**
  Executes the configured middleware pipeline with the given context.
  - `context: T`: The initial context to pass through the pipeline.
  - Returns the result of the pipeline execution.

## Built-in Middleware Classes

These classes implement `IMiddleware` and can be used with `MiddlewarePipeline.use_middleware()`.

### `ExceptionHandlerMiddleware`
Handles exceptions that occur during pipeline execution.

```python
class ExceptionHandlerMiddleware(IMiddleware):
    async def invoke(self, context: T, next: TNext) -> Any:
        try:
            return await next()
        except Exception as e:
            # Log the exception or handle it as needed
            raise
```
It catches exceptions from subsequent middleware, re-raising them by default. This can be subclassed to add custom exception logging or handling.

### `LoggingMiddleware`
Logs information before and after pipeline execution, and if exceptions occur.

```python
class LoggingMiddleware(IMiddleware):
    def __init__(self, logger: Optional[Callable[[str], None]] = None):
        self._logger = logger or print

    async def invoke(self, context: T, next: TNext) -> Any: ...
```
- `__init__(self, logger: Optional[Callable[[str], None]] = None)`: Initializes with an optional logger function (defaults to `print`).
Logs context, results, and errors.

### `ValidationMiddleware`
Validates the context object using a provided validator function.

```python
class ValidationMiddleware(IMiddleware):
    def __init__(self, validator: Callable[[T], bool]):
        self._validator = validator

    async def invoke(self, context: T, next: TNext) -> Any: ...
```
- `__init__(self, validator: Callable[[T], bool])`: Initializes with a validator function that takes the context and returns `True` if valid, `False` otherwise.
Raises a `ValueError` if validation fails.

### `CachingMiddleware`
Caches the result of the pipeline execution based on the context.

```python
class CachingMiddleware(IMiddleware):
    def __init__(self):
        self._cache = {}

    async def invoke(self, context: T, next: TNext) -> Any: ...
```
Attempts to use `hash(str(context.__dict__))` as a cache key. If the context is not hashable or doesn't have `__dict__`, caching is skipped. 