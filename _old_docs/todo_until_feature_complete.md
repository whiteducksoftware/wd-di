Here's the updated todo list with the "Instance Registration" feature now marked as complete:

---

### Updated Todo List

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

## Other ideas/Personal ideas

(Assuming `from wd.di import ServiceCollection` and `services = ServiceCollection()` are defined for these conceptual snippets)

1. **Service Discovery and Assembly Scanning**
- Auto-registration of services based on decorators/attributes
- Scanning assemblies/modules for services marked for registration
- Convention-based registration (e.g., all classes ending with 'Service')

2. **Advanced Service Resolution**
```python
# Named/keyed services
services.add_singleton(IService, ServiceA, name="serviceA")
services.add_singleton(IService, ServiceB, name="serviceB")

# Enumerable resolution
@services.singleton() # Updated
class Processor:
    def __init__(self, handlers: List[IHandler]):  # Inject all IHandler implementations
        self.handlers = handlers

# Lazy resolution
@services.singleton() # Updated
class Service:
    def __init__(self, lazy_dep: Lazy[ExpensiveService]):
        self._dep = lazy_dep  # Only created when accessed
```

3. **Better Async Support**
```python
# Async service initialization
@services.singleton() # Updated
class AsyncService:
    @classmethod
    async def create(cls):
        # Async initialization logic
        return cls()

# Async disposal
@services.singleton() # Updated
class AsyncDisposable:
    async def dispose(self):
        # Async cleanup
        pass
```

4. **Enhanced Configuration**
```python
# Environment-specific configuration
# (ConfigurationBuilder usage is independent of global services)
config_builder = ConfigurationBuilder() # Assuming ConfigurationBuilder is imported
config = (config_builder
    .add_json_file("appsettings.json")
    .add_json_file(f"appsettings.{env}.json", optional=True)
    .add_env_variables()
    .build())

# Strongly-typed nested configuration
@dataclass
class DatabaseConfig:
    connection_string: str
    max_connections: int

@dataclass
class AppConfig:
    database: DatabaseConfig
    debug: bool
```

5. **Service Replacement and Decoration**
```python
# Replace existing registration
services.replace_singleton(IService, NewImplementation) # Assuming services is ServiceCollection

# Decorate existing service
services.decorate(IService, lambda service: LoggingDecorator(service)) # Assuming services is ServiceCollection
```

6. **Enhanced Validation**
```python
# Validate service registration
services.validate()  # Check for missing dependencies, circular references; Assuming services is ServiceCollection

# Validate scoped service usage
services.validate_scopes()  # Ensure scoped services aren't used in singletons; Assuming services is ServiceCollection
```

7. **Service Factory Support**
```python
# Factory for creating services with runtime parameters
@services.singleton() # Updated
class UserService:
    def __init__(self, connection_factory: Callable[[str], Connection]):
        self.connection_factory = connection_factory

services.add_singleton_factory(
    Connection, 
    lambda sp, connection_string: create_connection(connection_string)
)
```

8. **Diagnostics and Debugging**
```python
# Service resolution visualization
services.print_dependency_graph() # Assuming services is ServiceCollection

# Resolution metrics
services.get_metrics()  # Service creation times, counts, etc.; Assuming services is ServiceCollection
```

9. **Middleware Enhancements**
```python
# Ordered middleware
# (MiddlewareBuilder patterns are independent of global services, they use the passed ServiceCollection)
# builder.use_middleware(AuthMiddleware, order=1)
# builder.use_middleware(LoggingMiddleware, order=2)

# Conditional middleware
# builder.use_middleware_if(DebugMiddleware, lambda context: context.is_debug)
```

10. **Scope Features**
```python
# Named scopes
# (Provider usage is independent of global services)
# with provider.create_scope("request") as scope:
#    service = scope.get_service(MyService)

# Scope validation
# services.validate_scope_boundaries() # Assuming services is ServiceCollection

# Scope events
# scope.on_disposing(lambda: cleanup_resources())
```

11. **Extended Type Support**
```python
# Generic service support
services.add_singleton(Repository[User]) # Assuming services is ServiceCollection
services.add_singleton(Repository[Order]) # Assuming services is ServiceCollection

# Optional dependencies
def __init__(self, optional: Optional[IService] = None):
    self.service = optional
```

12. **Testing Utilities**
```python
# Mock service provider
# (This is a conceptual mock, not directly tied to the global services change)
# mock_provider = MockServiceProvider()
# mock_provider.setup(IService).returns(mock_service)

# Service collection snapshots
# snapshot = services.create_snapshot() # Assuming services is ServiceCollection
# Make changes
# services.restore_snapshot(snapshot) # Assuming services is ServiceCollection
