from enum import Enum


class ServiceLifetime(Enum):
    TRANSIENT = 1
    SINGLETON = 2
    SCOPED = 3
