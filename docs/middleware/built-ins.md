# Built-in Middleware Components

WD-DI provides a few common middleware components out of the box to handle typical cross-cutting concerns. These can be used directly in your pipeline or serve as examples for creating your own custom middleware.

You can find these middleware classes in the `wd.di.middleware` module.

---

## `LoggingMiddleware`

**Purpose:** Logs the start and completion of pipeline execution for a given context.

**How it works:**
*   Accepts a `logger` callable (e.g., `print`, or a method from Python's `logging` module) in its constructor.
*   Before calling `await next()`, it logs a message like "Executing pipeline for context: [context]".
*   After `await next()` completes, it logs a message like "Pipeline for context: [context] completed with result: [result]".

**Example Usage:**
```python
from wd.di import ServiceCollection
from wd.di.middleware import LoggingMiddleware, MiddlewarePipeline

# Define a context and a simple final handler
class MyContext:
    def __init__(self, data):
        self.data = data
    def __str__(self): # For logging
        return f"MyContext(data='{self.data}')"

class FinalHandler:
    async def invoke(self, context, next):
        return f"Processed: {context.data}"

services = ServiceCollection()
app_builder = services.create_application_builder()

# Configure logging middleware (using print as the logger)
app_builder.configure_middleware(lambda builder: (
    builder
    .use_middleware(lambda: LoggingMiddleware(logger_func=print)) # Pass the logger function
    .use_middleware(FinalHandler)
))

provider = app_builder.build()
pipeline = provider.get_service(MiddlewarePipeline)

# import asyncio
# asyncio.run(pipeline.execute(MyContext("test_data")))
# Expected Output (will vary slightly based on actual context string representation):
# Executing pipeline for context: MyContext(data='test_data')
# Pipeline for context: MyContext(data='test_data') completed with result: Processed: test_data
```
**Dependencies:**
*   Requires a `logger_func: Callable[[str], None]` to be passed to its constructor. This function will be called with log messages.

---

## `ExceptionHandlerMiddleware`

**Purpose:** Centralizes error handling within the middleware pipeline. Catches exceptions from subsequent middleware and allows for custom error processing.

**How it works:**
*   Accepts an `exception_handler` callable in its constructor. This handler function should take the `context` and the `exception` as arguments.
*   It wraps the `await next()` call in a `try...except` block.
*   If an exception occurs, it calls the provided `exception_handler(context, exception)`. The return value of this handler becomes the result of the pipeline execution.

**Example Usage:**
```python
from wd.di import ServiceCollection
from wd.di.middleware import ExceptionHandlerMiddleware, MiddlewarePipeline

class MyContext:
    def __init__(self, should_fail: bool):
        self.should_fail = should_fail

class RiskyHandler:
    async def invoke(self, context, next):
        if context.should_fail:
            raise ValueError("Something went wrong in RiskyHandler!")
        return "RiskyHandler succeeded"

def my_custom_error_handler(context, exception):
    print(f"Custom Error Handler: Caught {type(exception).__name__}: {exception} for context: {context}")
    return "Default error response"

services = ServiceCollection()
app_builder = services.create_application_builder()

app_builder.configure_middleware(lambda builder: (
    builder
    .use_middleware(lambda: ExceptionHandlerMiddleware(my_custom_error_handler))
    .use_middleware(RiskyHandler)
))

provider = app_builder.build()
pipeline = provider.get_service(MiddlewarePipeline)

# import asyncio
# async def main():
#     success_context = MyContext(should_fail=False)
#     result_success = await pipeline.execute(success_context)
#     print(f"Result (Success): {result_success}")

#     fail_context = MyContext(should_fail=True)
#     result_fail = await pipeline.execute(fail_context)
#     print(f"Result (Fail): {result_fail}")
# asyncio.run(main())

# Expected Output:
# Result (Success): RiskyHandler succeeded
# Custom Error Handler: Caught ValueError: Something went wrong in RiskyHandler! for context: <__main__.MyContext object at 0x...>
# Result (Fail): Default error response
```

**Dependencies:**
*   Requires an `exception_handler: Callable[[Any, Exception], Any]` to be passed to its constructor.

---

## `ValidationMiddleware`

**Purpose:** Validates the context object before allowing the pipeline to proceed.

**How it works:**
*   Accepts a `validator` callable in its constructor. This validator function should take the `context` as an argument and return `True` if valid, or `False` (or raise an exception) if invalid.
*   If the `validator(context)` returns `False` or raises an error (by default, it raises `ValueError` if the validator returns `False`), the pipeline is short-circuited, and an exception is raised (or propagated).

**Example Usage:**
```python
from wd.di import ServiceCollection
from wd.di.middleware import ValidationMiddleware, MiddlewarePipeline

class MyContext:
    def __init__(self, data: str):
        self.data = data

class EchoHandler:
    async def invoke(self, context, next):
        return f"Echo: {context.data}"

def my_validator(context: MyContext) -> bool:
    is_valid = context.data is not None and len(context.data) > 3
    print(f"Validating '{context.data}': {is_valid}")
    return is_valid

services = ServiceCollection()
app_builder = services.create_application_builder()

app_builder.configure_middleware(lambda builder: (
    builder
    .use_middleware(lambda: ValidationMiddleware(my_validator))
    .use_middleware(EchoHandler)
))

provider = app_builder.build()
pipeline = provider.get_service(MiddlewarePipeline)

# import asyncio
# async def main():
#     valid_context = MyContext("valid_data")
#     result_valid = await pipeline.execute(valid_context)
#     print(f"Result (Valid): {result_valid}")

#     invalid_context = MyContext("bad")
#     try:
#         await pipeline.execute(invalid_context)
#     except ValueError as e:
#         print(f"Error (Invalid): {e}")
# asyncio.run(main())

# Expected Output:
# Validating 'valid_data': True
# Result (Valid): Echo: valid_data
# Validating 'bad': False
# Error (Invalid): Context validation failed.
```

**Dependencies:**
*   Requires a `validator: Callable[[Any], bool]` to be passed to its constructor.

---

## `CachingMiddleware`

**Purpose:** Caches the result of the pipeline execution for a given context to avoid re-computation.

**How it works:**
*   Uses the `context` object itself as the cache key (so the context must be hashable).
*   On first execution for a specific context, it calls `await next()` and stores the result in an in-memory dictionary.
*   On subsequent executions with an identical (hash-equal) context, it returns the cached result directly without calling `await next()`.

**Example Usage:**
```python
from wd.di import ServiceCollection
from wd.di.middleware import CachingMiddleware, MiddlewarePipeline
import time

# Make context hashable
from dataclasses import dataclass

@dataclass(frozen=True) # frozen=True makes it hashable
class MyContext:
    key: str

call_count = 0
class SlowHandler:
    async def invoke(self, context, next):
        nonlocal call_count
        call_count += 1
        print(f"SlowHandler called (call #{call_count}) for key: {context.key}")
        await asyncio.sleep(0.1) # Simulate work
        return f"Processed: {context.key}"

services = ServiceCollection()
app_builder = services.create_application_builder()

app_builder.configure_middleware(lambda builder: (
    builder
    .use_middleware(CachingMiddleware) # CachingMiddleware should usually be early in the pipeline
    .use_middleware(SlowHandler)
))

provider = app_builder.build()
pipeline = provider.get_service(MiddlewarePipeline)

# import asyncio
# async def main():
#     context1 = MyContext("data_key_1")
#     print(await pipeline.execute(context1)) # First call, SlowHandler executes
#     print(await pipeline.execute(context1)) # Second call, result is cached

#     context2 = MyContext("data_key_2")
#     print(await pipeline.execute(context2)) # First call for this context, SlowHandler executes
# asyncio.run(main())

# Expected Output:
# SlowHandler called (call #1) for key: data_key_1
# Processed: data_key_1
# Processed: data_key_1  (from cache, SlowHandler not called again for context1)
# SlowHandler called (call #2) for key: data_key_2
# Processed: data_key_2
```

**Dependencies:**
*   None, beyond the context being hashable.

---

These built-in middleware components provide a good starting point for handling common concerns. You can easily combine them with your own custom middleware to build sophisticated processing pipelines. 