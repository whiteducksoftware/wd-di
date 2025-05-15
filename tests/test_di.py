# tests/test_di.py

from typing import assert_type
# from wd.di.service_collection import ServiceCollection # Old import path
from wd.di import ServiceCollection # Correct import path


# Define test services - these are fine at module level
class IService:
    def execute(self):
        pass


class ServiceA(IService):
    def execute(self):
        return "ServiceA"


class ServiceB(IService):
    def __init__(self, service_a: ServiceA):
        self.service_a = service_a

    def execute(self):
        return f"ServiceB depends on {self.service_a.execute()}"


def test_transient_services():
    services = ServiceCollection() # Instantiate locally
    services.add_transient(ServiceA)
    services.add_transient(IService, ServiceB)

    provider = services.build_service_provider()
    service1 = provider.get_service(IService)
    service2 = provider.get_service(IService)

    assert service1 is not service2
    assert service1.execute() == "ServiceB depends on ServiceA"


def test_singleton_services():
    services = ServiceCollection() # Instantiate locally
    services.add_singleton(ServiceA)
    services.add_singleton(IService, ServiceB)

    provider = services.build_service_provider()
    service1 = provider.get_service(IService)
    service2 = provider.get_service(IService)


    assert_type(service1, IService)
    assert service1 is service2
    assert isinstance(service1, IService) and isinstance(service1, ServiceB)
    assert isinstance(service1, IService) and not isinstance(service1, ServiceA)