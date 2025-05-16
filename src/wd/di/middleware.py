from abc import ABC, abstractmethod
from typing import Callable, Dict, List, Optional, TypeVar

T = TypeVar("T")
TNext = Callable[[], any]
"""Type alias for the 'next' function in a middleware pipeline.

This callable represents the next step in the pipeline. Invoking it will pass
control to the subsequent middleware or the target handler if it's the last one.

Returns:
    any: The result of the next middleware or handler in the pipeline.
"""
TMiddleware = Callable[[T, TNext], any]
"""Type alias for a middleware function.

A middleware function takes a context object and the 'next' function in the
pipeline as arguments. It can perform actions before or after calling `call_next`,
or decide not to call `call_next` at all to short-circuit the pipeline.

Args:
    T: The type of the context object being passed through the pipeline.
    TNext: The function to call to pass control to the next middleware.

Returns:
    any: The result of the middleware processing, often the result from `call_next()`.
"""


class IMiddleware(ABC):
    """Defines the interface for a class-based middleware component.

    Middleware classes implementing this interface can be added to a
    [MiddlewarePipeline][wd.di.middleware.MiddlewarePipeline].
    """

    @abstractmethod
    async def invoke(self, context: T, call_next: TNext) -> any:
        """Processes a context and calls the next middleware in the pipeline.

        This method contains the core logic of the middleware.

        Args:
            context: The context object (of generic type T) being passed through
                the pipeline. This object typically carries data relevant to the
                operation being performed.
            call_next: A callable ([TNext][wd.di.middleware.TNext]) representing the next middleware or
                handler in the pipeline. The middleware should call this to
                continue processing, or it can choose not to call it to
                short-circuit the pipeline.

        Returns:
            any: The result of the middleware processing. This might be the result
                from `call_next()` or a custom result if the middleware modifies or
                generates a response.
        """


class MiddlewarePipeline:
    """Manages and executes a sequence of middleware components.

    The pipeline allows for adding middleware functions or classes and then
    executing them in the order they were added.

    Attributes:
        _middleware (List[[TMiddleware][wd.di.middleware.TMiddleware][T]]): A list storing the middleware
            functions or adapted middleware classes.
    """

    def __init__(self):
        """Initializes a new, empty MiddlewarePipeline."""
        self._middleware: List[TMiddleware[T]] = []

    def use(self, middleware: TMiddleware[T]) -> "MiddlewarePipeline":
        """Adds a middleware function to the pipeline.

        Args:
            middleware: A callable that conforms to the [TMiddleware][wd.di.middleware.TMiddleware] signature.

        Returns:
            The [MiddlewarePipeline][wd.di.middleware.MiddlewarePipeline] instance for fluent chaining.
        """
        self._middleware.append(middleware)
        return self

    def use_middleware(
        self, middleware_class: type, instance: Optional[any] = None
    ) -> "MiddlewarePipeline":
        """Adds a class-based middleware to the pipeline.

        An adapter is created to make the class's `invoke` method compatible with
        the functional pipeline. If an `instance` is not provided, a new instance
        of `middleware_class` will be created when the adapter is first called.

        Args:
            middleware_class: The class type of the middleware. This class must
                implement the [IMiddleware][wd.di.middleware.IMiddleware] interface (specifically, an
                `async def invoke(self, context: T, call_next: TNext)` method).
            instance: Optional. A pre-existing instance of `middleware_class`.
                If provided, this instance will be used. If `None`, an instance
                will be created on first use.

        Returns:
            The [MiddlewarePipeline][wd.di.middleware.MiddlewarePipeline] instance for fluent chaining.
        """

        def adapter(context: T, call_next: TNext) -> any:
            nonlocal instance
            if instance is None:
                instance = middleware_class()
            return instance.invoke(context, call_next)

        self._middleware.append(adapter)
        return self

    async def execute(self, context: T) -> any:
        """Executes the configured middleware pipeline with the given context.

        Each middleware is called in sequence. The execution starts with the first
        middleware, which can then call `invoke_next` to pass control to the next one.

        Args:
            context: The initial context object to be passed through the pipeline.

        Returns:
            any: The result of the pipeline execution. This is typically the result
                returned by the last middleware or handler in the chain.
                Returns `None` if the pipeline is empty.
        """
        if not self._middleware:
            return None

        index = 0

        async def invoke_next() -> any:
            nonlocal index
            if index < len(self._middleware):
                middleware = self._middleware[index]
                index += 1
                return await middleware(context, invoke_next)
            return None

        return await invoke_next()


class ExceptionHandlerMiddleware(IMiddleware):
    """A built-in middleware that handles exceptions occurring in the pipeline.

    This middleware wraps the call to the next component in a try-except block.
    If an exception occurs further down the pipeline, this middleware will catch it.
    By default, it re-raises the exception, but it can be customized to log or
    transform exceptions.
    """

    async def invoke(self, _context: T, call_next: TNext) -> any:
        try:
            return await call_next()
        except Exception:
            # Log the exception or handle it as needed
            raise


class LoggingMiddleware(IMiddleware):
    """A built-in middleware that logs information about pipeline execution.

    It logs when the pipeline execution starts for a context, when it completes,
    and if any exception occurs.

    Attributes:
        _logger (Callable[[str], None]): The logging function to use. Defaults to `print`.
    """

    def __init__(self, logger: Optional[Callable[[str], None]] = None):
        """Initializes a new LoggingMiddleware instance.

        Args:
            logger: Optional. A callable that takes a string message and logs it.
                If `None`, `print` is used as the default logger.
        """
        self._logger = logger or print

    async def invoke(self, context: T, call_next: TNext) -> any:
        self._logger(f"Executing pipeline with context: {context}")
        try:
            result = await call_next()
            self._logger(f"Pipeline execution completed with result: {result}")
            return result
        except Exception as e:
            self._logger(f"Pipeline execution failed: {e!s}")
            raise


class ValidationMiddleware(IMiddleware):
    """A built-in middleware that validates the context object.

    This middleware uses a provided validator function to check the context.
    If validation fails, it raises a `ValueError`.

    Attributes:
        _validator (Callable[[T], bool]): A function that takes the context
            and returns `True` if valid, `False` otherwise.
    """

    def __init__(self, validator: Callable[[T], bool]):
        """Initializes a new ValidationMiddleware instance.

        Args:
            validator: A callable that takes a context object (of type T)
                and returns `True` if the context is valid, or `False` otherwise.
        """
        self._validator = validator

    async def invoke(self, context: T, call_next: TNext) -> any:
        if not self._validator(context):
            raise ValueError(f"Invalid context: {context}")
        return await call_next()


class CachingMiddleware(IMiddleware):
    """A built-in middleware that caches the results of pipeline execution.

    It attempts to use a hash of the context's `__dict__` as a cache key.
    If the context (or its `__dict__`) is not hashable, caching is skipped for that call.

    Attributes:
        _cache (Dict[any, any]): A dictionary used to store cached results.
    """

    def __init__(self):
        """Initializes a new CachingMiddleware instance with an empty cache."""
        self._cache: Dict[any, any] = {}

    async def invoke(self, context: T, call_next: TNext) -> any:
        # Use context as cache key if it's hashable
        try:
            cache_key = hash(str(context.__dict__))
            if cache_key in self._cache:
                return self._cache[cache_key]

            result = await call_next()
            self._cache[cache_key] = result
            return result
        except (TypeError, AttributeError):
            # If context is not hashable or has no __dict__, skip caching
            return await call_next()
