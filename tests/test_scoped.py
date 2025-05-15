import pytest
# from wd.di.service_collection import ServiceCollection # Old import path
from wd.di import ServiceCollection # Correct import path

def test_scoped_service_from_root_fails():
    services = ServiceCollection() # Instantiate locally
    # Define a simple scoped service.
    class ScopedService:
        pass

    services.add_scoped(ScopedService)
    provider = services.build_service_provider()

    # Attempting to resolve a scoped service directly from the root provider should fail.
    with pytest.raises(Exception, match="Cannot resolve scoped service from the root provider"):
        provider.get_service(ScopedService)

def test_scoped_service_same_instance_in_scope():
    services = ServiceCollection() # Instantiate locally
    # Define a simple scoped service.
    class ScopedService:
        pass

    services.add_scoped(ScopedService)
    provider = services.build_service_provider()

    # Within the same scope, multiple resolutions should yield the same instance.
    with provider.create_scope() as scope:
        instance1 = scope.get_service(ScopedService)
        instance2 = scope.get_service(ScopedService)
        assert instance1 is instance2

def test_scoped_service_different_instances_in_different_scopes():
    services = ServiceCollection() # Instantiate locally
    # Define a simple scoped service.
    class ScopedService:
        pass

    services.add_scoped(ScopedService)
    provider = services.build_service_provider()

    # Different scopes should produce different instances.
    with provider.create_scope() as scope1:
        instance1 = scope1.get_service(ScopedService)
    with provider.create_scope() as scope2:
        instance2 = scope2.get_service(ScopedService)
    assert instance1 is not instance2

def test_disposable_service_is_disposed():
    services = ServiceCollection() # Instantiate locally
    # Define a disposable service that implements a dispose method.
    class DisposableService:
        def __init__(self):
            self.is_disposed = False

        def dispose(self):
            self.is_disposed = True

    services.add_scoped(DisposableService)
    provider = services.build_service_provider()
    disposable_instance = None

    # Within the scope, the instance is not disposed.
    with provider.create_scope() as scope:
        disposable_instance = scope.get_service(DisposableService)
        assert not disposable_instance.is_disposed

    # Exiting the scope should trigger disposal.
    assert disposable_instance.is_disposed

def test_close_method_is_called_for_disposable():
    services = ServiceCollection() # Instantiate locally
    # Define a disposable service that uses a close method.
    class DisposableService:
        def __init__(self):
            self.is_closed = False

        def close(self):
            self.is_closed = True

    services.add_scoped(DisposableService)
    provider = services.build_service_provider()
    disposable_instance = None

    # Within the scope, the instance is not closed.
    with provider.create_scope() as scope:
        disposable_instance = scope.get_service(DisposableService)
        assert not disposable_instance.is_closed

    # Exiting the scope should trigger the close method.
    assert disposable_instance.is_closed
