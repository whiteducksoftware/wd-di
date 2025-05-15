# WD-DI Library Roadmap

This document outlines the planned features and enhancements for the WD-DI library. It is based on the previous internal TODO list and will be updated as the project progresses.

---

### Planned Features and Enhancements

#### 1. Dependency Injection Container Enhancements

- [x] **Scoped Services Resolution & Scope Management**  
  *Explicit scope creation and disposal management for scoped services have been implemented.*

- [x] **Circular Dependency Detection**  
  *Detection of circular dependencies during resolution (with proper error messages) is now in place.*

- [ ] **Open Generic Types Support:**  
  Add the ability to register and resolve open generic types for generic service definitions.

- [x] **Instance Registration:**  
  *The `add_instance` API for registering pre-instantiated services has been implemented.*

- [ ] **Multiple Implementations / Named Services:**  
  Support multiple registrations for a single service type and allow resolution as collections.

- [ ] **Improved Constructor Injection:**  
  Enhance dependency resolution to handle default parameter values and cases with missing or ambiguous type annotations.

- [x] **Thread Safety Improvements:**  
  *Review and enhance the container to be thread-safe in multi-threaded environments.* (ContextVar for circular dependency stack implemented)

---

#### 2. Middleware Pipeline Enhancements

- [ ] **Exception Handling Integration:**  
  Integrate `ExceptionHandlerMiddleware` into the default pipeline configuration and add tests for graceful error handling.

- [ ] **Middleware Registration & Lifetime Management:**  
  Refine middleware registration to better manage middleware lifetimes and resolve dependencies within appropriate scopes.

- [ ] **Advanced Pipeline Configuration:**  
  Explore features like branching pipelines, conditional middleware execution, or pipeline termination.

---

#### 3. Options/Configuration Enhancements

- [ ] **Type Conversion and Validation:**  
  Improve the `OptionsBuilder` to support robust type conversion and integrate validation logic.

- [ ] **Dynamic Configuration Reloading:**  
  Optionally add support for reloading configuration when underlying sources (e.g., JSON or environment variables) change.

---

#### 4. Testing and Documentation

- [ ] **Expanded Test Coverage:**  
  Add tests for new and pending features (e.g., open generic types, multiple implementations).

- [ ] **Documentation and Code Comments:**  
  Enhance inline documentation, add usage examples, and update the README to guide users.

- [x] **Refactor Global State:**  
  *The global `services` instance has been removed. DI container setup now requires explicit `ServiceCollection` instantiation.*

---

#### 5. Additional Features

- [ ] **Integration with Python Logging:**  
  Replace default print statements in logging middleware with integration into Python's standard logging module.

- [ ] **Support for Async Service Factories:**  
  Investigate and add support for asynchronous factory methods for services requiring async initialization.

- [ ] **Dependency Injection Extensions:**  
  Create helper functions or decorators for common patterns (e.g., function injection, async injection) to extend the framework's usability.

---

## Future Ideas and Exploration

This section lists features and concepts that are under consideration for future development or as potential extensions to the library. These are not yet committed items but represent areas of interest.

(Note: Code snippets below are conceptual and assume `from wd.di import ServiceCollection` and `sc = create_service_collection()` are defined.)

1.  **Service Discovery and Assembly Scanning**
    *   Auto-registration of services based on decorators/attributes.
    *   Scanning assemblies/modules for services marked for registration.
    *   Convention-based registration (e.g., all classes ending with 'Service').

2.  **Advanced Service Resolution**
    *   **Named/Keyed Services:**
        ```python
        # sc.add_singleton(IService, ServiceA, name="serviceA")
        # sc.add_singleton(IService, ServiceB, name="serviceB")
        ```
    *   **Enumerable Resolution (Resolving all implementations of an interface):**
        ```python
        # @sc.singleton()
        # class Processor:
        #     def __init__(self, handlers: list[IHandler]): # Inject all IHandler implementations
        #         self.handlers = handlers
        ```
    *   **Lazy Resolution:**
        ```python
        # from wd.di import Lazy # Hypothetical Lazy type
        # @sc.singleton()
        # class Service:
        #     def __init__(self, lazy_dep: Lazy[ExpensiveService]):
        #         self._dep = lazy_dep  # ExpensiveService only created when self._dep.value is accessed
        ```

3.  **Enhanced Async Support**
    *   **Async Service Initialization/Factories:** (Covered in "Additional Features")
    *   **Async Disposal (`aclose` or `adispose`):** Support for services that need to perform asynchronous cleanup.
        ```python
        # @sc.scoped() # Or other lifetimes
        # class AsyncDisposableResource:
        #     async def setup(self):
        #         # async setup
        #         pass
        #     async def aclose(self): # Or async_dispose
        #         # async cleanup
        #         pass
        # # ServiceProvider scope would need to handle await scope.aclose()
        ```

4.  **Enhanced Configuration (beyond current `Options` pattern)**
    *   **Environment-Specific Configuration Files:** (Already conceptually manageable by how `Configuration` is built)
    *   **Binding to Nested Dataclasses:** (Already supported by current `Options` pattern and `Configuration` section binding)

5.  **Service Replacement and Decoration**
    *   **Replace Existing Registration:**
        ```python
        # sc.replace_singleton(IService, NewImplementation)
        ```
    *   **Decorate Existing Service:**
        ```python
        # sc.decorate(IService, lambda sp, service_instance: LoggingDecorator(service_instance, sp.get_service(ILogger)))
        ```

6.  **Enhanced Validation**
    *   **Startup Validation:** Extended checks during `build_service_provider()` for common issues.
        ```python
        # provider = sc.build_service_provider(validate_on_build=True) # Check for missing dependencies, certain circular refs
        ```
    *   **Scope Validation:** Ensure scoped services aren't inadvertently resolved by singletons in a problematic way.

7.  **Service Factory Enhancements**
    *   Support for factories that can take runtime parameters beyond just the `ServiceProvider`.
        ```python
        # # For services that need parameters not known at registration time
        # # This is more of an application-level factory pattern that DI can help construct.
        # sc.add_transient_factory(lambda sp, param1: MyServiceWithParams(sp.get_service(IDependency), param1))
        ```

8.  **Diagnostics and Debugging Tools**
    *   **Dependency Graph Visualization:** Tools or methods to inspect the resolved dependency tree.
    *   **Resolution Metrics:** Optional tracking of service creation times, instance counts, etc.

9.  **Middleware Enhancements (beyond current pipeline)**
    *   **Ordered Middleware:** (Already supported by registration order)
    *   **Conditional Middleware:** (Already possible by implementing logic within `invoke`)

10. **Scope Features**
    *   **Named Scopes:** (For scenarios requiring multiple distinct types of scopes)
    *   **Scope Events:** Callbacks for scope creation or disposal.

11. **Extended Type Support**
    *   **Generic Service Support:** (Covered in "Container Enhancements" - Open Generics)
    *   **Optional Dependencies:** Clear patterns for handling optional dependencies (e.g. `dep: IMyService | None = None`).

12. **Testing Utilities**
    *   **Test ServiceProvider/ServiceCollection Helpers:** Utilities to simplify mocking or overriding services in test environments.
        ```python
        # with sc.override_service(IMyService, MockMyService()):
        #    provider = sc.build_service_provider()
        #    # ... tests ...
        ``` 