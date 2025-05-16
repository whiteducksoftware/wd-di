from typing import Callable, TypeVar

from wd.di.container import ServiceProvider

from .middleware import LoggingMiddleware, MiddlewarePipeline
from .service_collection import ServiceCollection

T = TypeVar("T")
TNext = Callable[[], any] # Explicitly define TNext for clarity in the adapter

# Forward declaration for type hinting if ServiceCollection is used in type hints
# before its full definition in this file or if it's a circular dependency concern.
# However, in this case, ServiceCollection is imported and used as a type hint
# for the constructor argument, which is standard.
# class ServiceCollection: # This is a forward reference / type stub for the real one
#     pass                 # that will be passed in. # REMOVE STUB

class MiddlewareBuilder:
    """Builds and configures a [MiddlewarePipeline][wd.di.middleware.MiddlewarePipeline] integrated with a
    [ServiceCollection][wd.di.service_collection.ServiceCollection].

    This builder allows adding middleware functions or classes to a pipeline.
    Middleware classes added via `use_middleware` will be registered with the
    provided [ServiceCollection][wd.di.service_collection.ServiceCollection] and resolved from it during pipeline
    execution.

    Attributes:
        _services ([ServiceCollection][wd.di.service_collection.ServiceCollection]): The service collection used for
            registering and resolving middleware class instances.
        _pipeline ([MiddlewarePipeline][wd.di.middleware.MiddlewarePipeline]): The underlying middleware pipeline
            being configured.
    """

    def __init__(self, services: ServiceCollection):
        """Initializes a new MiddlewareBuilder.

        Args:
            services: The [ServiceCollection][wd.di.service_collection.ServiceCollection] to use for middleware
                dependency injection.
        """
        self._services = services
        self._pipeline = MiddlewarePipeline()

    def use(
        self, middleware: Callable[[T, TNext], any] # Use TNext here
    ) -> "MiddlewareBuilder":
        """Adds a middleware function directly to the pipeline.

        Args:
            middleware: A callable conforming to the middleware signature
                (context: T, next: TNext) -> any.

        Returns:
            The [MiddlewareBuilder][wd.di.middleware_di.MiddlewareBuilder] instance for fluent chaining.
        """
        self._pipeline.use(middleware)
        return self

    def use_middleware(self, middleware_type: type) -> "MiddlewareBuilder":
        """Adds a class-based middleware to the pipeline and registers it with DI.

        The specified `middleware_type` is registered as a transient service in the
        [ServiceCollection][wd.di.service_collection.ServiceCollection]. When the pipeline executes, an instance of
        this middleware will be resolved from a [ServiceProvider][wd.di.container.ServiceProvider] built from the
        `_services` collection for each execution of this middleware component
        in the pipeline.

        Args:
            middleware_type: The class type of the middleware to add. This class
                should typically implement [IMiddleware][wd.di.middleware.IMiddleware] or have a compatible
                `invoke` method.

        Returns:
            The [MiddlewareBuilder][wd.di.middleware_di.MiddlewareBuilder] instance for fluent chaining.
        """
        # Register the middleware type with DI using the provided services instance
        if middleware_type == LoggingMiddleware:
            self._services.add_transient_factory(
                middleware_type, lambda _: LoggingMiddleware() # Assuming LoggingMiddleware can be default constructed
            )
        else:
            # Ensure the middleware itself is registered as transient so each resolution gets a new one
            # if needed by its design
            self._services.add_transient(middleware_type)

        # This adapter will be called by the MiddlewarePipeline for each execution
        def adapter_for_pipeline(context: T, next_func: TNext) -> any:
            # Build provider and resolve middleware instance ONCE PER EXECUTION of this middleware in the pipeline
            # This uses the ServiceCollection available at the time ApplicationBuilder.build() will be called (or later
            # if services are added)
            # which might still be an issue if services are added *after* ApplicationBuilder.build() and before request.
            # However, the more common pattern is that the main service provider is built once.
            # If the goal is to use THE final application provider, that would need to be passed around differently.
            # For now, this builds from the _services collection held by MiddlewareBuilder, which is typically the main
            # app collection.
            provider = self._services.build_service_provider()
            instance = provider.get_service(middleware_type)
            return instance.invoke(context, next_func) # type: ignore

        self._pipeline.use(adapter_for_pipeline) # Use the generic .use() method
        return self

    def build(self) -> MiddlewarePipeline:
        """Builds the configured [MiddlewarePipeline][wd.di.middleware.MiddlewarePipeline].

        Returns:
            The constructed [MiddlewarePipeline][wd.di.middleware.MiddlewarePipeline] containing all added
            middleware components.
        """
        return self._pipeline


class ApplicationBuilder:
    """A builder for configuring an application, including its middleware pipeline.

    This class provides a way to set up services and then configure a
    [MiddlewarePipeline][wd.di.middleware.MiddlewarePipeline] that will be registered as a singleton service.

    Attributes:
        _services ([ServiceCollection][wd.di.service_collection.ServiceCollection]): The service collection for the
            application.
    """

    def __init__(self, services: ServiceCollection):
        """Initializes a new ApplicationBuilder.

        Args:
            services: The [ServiceCollection][wd.di.service_collection.ServiceCollection] for the application.
        """
        self._services = services

    def configure_middleware(
        self, configure: Callable[["MiddlewareBuilder"], None]
    ) -> "ApplicationBuilder":
        """Configures the application's middleware pipeline.

        This method takes a configuration function that will be called with a
        [MiddlewareBuilder][wd.di.middleware_di.MiddlewareBuilder]. The configured pipeline is then registered
        as a singleton [MiddlewarePipeline][wd.di.middleware.MiddlewarePipeline] in the service collection.

        Args:
            configure: A callable that receives a [MiddlewareBuilder][wd.di.middleware_di.MiddlewareBuilder] instance
                and should use it to add middleware components.

        Returns:
            The [ApplicationBuilder][wd.di.middleware_di.ApplicationBuilder] instance for fluent chaining.
        """
        builder = MiddlewareBuilder(self._services)
        configure(builder)
        pipeline = builder.build()

        self._services.add_singleton_factory(MiddlewarePipeline, lambda _: pipeline)
        return self

    def build(self) -> ServiceProvider:
        """Builds the application's [ServiceProvider][wd.di.container.ServiceProvider].

        Finalizes the service registrations and constructs the main
        [ServiceProvider][wd.di.container.ServiceProvider] for the application.

        Returns:
            The built [ServiceProvider][wd.di.container.ServiceProvider] for the application.
        """
        # The ServiceProvider built here is the one that should ideally be used by middleware if they need the "final"
        # app state.
        # The current MiddlewareBuilder approach builds a new provider each time from self._services.
        # This is a complex interaction. The user's suggestion improves it from config-time to per-request, which is
        # better.
        return self._services.build_service_provider()


def create_application_builder(services: ServiceCollection) -> ApplicationBuilder:
    """Creates an [ApplicationBuilder][wd.di.middleware_di.ApplicationBuilder] for a given
    [ServiceCollection][wd.di.service_collection.ServiceCollection].

    This is a convenience factory function.

    Args:
        services: The [ServiceCollection][wd.di.service_collection.ServiceCollection] to be used by the application
        builder.

    Returns:
        A new [ApplicationBuilder][wd.di.middleware_di.ApplicationBuilder] instance.
    """
    return ApplicationBuilder(services)
