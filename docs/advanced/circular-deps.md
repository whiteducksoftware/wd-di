# Circular Dependency Detection

Circular dependencies occur when two or more services depend on each other directly or indirectly, creating a loop that cannot be resolved. For example, Service A depends on Service B, and Service B depends on Service A. Such a situation can lead to infinite recursion during instantiation if not detected.

WD-DI is designed to detect and report these circular dependencies at runtime, preventing your application from crashing due to stack overflows or unresolvable states.

---

## How WD-DI Detects Circular Dependencies

WD-DI uses a `ContextVar` (a context-local variable, ensuring thread/task safety for asynchronous applications) to keep track of the set of services that are currently in the process of being resolved for a given request chain.

When you request a service from the `ServiceProvider` (or a `Scope`):
1.  Before attempting to create an instance of the requested service, WD-DI adds the service's unique key (usually its type or interface) to this `ContextVar` set.
2.  If the service has dependencies, WD-DI recursively attempts to resolve them.
3.  If, during this recursive resolution, WD-DI encounters a request for a service key that is already present in the `ContextVar` set for the current resolution path, it means a circular dependency has been detected.
4.  Once the service (and its dependencies) are successfully resolved, its key is removed from the `ContextVar` set for that path, allowing other independent resolutions of the same service type if needed (e.g., for transient services requested multiple times by different branches of a dependency graph).

This mechanism ensures that a circular loop is caught before it can cause an infinite instantiation loop.

---

## `CircularDependencyError`

When a circular dependency is detected, WD-DI raises a `wd.di.errors.CircularDependencyError`. This error typically includes a message indicating the service type that caused the cycle and often the chain of dependencies involved.

---

## Example of a Circular Dependency

Consider two services, `ServiceA` and `ServiceB`, that depend on each other:

```python
from wd.di import create_service_collection
from wd.di.errors import CircularDependencyError

sc = create_service_collection()

# Forward declaration for type hints if classes are in the same scope
class ServiceB: ...

@sc.singleton()
class ServiceA:
    def __init__(self, b: ServiceB): # ServiceA depends on ServiceB
        self.b = b
        print("ServiceA created")

@sc.singleton()
class ServiceB:
    def __init__(self, a: ServiceA): # ServiceB depends on ServiceA
        self.a = a
        print("ServiceB created")

# --- Attempt to resolve ---
provider = sc.build_service_provider()

try:
    # Requesting either ServiceA or ServiceB will trigger the error
    service_a = provider.get_service(ServiceA)
except CircularDependencyError as e:
    print(f"Caught expected error: {e}")
    # Example error message might be:
    # "Circular dependency detected while resolving type <class '__main__.ServiceA'>. Resolution path: {<class '__main__.ServiceA'>, <class '__main__.ServiceB'>}"

# Expected Output (simplified, actual message might vary slightly):
# Caught expected error: Circular dependency detected for service <class '__main__.ServiceA'>. Current resolution path: {<ServiceKey for ServiceA>, <ServiceKey for ServiceB>}
```

In this scenario:
1.  Resolving `ServiceA` requires `ServiceB`. `ServiceA` is added to the resolution stack.
2.  Resolving `ServiceB` (for `ServiceA`) requires `ServiceA`. `ServiceB` is added to the resolution stack.
3.  Attempting to resolve `ServiceA` (for `ServiceB`) finds `ServiceA` already in the resolution stack, triggering `CircularDependencyError`.

---

## Resolving Circular Dependencies

If you encounter a `CircularDependencyError`, it's a signal that your application's design has a problematic dependency loop. WD-DI does not provide mechanisms to "break" the cycle automatically (e.g., with lazy proxies for one of the dependencies) because circular dependencies often indicate a deeper architectural issue.

The recommended ways to resolve circular dependencies are:

1.  **Refactor your services:**
    *   **Interface Segregation:** Introduce an interface that one of the services can depend on, and have the other service implement it. This can sometimes break the direct cycle if the interface is more focused.
    *   **Mediator Pattern:** Introduce a third service (a mediator) that both services depend on. The original services then communicate through the mediator rather than directly.
    *   **Re-evaluate Responsibilities:** Often, a circular dependency suggests that one or both services are doing too much or that responsibilities are not clearly separated. Splitting services into smaller, more focused units can help.
2.  **Property/Method Injection (Use with Caution):**
    *   While constructor injection is preferred, you could, in some rare cases, break a cycle by having one service set a dependency on another via a property or method after both are constructed. This is generally not recommended as it makes dependencies less explicit and can lead to objects being in an incompletely initialized state. WD-DI focuses on constructor injection.
3.  **Eventual Consistency/Callbacks:**
    *   Instead of a direct synchronous dependency, one service might raise an event that the other service subscribes to, decoupling them.

The best approach is usually to refactor the dependencies to eliminate the circularity, leading to a cleaner and more understandable architecture. 