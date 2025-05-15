from wd.di import ServiceCollection

services = ServiceCollection()

@services.transient()
class FooService:
    def do_something(self):
        print("FooService doing something!")


@services.singleton()
class BarService:
    def __init__(self, foo_service: FooService):
        self.foo_service = foo_service

    def do_something_else(self):
        print("BarService doing something else!")
        self.foo_service.do_something()


def test_decorators():
    service_provider = services.build_service_provider()
    bar_service = service_provider.get_service(BarService)
    bar_service.do_something_else()

    assert bar_service is not None
