from typing import Any, Dict, Type, Set, Optional, get_type_hints, TypeVar, Generic, overload, List
from contextvars import ContextVar, Token

from .descriptors import ServiceDescriptor
from .lifetimes import ServiceLifetime

T = TypeVar('T')

# ContextVar for managing the resolving stack for circular dependency detection in a thread-safe manner.
# Each async task or thread will have its own stack.
_current_resolving_stack: ContextVar[List[Type]] = ContextVar("current_resolving_stack")

class ServiceProvider:
    def __init__(self, services: Dict[Type, ServiceDescriptor]):
        self._services = services
        self._singletons = {}

    @overload
    def get_service(self, service_type: Type[T]) -> T: ...

    def get_service(self, service_type: Type[T]) -> T:
        current_stack: List[Type]
        try:
            current_stack = _current_resolving_stack.get()
        except LookupError:
            current_stack = []
        
        if service_type in current_stack:
            # Stack includes current service_type, so it's a cycle
            raise Exception(f"Circular dependency detected for service: {service_type}. Resolution stack: {current_stack + [service_type]}")
        
        # Set new stack for this resolution context
        new_stack = current_stack + [service_type]
        token = _current_resolving_stack.set(new_stack)

        try:
            descriptor = self._services.get(service_type)
            if descriptor is None:
                raise Exception(f"Service {service_type} not registered.")

            if descriptor.lifetime == ServiceLifetime.SINGLETON:
                if service_type not in self._singletons:
                    self._singletons[service_type] = self._create_instance(descriptor)
                return self._singletons[service_type]
            elif descriptor.lifetime == ServiceLifetime.TRANSIENT:
                return self._create_instance(descriptor)
            elif descriptor.lifetime == ServiceLifetime.SCOPED:
                raise Exception("Cannot resolve scoped service from the root provider. "
                                "Please create a scope using 'create_scope()' and resolve it from the scope.")
            else:
                raise Exception("Unknown service lifetime.")
        finally:
            _current_resolving_stack.reset(token) # Reset to previous stack

    def create_scope(self) -> "Scope":
        return Scope(self._services, self._singletons, self)

    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        if descriptor.implementation_factory:
            return descriptor.implementation_factory(self)
        else:
            implementation_type = descriptor.implementation_type
            if implementation_type is None:
                raise Exception(f"Service descriptor for {descriptor.service_type} has no implementation type or factory.")

            constructor = implementation_type.__init__
            try:
                param_types = get_type_hints(constructor)
            except NameError as e:
                # If NameError occurs, capture current stack for better diagnostics
                current_stack_for_error: List[Type]
                try:
                    current_stack_for_error = _current_resolving_stack.get()
                except LookupError:
                    current_stack_for_error = [] # Should ideally be set if we are in _create_instance
                raise Exception(f"Failed to resolve dependencies for {implementation_type} due to NameError (potential forward reference in a circular dependency): {e}. Resolution stack: {current_stack_for_error}") from e

            dependencies = {}
            for param, param_type in param_types.items():
                if param == "return":
                    continue
                dependencies[param] = self.get_service(param_type) # This will use the updated ContextVar logic
            return implementation_type(**dependencies)  # type: ignore


class Scope(ServiceProvider):
    def __init__(self, services: Dict[Type, ServiceDescriptor], root_singletons: Dict[Type, Any], parent_provider: ServiceProvider):
        super().__init__(services)
        self._parent_provider = parent_provider
        self._root_singletons = root_singletons
        self._scoped_instances = {}
        self._disposables = []

    @overload
    def get_service(self, service_type: Type[T]) -> T: ...

    def get_service(self, service_type: Type[T]) -> T:
        current_stack: List[Type]
        try:
            current_stack = _current_resolving_stack.get()
        except LookupError:
            current_stack = []

        if service_type in current_stack:
            raise Exception(f"Circular dependency detected for service: {service_type}. Resolution stack: {current_stack + [service_type]}")

        new_stack = current_stack + [service_type]
        token = _current_resolving_stack.set(new_stack)

        try:
            descriptor = self._services.get(service_type)
            if descriptor is None:
                raise Exception(f"Service {service_type} not registered.")

            if descriptor.lifetime == ServiceLifetime.SCOPED:
                if service_type not in self._scoped_instances:
                    instance = self._create_instance(descriptor)
                    self._scoped_instances[service_type] = instance
                    if hasattr(instance, "dispose") and callable(instance.dispose):
                        self._disposables.append(instance)
                    elif hasattr(instance, "close") and callable(instance.close):
                        self._disposables.append(instance)
                return self._scoped_instances[service_type]
            elif descriptor.lifetime == ServiceLifetime.SINGLETON:
                if service_type not in self._root_singletons:
                    # Create singleton via parent if not exists, ensuring it's stored in root_singletons
                    # This path should ideally be via parent_provider.get_service(service_type) to ensure
                    # parent's full singleton creation logic (including its _create_instance if needed)
                    # is respected if the singleton isn't in the _root_singletons cache yet.
                    # However, _parent_provider._create_instance(descriptor) is what was there.
                    # Let's refine to call parent's get_service if not in the passed cache.
                    # This assumes _root_singletons is the definitive cache passed down.
                    self._root_singletons[service_type] = self._parent_provider.get_service(service_type)
                return self._root_singletons[service_type]
            else: # TRANSIENT
                return self._create_instance(descriptor)
        finally:
            _current_resolving_stack.reset(token)

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
