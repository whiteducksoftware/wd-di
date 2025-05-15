# di_container/service_collection.py

from typing import Any, Callable, Dict, Optional, Type, TypeVar, TYPE_CHECKING, Generic, overload

from .descriptors import ServiceDescriptor
from .lifetimes import ServiceLifetime
from .config import IConfiguration, Options, OptionsBuilder

if TYPE_CHECKING:
    from .container import ServiceProvider


T = TypeVar("T")
S = TypeVar("S") # Added for decorator type hints


class ServiceCollection:
    def __init__(self):
        self._services: Dict[Type, ServiceDescriptor] = {}

    def add_transient_factory(
        self, service_type: Type, factory: Callable[["ServiceProvider"], Any]
    ):
        descriptor = ServiceDescriptor(
            service_type,
            implementation_factory=factory,
            lifetime=ServiceLifetime.TRANSIENT,
        )
        self._services[service_type] = descriptor

    def add_singleton_factory(
        self, service_type: Type, factory: Callable[["ServiceProvider"], Any]
    ):
        descriptor = ServiceDescriptor(
            service_type,
            implementation_factory=factory,
            lifetime=ServiceLifetime.SINGLETON,
        )
        self._services[service_type] = descriptor

    def add_transient(
        self, service_type: Type, implementation_type: Optional[Type] = None
    ):
        self._add_service(service_type, implementation_type, ServiceLifetime.TRANSIENT)

    def add_singleton(
        self, service_type: Type, implementation_type: Optional[Type] = None
    ):
        self._add_service(service_type, implementation_type, ServiceLifetime.SINGLETON)

    def add_scoped(
        self, service_type: Type, implementation_type: Optional[Type] = None
    ):
        self._add_service(service_type, implementation_type, ServiceLifetime.SCOPED)

    def _add_service(
        self,
        service_type: Type,
        implementation_type: Optional[Type],
        lifetime: ServiceLifetime,
    ):
        if implementation_type is None:
            implementation_type = service_type
        descriptor = ServiceDescriptor(
            service_type, implementation_type, None, lifetime
        )
        self._services[service_type] = descriptor

    def build_service_provider(self):
        from .container import ServiceProvider

        return ServiceProvider(self._services)
    
    def add_instance(self, service_type: Type, instance: Any):
        """
        Register an *already-constructed* object as a singleton.

        We implement this by delegating to `add_singleton_factory`, wrapping the
        instance in a trivial factory (`lambda _: instance`).  That lets the
        existing provider logic—already designed to call factories for singletons—
        do all the work, without touching `ServiceProvider`.
        """
        # The lambda’s sole parameter is the ServiceProvider; it’s unused.
        self.add_singleton_factory(service_type, lambda _: instance)

    def configure(
        self, options_type: Type[T], *, section: Optional[str] = None
    ) -> None:
        """Configure options binding from configuration."""

        def factory(sp: "ServiceProvider") -> Options[T]:
            try:
                configuration = sp.get_service(IConfiguration)
                builder = OptionsBuilder(options_type)
                builder.bind_configuration(configuration, section)
                return Options(builder.build())
            except Exception as e:
                raise Exception("Configuration service not registered") from e

        self.add_singleton_factory(Options[options_type], factory)  # type: ignore

    # -- DECORATOR REGISTRATION -------------------------------------
    @overload  # @services.singleton()
    def singleton(self) -> Callable[[Type[T]], Type[T]]: ...
    @overload  # @services.singleton(IMyInterface)
    def singleton(self, service_type: Type[S]) -> Callable[[Type[T]], Type[T]]: ...

    def singleton(self, service_type: Optional[Type[S]] = None) -> Callable[[Type[T]], Type[T]]:
        def decorator(impl: Type[T]) -> Type[T]:
            if service_type is None:
                self.add_singleton(impl, impl)
            else:
                # We need to tell mypy that service_type is not None here.
                # However, the overloads should handle the external type checking.
                self.add_singleton(service_type, impl) # type: ignore
            return impl
        return decorator

    @overload  # @services.transient()
    def transient(self) -> Callable[[Type[T]], Type[T]]: ...
    @overload  # @services.transient(IMyInterface)
    def transient(self, service_type: Type[S]) -> Callable[[Type[T]], Type[T]]: ...

    def transient(self, service_type: Optional[Type[S]] = None) -> Callable[[Type[T]], Type[T]]:
        def decorator(impl: Type[T]) -> Type[T]:
            if service_type is None:
                self.add_transient(impl, impl)
            else:
                self.add_transient(service_type, impl) # type: ignore
            return impl
        return decorator

    @overload  # @services.scoped()
    def scoped(self) -> Callable[[Type[T]], Type[T]]: ...
    @overload  # @services.scoped(IMyInterface)
    def scoped(self, service_type: Type[S]) -> Callable[[Type[T]], Type[T]]: ...

    def scoped(self, service_type: Optional[Type[S]] = None) -> Callable[[Type[T]], Type[T]]:
        def decorator(impl: Type[T]) -> Type[T]:
            if service_type is None:
                self.add_scoped(impl, impl)
            else:
                self.add_scoped(service_type, impl) # type: ignore
            return impl
        return decorator
