import pytest
from wd_di.service_collection import ServiceCollection

def test_circular_dependency_detection():
    # Define two classes that depend on each other
    class ServiceA:
        def __init__(self, service_b: "ServiceB"):
            self.service_b = service_b

    class ServiceB:
        def __init__(self, service_a: ServiceA):
            self.service_a = service_a

    services = ServiceCollection()
    services.add_transient(ServiceA)
    services.add_transient(ServiceB)

    provider = services.build_service_provider()

    with pytest.raises(Exception, match="Circular dependency detected"):
        provider.get_service(ServiceA)
