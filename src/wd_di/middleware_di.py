from typing import Any, Callable, Optional, TypeVar
from .middleware import IMiddleware, MiddlewarePipeline, LoggingMiddleware
from .service_collection import ServiceCollection

T = TypeVar("T")


class MiddlewareBuilder:
    """Builder for configuring middleware in the DI container."""

    def __init__(self, services: ServiceCollection):
        self._services = services
        self._pipeline = MiddlewarePipeline()

    def use(
        self, middleware: Callable[[T, Callable[[], Any]], Any]
    ) -> "MiddlewareBuilder":
        """Add a middleware function to the pipeline."""
        self._pipeline.use(middleware)
        return self

    def use_middleware(self, middleware_type: type) -> "MiddlewareBuilder":
        """Add a middleware class to the pipeline."""
        # Register the middleware type with DI
        if middleware_type == LoggingMiddleware:
            # Special handling for LoggingMiddleware to provide default logger
            self._services.add_transient_factory(
                middleware_type, lambda _: LoggingMiddleware()
            )
        else:
            self._services.add_transient(middleware_type)

        # Create factory to resolve middleware instance from DI
        def create_middleware():
            provider = self._services.build_service_provider()
            return provider.get_service(middleware_type)

        self._pipeline.use_middleware(middleware_type, instance=create_middleware())
        return self

    def build(self) -> MiddlewarePipeline:
        """Build the middleware pipeline."""
        return self._pipeline


class ApplicationBuilder:
    """Builder for configuring the application with middleware support."""

    def __init__(self, services: ServiceCollection):
        self._services = services

    def configure_middleware(
        self, configure: Callable[["MiddlewareBuilder"], None]
    ) -> "ApplicationBuilder":
        """Configure the middleware pipeline."""
        builder = MiddlewareBuilder(self._services)
        configure(builder)
        pipeline = builder.build()

        # Register the pipeline as a singleton
        self._services.add_singleton_factory(MiddlewarePipeline, lambda _: pipeline)
        return self

    def build(self):
        """Build the application."""
        return self._services.build_service_provider()


# Extension methods for ServiceCollection
def create_application_builder(services: ServiceCollection) -> ApplicationBuilder:
    """Create an application builder for the service collection."""
    return ApplicationBuilder(services)


# Attach the extension method to ServiceCollection
ServiceCollection.create_application_builder = create_application_builder
