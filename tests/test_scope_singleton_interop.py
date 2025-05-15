"""
Verifies that resolving a root-level singleton from inside a scope
*does not* trip the circular-dependency guard and that the singleton is
shared across scopes.
"""

from wd.di import ServiceCollection
from wd.di.config import Configuration, IConfiguration

# ── Sample services -------------------------------------------------

class RootSingleton:
    def __init__(self):
        self.counter = 0

class ScopedWorker:
    def __init__(self, singleton: RootSingleton):
        # Touch the singleton to prove we can use it
        singleton.counter += 1
        self.singleton = singleton

# ── Test ------------------------------------------------------------

def test_singleton_resolved_from_scope_without_cycle():
    services = ServiceCollection()
    # root singleton comes from normal registration
    services.add_singleton(RootSingleton)
    # register scoped worker that *depends on* the singleton
    services.add_scoped(ScopedWorker)

    provider = services.build_service_provider()

    # Use two independent scopes
    for _ in range(2):
        with provider.create_scope() as scope:
            worker = scope.get_service(ScopedWorker)
            assert isinstance(worker, ScopedWorker)
            # each scope sees the *same* singleton object
            assert worker.singleton is provider.get_service(RootSingleton)

    # singleton's counter was incremented twice (once per scope)
    assert provider.get_service(RootSingleton).counter == 2
