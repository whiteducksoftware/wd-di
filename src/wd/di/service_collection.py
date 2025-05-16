"""Service registration API for **wd-di** (decorator-aware).

This module provides the [ServiceCollection][wd.di.service_collection.ServiceCollection] class,
which is the primary entry point for users to define how services in their application
should be created and managed. It employs a fluent Domain Specific Language (DSL)
for registering services, their implementations, and their lifetimes.

Key features include:
    - Registration of services with transient, scoped, or singleton lifetimes.
    - Support for factory functions to create service instances.
    - Registration of pre-existing instances as singletons.
    - Configuration binding to strongly-typed options objects via [IConfiguration][wd.di.config.IConfiguration].
    - Python-level decorators (`@singleton`, `@scoped`, `@transient`) for concise
      service registration.
    - Support for decorating (wrapping) already registered services to add
      cross-cutting concerns like logging or caching.

The API is designed to be additive, ensuring that existing user code relying on
previous versions of this library does not require modification.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Generic, Iterable, Optional, Type, TypeVar, overload

from .config import IConfiguration, Options, OptionsBuilder
from .descriptors import DecoratorFactory, ServiceDescriptor
from .exceptions import InvalidOperationError
from .lifetimes import ServiceLifetime

if TYPE_CHECKING:  # pragma: no cover
    from .container import ServiceProvider

__all__ = ["ServiceCollection"]

T = TypeVar("T")
S = TypeVar("S")  # service/abstraction type for decorator overloads


class ServiceCollection(Generic[T]):
    """Manages service registrations and builds a [ServiceProvider][wd.di.container.ServiceProvider].

    This class acts as a registry for defining how different services in an
    application should be created and managed. Services are first registered here,
    specifying their type, implementation, and lifetime. Once all services are
    registered, this collection is "built" to create a [ServiceProvider][wd.di.container.ServiceProvider],
    which is then used to retrieve service instances.

    Attributes:
        _services (List[[ServiceDescriptor][wd.di.descriptors.ServiceDescriptor][any]]): A list of service descriptors.
        _is_built (bool): True if the [ServiceProvider][wd.di.container.ServiceProvider] has been built,
        False otherwise.
    """

    # ------------------------------------------------------------------ #
    # Construction
    # ------------------------------------------------------------------ #
    def __init__(self, descriptors: Optional[Iterable[ServiceDescriptor[any]]] = None):
        """Initializes a new [ServiceCollection][wd.di.service_collection.ServiceCollection].

        Args:
            descriptors: An optional initial list of
                [ServiceDescriptor][wd.di.descriptors.ServiceDescriptor] objects.
                Useful for starting with pre-registered services.
        """
        self._services: list[ServiceDescriptor[any]] = list(descriptors) if descriptors else []
        self._is_built: bool = False

    # ------------------------------------------------------------------ #
    # Private helpers
    # ------------------------------------------------------------------ #
    def _ensure_not_built(self) -> None:
        """Checks if the [ServiceProvider][wd.di.container.ServiceProvider] has been built.

        Raises:
            [InvalidOperationError][wd.di.exceptions.InvalidOperationError]: If the
                [ServiceProvider][wd.di.container.ServiceProvider] has already been built,
                preventing further modifications to the collection.
        """
        if self._is_built:
            raise InvalidOperationError(
                "Cannot modify ServiceCollection after ServiceProvider has been built."
            )

    def _add(
        self,
        lifetime: ServiceLifetime,
        service_type: Type[any],
        implementation_type: Optional[Type[any]] = None,
        factory: Optional[Callable[["ServiceProvider"], any]] = None,
    ) -> "ServiceCollection":
        """Creates and stores a [ServiceDescriptor][wd.di.descriptors.ServiceDescriptor].

        This internal helper is used by the public `add_transient`, `add_scoped`,
        and `add_singleton` methods. If both `implementation_type` and `factory`
        are `None`, it assumes a "self-binding" where `implementation_type`
        is set to `service_type`. This preserves legacy behavior.

        Args:
            lifetime: The [ServiceLifetime][wd.di.lifetimes.ServiceLifetime] for the service.
            service_type: The type (often an interface) of the service.
            implementation_type: The concrete class implementing the service.
                Optional if `factory` is provided or for self-binding.
            factory: A function (`[ServiceProvider][wd.di.container.ServiceProvider] -> any`) that creates
                the service instance. Optional if `implementation_type` is provided.

        Returns:
            The [ServiceCollection][wd.di.service_collection.ServiceCollection] instance, allowing for fluent method
            chaining.
        """
        self._ensure_not_built()

        if implementation_type is None and factory is None:
            implementation_type = service_type

        descriptor = ServiceDescriptor(
            service_type,
            implementation_type,
            factory,
            lifetime,
        )
        self._services.append(descriptor)
        return self  # fluent API

    # ------------------------------------------------------------------ #
    # Public API - registrations (class or factory)
    # ------------------------------------------------------------------ #
    def add_transient(
        self,
        service_type: Type[any],
        implementation_type: Optional[Type[any]] = None,
        factory: Optional[Callable[["ServiceProvider"], any]] = None,
    ) -> "ServiceCollection":
        """Registers a transient service.

        A new instance of the service is created each time it is requested from the
        [ServiceProvider][wd.di.container.ServiceProvider]. This lifetime is suitable for lightweight,
        stateless services.

        Args:
            service_type: The type (interface or class) of the service to register.
            implementation_type: The concrete class that implements the service.
                If `None` and no `factory` is provided, `service_type` is used
                (self-binding).
            factory: A function (`[ServiceProvider][wd.di.container.ServiceProvider] -> any`) that creates
                an instance of the service.

        Returns:
            The [ServiceCollection][wd.di.service_collection.ServiceCollection] instance for fluent chaining.
        """
        return self._add(ServiceLifetime.TRANSIENT, service_type, implementation_type, factory)

    def add_scoped(
        self,
        service_type: Type[any],
        implementation_type: Optional[Type[any]] = None,
        factory: Optional[Callable[["ServiceProvider"], any]] = None,
    ) -> "ServiceCollection":
        """Registers a scoped service.

        A single instance of the service is created per scope (e.g., within a web
        request or a custom scope). All requests for this service within the same
        scope will receive the same instance.

        Args:
            service_type: The type (interface or class) of the service to register.
            implementation_type: The concrete class that implements the service.
                If `None` and no `factory` is provided, `service_type` is used
                (self-binding).
            factory: A function (`[ServiceProvider][wd.di.container.ServiceProvider] -> any`) that creates
                an instance of the service.

        Returns:
            The [ServiceCollection][wd.di.service_collection.ServiceCollection] instance for fluent chaining.
        """
        return self._add(ServiceLifetime.SCOPED, service_type, implementation_type, factory)

    def add_singleton(
        self,
        service_type: Type[any],
        implementation_type: Optional[Type[any]] = None,
        factory: Optional[Callable[["ServiceProvider"], any]] = None,
    ) -> "ServiceCollection":
        """Registers a singleton service.

        A single instance of the service is created for the lifetime of the
        application's [ServiceProvider][wd.di.container.ServiceProvider]. All requests for this service
        will receive the same instance. This is suitable for services that are
        expensive to create or need to maintain global state.

        Args:
            service_type: The type (interface or class) of the service to register.
            implementation_type: The concrete class that implements the service.
                If `None` and no `factory` is provided, `service_type` is used
                (self-binding).
            factory: A function (`[ServiceProvider][wd.di.container.ServiceProvider] -> any`) that creates
                the single instance of the service.

        Returns:
            The [ServiceCollection][wd.di.service_collection.ServiceCollection] instance for fluent chaining.
        """
        return self._add(ServiceLifetime.SINGLETON, service_type, implementation_type, factory)

    # ------------------------------------------------------------------ #
    # Convenience - direct instance
    # ------------------------------------------------------------------ #
    def add_instance(self, service_type: Type[any], instance: any) -> "ServiceCollection":
        """Registers an existing object instance as a singleton service.

        The provided `instance` will be used for all requests for `service_type`.
        This is effectively a singleton registration where the instance is
        provided upfront.

        Args:
            service_type: The type (interface or class) against which to register
                the instance.
            instance: The pre-existing object instance.

        Returns:
            The [ServiceCollection][wd.di.service_collection.ServiceCollection] instance for fluent chaining.
        """
        self._ensure_not_built()

        def _factory(_: "ServiceProvider") -> any:
            return instance

        descriptor = ServiceDescriptor(
            service_type,
            factory=_factory,
            lifetime=ServiceLifetime.SINGLETON,
        )
        self._services.append(descriptor)
        return self

    # ------------------------------------------------------------------ #
    # Convenience - explicit factory overloads
    # ------------------------------------------------------------------ #
    def add_transient_factory(
        self,
        service_type: Type[any],
        factory: Callable[["ServiceProvider"], any],
    ) -> "ServiceCollection":
        """Registers a transient service using an explicit factory function.

        Args:
            service_type: The type (interface or class) of the service.
            factory: A function (`[ServiceProvider][wd.di.container.ServiceProvider] -> any`) that creates a new
                instance of the service each time it's called.

        Returns:
            The [ServiceCollection][wd.di.service_collection.ServiceCollection] instance for fluent chaining.
        """
        return self._add(ServiceLifetime.TRANSIENT, service_type, factory=factory)

    def add_scoped_factory(
        self,
        service_type: Type[any],
        factory: Callable[["ServiceProvider"], any],
    ) -> "ServiceCollection":
        """Registers a scoped service using an explicit factory function.

        Args:
            service_type: The type (interface or class) of the service.
            factory: A function (`[ServiceProvider][wd.di.container.ServiceProvider] -> any`) that creates an instance
                of the service once per scope.

        Returns:
            The [ServiceCollection][wd.di.service_collection.ServiceCollection] instance for fluent chaining.
        """
        return self._add(ServiceLifetime.SCOPED, service_type, factory=factory)

    def add_singleton_factory(
        self,
        service_type: Type[any],
        factory: Callable[["ServiceProvider"], any],
    ) -> "ServiceCollection":
        """Registers a singleton service using an explicit factory function.

        Args:
            service_type: The type (interface or class) of the service.
            factory: A function (`[ServiceProvider][wd.di.container.ServiceProvider] -> any`) that creates the single
                instance of the service for the application's lifetime.

        Returns:
            The [ServiceCollection][wd.di.service_collection.ServiceCollection] instance for fluent chaining.
        """
        return self._add(ServiceLifetime.SINGLETON, service_type, factory=factory)

    # ------------------------------------------------------------------ #
    # Options / configuration support
    # ------------------------------------------------------------------ #
    def configure(self, options_type: Type[T], *, section: Optional[str] = None) -> "ServiceCollection":
        """Registers a configuration options class to be loaded from [IConfiguration][wd.di.config.IConfiguration].

        This method makes `[Options][wd.di.config.Options][options_type]` available as a singleton service.
        The value of these options is an instance of `options_type`, populated by
        binding against the application's [IConfiguration][wd.di.config.IConfiguration] source when the
        [ServiceProvider][wd.di.container.ServiceProvider] is built.

        Example:
            A common use case is to define a settings class:
            ```python
            class MySettings:
                property_a: str
                property_b: int
            ```
            Then register it with the service collection:
            ```python
            services = ServiceCollection()
            services.configure(MySettings, section="MyApplication:MySettings")
            ```
            Later, it can be resolved from a [ServiceProvider][wd.di.container.ServiceProvider]:
            ```python
            provider = services.build_service_provider()
            settings_options = provider.get_service(Options[MySettings])
            if settings_options:
                my_actual_settings = settings_options.value
                print(my_actual_settings.property_a)
            ```

        Args:
            options_type: The class definition for the options (e.g., `MySettings`).
                This class should have type annotations for its fields.
            section: Optional. The name of the configuration section from which
                to load the options. If `None`, options are typically loaded
                from a section matching the `options_type` class name or from
                the root of the configuration.

        Returns:
            The [ServiceCollection][wd.di.service_collection.ServiceCollection] instance for fluent chaining.
        """
        self._ensure_not_built()

        def _factory(sp: "ServiceProvider") -> Options[T]:  # runtime generic
            try:
                configuration = sp.get_service(IConfiguration)
            except Exception as exc:  # pragma: no cover - defensive
                raise Exception("IConfiguration service not registered") from exc

            builder = OptionsBuilder(options_type)
            builder.bind_configuration(configuration, section)
            return Options(builder.build())

        # Register an *open-generic* Options[...] singleton.
        self.add_singleton_factory(Options[options_type], _factory)  # type: ignore[index]
        return self

    # ------------------------------------------------------------------ #
    # Python-level decorators - syntactic sugar
    # ------------------------------------------------------------------ #
    # Singleton -------------------------------------------------------- #
    @overload
    def singleton(self) -> Callable[[Type[T]], Type[T]]: ...

    @overload
    def singleton(self, service_type: Type[S]) -> Callable[[Type[T]], Type[T]]: ...

    def singleton(self, service_type: Optional[Type[S]] = None) -> Callable[[Type[T]], Type[T]]:  # type: ignore[override]
        """Decorator to register a class as a singleton service.

        This provides syntactic sugar for `add_singleton`.

        Examples:
            To register `MyService` as a singleton of its own type:
            ```python
            @services.singleton()
            class MyService:
                pass
            ```

            To register `MyServiceImpl` as a singleton for the `IMyService` interface:
            ```python
            class IMyService(ABC): ...

            @services.singleton(IMyService)
            class MyServiceImpl(IMyService):
                pass
            ```

        Args:
            service_type: Optional. The type (interface or class) to register
                the decorated class against. If `None`, the decorated class is
                registered against its own type (self-binding).

        Returns:
            A decorator function that registers the class and returns it,
            allowing the class definition to proceed as usual.
        """
        def _decorator(impl: Type[T]) -> Type[T]:
            if service_type is None:
                self.add_singleton(impl, impl)
            else:
                self.add_singleton(service_type, impl)  # type: ignore[arg-type]
            return impl

        return _decorator

    # Scoped ----------------------------------------------------------- #
    @overload
    def scoped(self) -> Callable[[Type[T]], Type[T]]: ...

    @overload
    def scoped(self, service_type: Type[S]) -> Callable[[Type[T]], Type[T]]: ...

    def scoped(self, service_type: Optional[Type[S]] = None) -> Callable[[Type[T]], Type[T]]:  # type: ignore[override]
        """Decorator to register a class as a scoped service.

        This provides syntactic sugar for `add_scoped`.

        Examples:
            To register `UserSessionService` as a scoped service of its own type:
            ```python
            @services.scoped()
            class UserSessionService:
                pass
            ```

            To register `UserSessionServiceImpl` as a scoped service for the
            `IUserSessionService` interface:
            ```python
            class IUserSessionService(ABC): ...

            @services.scoped(IUserSessionService)
            class UserSessionServiceImpl(IUserSessionService):
                pass
            ```

        Args:
            service_type: Optional. The type (interface or class) to register
                the decorated class against. If `None`, the decorated class is
                registered against its own type (self-binding).

        Returns:
            A decorator function that registers the class and returns it.
        """
        def _decorator(impl: Type[T]) -> Type[T]:
            if service_type is None:
                self.add_scoped(impl, impl)
            else:
                self.add_scoped(service_type, impl)  # type: ignore[arg-type]
            return impl

        return _decorator

    # Transient -------------------------------------------------------- #
    @overload
    def transient(self) -> Callable[[Type[T]], Type[T]]: ...

    @overload
    def transient(self, service_type: Type[S]) -> Callable[[Type[T]], Type[T]]: ...

    def transient(self, service_type: Optional[Type[S]] = None) -> Callable[[Type[T]], Type[T]]:  # type: ignore[override]
        """Decorator to register a class as a transient service.

        This provides syntactic sugar for `add_transient`.

        Examples:
            To register `EmailSender` as a transient service of its own type:
            ```python
            @services.transient()
            class EmailSender:
                pass
            ```

            To register `EmailSenderImpl` as a transient service for the
            `IEmailSender` interface:
            ```python
            class IEmailSender(ABC): ...

            @services.transient(IEmailSender)
            class EmailSenderImpl(IEmailSender):
                pass
            ```

        Args:
            service_type: Optional. The type (interface or class) to register
                the decorated class against. If `None`, the decorated class is
                registered against its own type (self-binding).

        Returns:
            A decorator function that registers the class and returns it.
        """
        def _decorator(impl: Type[T]) -> Type[T]:
            if service_type is None:
                self.add_transient(impl, impl)
            else:
                self.add_transient(service_type, impl)  # type: ignore[arg-type]
            return impl

        return _decorator

    # ------------------------------------------------------------------ #
    # Public API - decorator support (service *wrappers*)
    # ------------------------------------------------------------------ #
    def decorate(self, service_type: Type[any], decorator: DecoratorFactory) -> "ServiceCollection":
        """Applies a decorator (wrapper) to an already registered service.

        This method allows augmenting the behavior of a service without modifying
        its original implementation. The `decorator` is a factory function that
        receives the original service instance (and the current
        [ServiceProvider][wd.di.container.ServiceProvider]) and returns a new, wrapped instance that
        replaces the original registration.

        This is useful for adding cross-cutting concerns like logging, caching,
        or monitoring to services in a clean and decoupled way.

        Args:
            service_type: The type of the service to be decorated. This must
                match a service type already registered in the collection.
            decorator: A [DecoratorFactory][wd.di.descriptors.DecoratorFactory] function.
                This factory takes two arguments: the service instance to be
                decorated and the current [ServiceProvider][wd.di.container.ServiceProvider]. It should
                return the decorated (wrapped) instance of the service.

        Returns:
            The [ServiceCollection][wd.di.service_collection.ServiceCollection] instance for fluent chaining.

        Raises:
            KeyError: If no service is registered for the given `service_type`,
                as there is no existing registration to apply the decorator to.
        """
        self._ensure_not_built()

        for idx, descriptor in enumerate(self._services):
            if descriptor.service_type is service_type:
                self._services[idx] = descriptor.with_decorator(decorator)
                break
        else:  # pragma: no cover
            raise KeyError(
                f"No service registered for {service_type.__name__!s}; cannot apply decorator."
            )

        return self

    # ------------------------------------------------------------------ #
    # Build provider
    # ------------------------------------------------------------------ #
    def build_service_provider(self) -> "ServiceProvider":
        """Creates a [ServiceProvider][wd.di.container.ServiceProvider] from the registered services.

        Once this method is called, the [ServiceCollection][wd.di.service_collection.ServiceCollection] is considered
        "built"
        and can no longer be modified. The returned [ServiceProvider][wd.di.container.ServiceProvider]
        is then used to resolve (get instances of) the registered services.

        A local import of [ServiceProvider][wd.di.container.ServiceProvider] is used here to avoid potential
        circular dependencies and to defer the import cost until it's actually needed.

        Returns:
            A new [ServiceProvider][wd.di.container.ServiceProvider] instance configured with all the
            services defined in this collection.
        """
        from .container import ServiceProvider  # local import avoids heavy cost when only building collections

        self._is_built = True
        return ServiceProvider(self._services)

    # ------------------------------------------------------------------ #
    # Introspection helpers
    # ------------------------------------------------------------------ #
    def __iter__(self):
        """Allows iteration over the registered [ServiceDescriptor][wd.di.descriptors.ServiceDescriptor] objects.

        Yields:
            [ServiceDescriptor][wd.di.descriptors.ServiceDescriptor]: The next service descriptor in the collection.
        """
        return iter(self._services)

    def __len__(self) -> int:  # type: ignore[override]
        """Returns the number of services registered in this collection.

        Returns:
            int: The count of registered services.
        """
        return len(self._services)

    def __repr__(self) -> str:  # pragma: no cover
        """Provides a developer-friendly string representation of the
        [ServiceCollection][wd.di.service_collection.ServiceCollection].

        Returns:
            str: A string representation indicating the number of services
                 and whether the provider has been built.
        """
        return f"<ServiceCollection services={len(self)} built={self._is_built}>"
