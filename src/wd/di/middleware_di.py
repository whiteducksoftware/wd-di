from typing import Any, Callable, Optional, TypeVar
from .middleware import IMiddleware, MiddlewarePipeline, LoggingMiddleware
from .service_collection import ServiceCollection

T = TypeVar("T")
TNext = Callable[[], Any] # Explicitly define TNext for clarity in the adapter

# Forward declaration for type hinting if ServiceCollection is used in type hints
# before its full definition in this file or if it's a circular dependency concern.
# However, in this case, ServiceCollection is imported and used as a type hint
# for the constructor argument, which is standard.
# class ServiceCollection: # This is a forward reference / type stub for the real one
#     pass                 # that will be passed in. # REMOVE STUB

class MiddlewareBuilder:
    """Builder for configuring middleware in the DI container."""

    def __init__(self, services: ServiceCollection):
        self._services = services
        self._pipeline = MiddlewarePipeline()

    def use(
        self, middleware: Callable[[T, TNext], Any] # Use TNext here
    ) -> "MiddlewareBuilder":
        """Add a middleware function to the pipeline."""
        self._pipeline.use(middleware)
        return self

    def use_middleware(self, middleware_type: type) -> "MiddlewareBuilder":
        """Add a middleware class to the pipeline."""
        # Register the middleware type with DI using the provided services instance
        if middleware_type == LoggingMiddleware:
            self._services.add_transient_factory(
                middleware_type, lambda _: LoggingMiddleware() # Assuming LoggingMiddleware can be default constructed or gets deps
            )
        else:
            # Ensure the middleware itself is registered as transient so each resolution gets a new one if needed by its design
            self._services.add_transient(middleware_type)

        # This adapter will be called by the MiddlewarePipeline for each execution
        def adapter_for_pipeline(context: T, next_func: TNext) -> Any:
            # Build provider and resolve middleware instance ONCE PER EXECUTION of this middleware in the pipeline
            # This uses the ServiceCollection available at the time ApplicationBuilder.build() will be called (or later if services are added)
            # which might still be an issue if services are added *after* ApplicationBuilder.build() and before request.
            # However, the more common pattern is that the main service provider is built once.
            # If the goal is to use THE final application provider, that would need to be passed around differently.
            # For now, this builds from the _services collection held by MiddlewareBuilder, which is typically the main app collection.
            provider = self._services.build_service_provider() 
            instance = provider.get_service(middleware_type)
            return instance.invoke(context, next_func) # type: ignore

        self._pipeline.use(adapter_for_pipeline) # Use the generic .use() method
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

        self._services.add_singleton_factory(MiddlewarePipeline, lambda _: pipeline)
        return self

    def build(self):
        """Build the application."""
        # The ServiceProvider built here is the one that should ideally be used by middleware if they need the "final" app state.
        # The current MiddlewareBuilder approach builds a new provider each time from self._services.
        # This is a complex interaction. The user's suggestion improves it from config-time to per-request, which is better.
        return self._services.build_service_provider()


def create_application_builder(services: ServiceCollection) -> ApplicationBuilder:
    """Create an application builder for the service collection."""
    return ApplicationBuilder(services)


# Attach the extension method to ServiceCollection - This is done in __init__.py now
# ServiceCollection.create_application_builder = create_application_builder
