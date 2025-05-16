from enum import Enum


class ServiceLifetime(Enum):
    """Specifies the lifetime of a service in a [ServiceCollection][wd.di.service_collection.ServiceCollection].

    The lifetime determines how a service instance is created and managed by the
    [ServiceProvider][wd.di.container.ServiceProvider].

    Attributes:
        TRANSIENT: A new instance of the service is created each time it is requested.
        SINGLETON: A single instance of the service is created once and reused for all
            subsequent requests across all scopes and the root container.
        SCOPED: A new instance of the service is created once per scope. Within the
            same scope, the same instance is reused.
    """
    TRANSIENT = 1
    SINGLETON = 2
    SCOPED = 3
