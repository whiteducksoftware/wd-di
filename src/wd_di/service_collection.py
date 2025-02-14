# di_container/service_collection.py

from typing import Any, Callable, Dict, Optional, Type, TypeVar, TYPE_CHECKING, Generic

from .descriptors import ServiceDescriptor
from .lifetimes import ServiceLifetime
from .config import IConfiguration, Options, OptionsBuilder

if TYPE_CHECKING:
    from .container import ServiceProvider


T = TypeVar("T")


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

    def transient(self, implementation_type: Type):
        self.add_transient(implementation_type)
        return implementation_type

    def singleton(self, implementation_type: Type):
        self.add_singleton(implementation_type)
        return implementation_type

    def scoped(self, implementation_type: Type):
        self.add_scoped(implementation_type)
        return implementation_type

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
        Register an already constructed instance as a singleton service.
        This instance will be returned whenever service_type is requested.
        """
        descriptor = ServiceDescriptor(service_type, lifetime=ServiceLifetime.SINGLETON)
        descriptor.instance = instance
        self._services[service_type] = descriptor

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
