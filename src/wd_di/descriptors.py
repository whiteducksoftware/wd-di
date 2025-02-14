from typing import Any, Callable, Optional, Type, TYPE_CHECKING

from .lifetimes import ServiceLifetime

if TYPE_CHECKING:
    from .container import ServiceProvider


class ServiceDescriptor:
    def __init__(
        self,
        service_type: Type,
        implementation_type: Optional[Type] = None,
        implementation_factory: Optional[Callable[["ServiceProvider"], Any]] = None,
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
    ):
        self.service_type = service_type
        self.implementation_type = implementation_type
        self.implementation_factory = implementation_factory
        self.lifetime = lifetime
        self.instance = None  # For singleton
