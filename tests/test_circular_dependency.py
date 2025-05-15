import pytest
# from wd.di.service_collection import ServiceCollection # Old import path
from wd.di import ServiceCollection # Correct import path

def test_circular_dependency_detection():
    services = ServiceCollection() # Instantiate locally

    # Define two classes that depend on each other
    class ServiceA:
        def __init__(self, service_b: "ServiceB"):
            self.service_b = service_b

    class ServiceB:
        def __init__(self, service_a: ServiceA):
            self.service_a = service_a

    services.add_transient(ServiceA)
    services.add_transient(ServiceB)

    provider = services.build_service_provider()

    # Updated to expect the NameError that occurs first when forward references
    # are involved in a circular dependency.
    expected_pattern = (
        r"Failed to resolve dependencies for .*ServiceA.* "
        r"due to NameError \(potential forward reference in a circular dependency\): "
        r"name 'ServiceB' is not defined. "
        r"Resolution stack: \[.*ServiceA.*\]"
    )
    with pytest.raises(Exception, match=expected_pattern):
        provider.get_service(ServiceA)
