"""
Ensures that ServiceCollection.add_instance registers an already
constructed object exactly once and that the very *same* object is
returned from any provider or scope.
"""

from wd.di import ServiceCollection

class Logger:
    def __init__(self):
        self.lines = []

    def log(self, msg: str) -> None:
        self.lines.append(msg)

def test_add_instance_returns_same_object_everywhere():
    services = ServiceCollection()

    logger = Logger()
    services.add_instance(Logger, logger)

    provider = services.build_service_provider()

    # root access
    assert provider.get_service(Logger) is logger

    # scoped access – must still be the very same object
    with provider.create_scope() as scope:
        assert scope.get_service(Logger) is logger

    # sanity: logger is functional
    logger.log("hello")
    assert logger.lines == ["hello"]
