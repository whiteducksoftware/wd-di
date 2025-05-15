import pytest

from wd.di import ServiceCollection, ServiceProvider
from wd.di.exceptions import CircularDecoratorError, InvalidOperationError

# --- Test Services ---

class IMessageHandler:
    def handle(self, message: str) -> str:
        raise NotImplementedError

class ConcreteMessageHandler(IMessageHandler):
    def handle(self, message: str) -> str:
        return f"ConcreteHandler: {message}"

# --- Decorator Factories ---

def UppercaseDecoratorFactory(sp: ServiceProvider, inner: IMessageHandler) -> IMessageHandler:
    return UppercaseDecorator(inner)

class UppercaseDecorator(IMessageHandler):
    def __init__(self, inner: IMessageHandler):
        self.inner = inner
    def handle(self, message: str) -> str:
        return self.inner.handle(message).upper()

def ExclamationDecoratorFactory(sp: ServiceProvider, inner: IMessageHandler) -> IMessageHandler:
    return ExclamationDecorator(inner)

class ExclamationDecorator(IMessageHandler):
    def __init__(self, inner: IMessageHandler):
        self.inner = inner
    def handle(self, message: str) -> str:
        return f"{self.inner.handle(message)}!"

def create_wrapping_decorator_factory(prefix: str, suffix: str):
    def factory(sp: ServiceProvider, inner: IMessageHandler) -> IMessageHandler:
        return WrappingDecorator(inner, prefix, suffix)
    return factory

class WrappingDecorator(IMessageHandler):
    def __init__(self, inner: IMessageHandler, prefix: str, suffix: str):
        self.inner = inner
        self.prefix = prefix
        self.suffix = suffix
    def handle(self, message: str) -> str:
        return f"{self.prefix}{self.inner.handle(message)}{self.suffix}"

# --- Tests ---

def test_single_decorator_applied():
    services = ServiceCollection()
    services.add_transient(IMessageHandler, ConcreteMessageHandler)
    services.decorate(IMessageHandler, UppercaseDecoratorFactory)
    
    provider = services.build_service_provider()
    handler = provider.get_service(IMessageHandler)
    
    result = handler.handle("hello")
    assert result == "CONCRETEHANDLER: HELLO"

def test_multiple_decorators_applied_in_order():
    services = ServiceCollection()
    services.add_transient(IMessageHandler, ConcreteMessageHandler)
    services.decorate(IMessageHandler, UppercaseDecoratorFactory)
    services.decorate(IMessageHandler, ExclamationDecoratorFactory)
    
    provider = services.build_service_provider()
    handler = provider.get_service(IMessageHandler)
    
    result = handler.handle("hello")
    assert result == "CONCRETEHANDLER: HELLO!"

def test_decorator_with_parameters_from_factory():
    services = ServiceCollection()
    services.add_transient(IMessageHandler, ConcreteMessageHandler)
    
    prefix_suffix_decorator_factory = create_wrapping_decorator_factory(prefix="[INFO] ", suffix=" ...done")
    services.decorate(IMessageHandler, prefix_suffix_decorator_factory)
    
    provider = services.build_service_provider()
    handler = provider.get_service(IMessageHandler)
    
    result = handler.handle("processing event")
    assert result == "[INFO] ConcreteHandler: processing event ...done"

def test_decorate_unregistered_service_raises_keyerror():
    services = ServiceCollection()
    with pytest.raises(KeyError, match=r"No service registered for IMessageHandler; cannot apply decorator\."):
        services.decorate(IMessageHandler, UppercaseDecoratorFactory)

def test_decorate_after_provider_built_raises_invalidoperationerror():
    services = ServiceCollection()
    services.add_transient(IMessageHandler, ConcreteMessageHandler)
    provider = services.build_service_provider()
    with pytest.raises(InvalidOperationError, match="Cannot modify ServiceCollection after ServiceProvider has been built."):
        services.decorate(IMessageHandler, UppercaseDecoratorFactory)

# --- Circular Decorator Detection Test ---

def _test_key(obj: object) -> str:
    if isinstance(obj, type):
        return obj.__qualname__
    if hasattr(obj, "__qualname__"):
        return obj.__qualname__
    if hasattr(obj, "__name__"):
        return obj.__name__
    return repr(obj)

def test_circular_decorator_dependency_detected():
    services = ServiceCollection()

    def recursive_decorator_factory(sp: ServiceProvider, inner: IMessageHandler) -> IMessageHandler:
        sp.get_service(IMessageHandler) 
        return inner

    services.add_transient(IMessageHandler, ConcreteMessageHandler)
    services.decorate(IMessageHandler, recursive_decorator_factory)

    provider = services.build_service_provider()

    with pytest.raises(CircularDecoratorError) as excinfo:
        provider.get_service(IMessageHandler)
    
    expected_deco_key_name = _test_key(recursive_decorator_factory)
    assert expected_deco_key_name in str(excinfo.value)
    assert "Circular decorator chain detected" in str(excinfo.value) 