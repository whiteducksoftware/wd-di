from abc import ABC, abstractmethod
from typing import Any, Callable, List, Optional, TypeVar

T = TypeVar("T")
TNext = Callable[[], Any]
TMiddleware = Callable[[T, TNext], Any]


class IMiddleware(ABC):
    """Base interface for middleware components."""

    @abstractmethod
    async def invoke(self, context: T, next: TNext) -> Any:
        """Process the context and call the next middleware in the pipeline."""
        pass


class MiddlewarePipeline:
    """Manages the middleware pipeline execution."""

    def __init__(self):
        self._middleware: List[TMiddleware[T]] = []

    def use(self, middleware: TMiddleware[T]) -> "MiddlewarePipeline":
        """Add a middleware to the pipeline."""
        self._middleware.append(middleware)
        return self

    def use_middleware(
        self, middleware_class: type, instance: Optional[Any] = None
    ) -> "MiddlewarePipeline":
        """Add a middleware class to the pipeline."""

        def adapter(context: T, next: TNext) -> Any:
            nonlocal instance
            if instance is None:
                instance = middleware_class()
            return instance.invoke(context, next)

        self._middleware.append(adapter)
        return self

    async def execute(self, context: T) -> Any:
        """Execute the middleware pipeline."""
        if not self._middleware:
            return None

        index = 0

        async def invoke_next() -> Any:
            nonlocal index
            if index < len(self._middleware):
                middleware = self._middleware[index]
                index += 1
                return await middleware(context, invoke_next)
            return None

        return await invoke_next()


class ExceptionHandlerMiddleware(IMiddleware):
    """Built-in middleware for handling exceptions in the pipeline."""

    async def invoke(self, context: T, next: TNext) -> Any:
        try:
            return await next()
        except Exception as e:
            # Log the exception or handle it as needed
            raise


class LoggingMiddleware(IMiddleware):
    """Built-in middleware for logging pipeline execution."""

    def __init__(self, logger: Optional[Callable[[str], None]] = None):
        self._logger = logger or print

    async def invoke(self, context: T, next: TNext) -> Any:
        self._logger(f"Executing pipeline with context: {context}")
        try:
            result = await next()
            self._logger(f"Pipeline execution completed with result: {result}")
            return result
        except Exception as e:
            self._logger(f"Pipeline execution failed: {str(e)}")
            raise


class ValidationMiddleware(IMiddleware):
    """Built-in middleware for context validation."""

    def __init__(self, validator: Callable[[T], bool]):
        self._validator = validator

    async def invoke(self, context: T, next: TNext) -> Any:
        if not self._validator(context):
            raise ValueError(f"Invalid context: {context}")
        return await next()


class CachingMiddleware(IMiddleware):
    """Built-in middleware for caching pipeline results."""

    def __init__(self):
        self._cache = {}

    async def invoke(self, context: T, next: TNext) -> Any:
        # Use context as cache key if it's hashable
        try:
            cache_key = hash(str(context.__dict__))
            if cache_key in self._cache:
                return self._cache[cache_key]

            result = await next()
            self._cache[cache_key] = result
            return result
        except (TypeError, AttributeError):
            # If context is not hashable or has no __dict__, skip caching
            return await next()
