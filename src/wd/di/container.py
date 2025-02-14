from typing import Any, Dict, Type, Set, Optional, get_type_hints

from .descriptors import ServiceDescriptor
from .lifetimes import ServiceLifetime

class ServiceProvider:
    def __init__(self, services: Dict[Type, ServiceDescriptor]):
        self._services = services
        self._singletons = {}

    def get_service(self, service_type: Type, resolving: Optional[Set[Type]] = None) -> Any:
        if resolving is None:
            resolving = set()
        if service_type in resolving:
            raise Exception(f"Circular dependency detected for service: {service_type}")
        resolving.add(service_type)
        try:
            descriptor = self._services.get(service_type)
            if descriptor is None:
                raise Exception(f"Service {service_type} not registered.")

            if descriptor.lifetime == ServiceLifetime.SINGLETON:
                if descriptor.instance is None:
                    descriptor.instance = self._create_instance(descriptor, resolving)
                return descriptor.instance
            elif descriptor.lifetime == ServiceLifetime.TRANSIENT:
                return self._create_instance(descriptor, resolving)
            elif descriptor.lifetime == ServiceLifetime.SCOPED:
                raise Exception("Cannot resolve scoped service from the root provider. "
                                "Please create a scope using 'create_scope()' and resolve it from the scope.")
            else:
                raise Exception("Unknown service lifetime.")
        finally:
            resolving.remove(service_type)

    def create_scope(self) -> "Scope":
        return Scope(self._services, self)

    def _create_instance(self, descriptor: ServiceDescriptor, resolving: Set[Type]) -> Any:
        if descriptor.implementation_factory:
            return descriptor.implementation_factory(self)
        else:
            implementation_type = descriptor.implementation_type
            constructor = implementation_type.__init__
            try:
                param_types = get_type_hints(constructor)
            except NameError as e:
                # This catch-all assumes that a NameError during get_type_hints is due to a circular dependency
                # involving local forward references. Re-raise as a circular dependency error.
                raise Exception(f"Circular dependency detected for service: {implementation_type}") from e

            dependencies = {}
            for param, param_type in param_types.items():
                if param == "return":
                    continue
                dependencies[param] = self.get_service(param_type, resolving)
            return implementation_type(**dependencies)  # type: ignore


class Scope(ServiceProvider):
    def __init__(self, services: Dict[Type, ServiceDescriptor], parent_provider: ServiceProvider):
        super().__init__(services)
        self._parent_provider = parent_provider
        self._scoped_instances = {}
        self._disposables = []

    def get_service(self, service_type: Type, resolving: Optional[Set[Type]] = None) -> Any:
        if resolving is None:
            resolving = set()
        if service_type in resolving:
            raise Exception(f"Circular dependency detected for service: {service_type}")
        resolving.add(service_type)
        try:
            descriptor = self._services.get(service_type)
            if descriptor is None:
                raise Exception(f"Service {service_type} not registered.")

            if descriptor.lifetime == ServiceLifetime.SCOPED:
                if service_type not in self._scoped_instances:
                    instance = self._create_instance(descriptor, resolving)
                    self._scoped_instances[service_type] = instance
                    if hasattr(instance, "dispose") and callable(instance.dispose):
                        self._disposables.append(instance)
                    elif hasattr(instance, "close") and callable(instance.close):
                        self._disposables.append(instance)
                return self._scoped_instances[service_type]
            else:
                return super().get_service(service_type, resolving)
        finally:
            resolving.remove(service_type)

    def dispose(self):
        for instance in self._disposables:
            if hasattr(instance, "dispose") and callable(instance.dispose):
                try:
                    instance.dispose()
                except Exception as e:
                    print(f"Error disposing {instance}: {e}")
            elif hasattr(instance, "close") and callable(instance.close):
                try:
                    instance.close()
                except Exception as e:
                    print(f"Error closing {instance}: {e}")
        self._disposables.clear()
        self._scoped_instances.clear()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.dispose()
