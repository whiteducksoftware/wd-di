# Configuration API

This document describes the classes and interfaces related to configuration management from `wd.di.config`.

```python
from wd.di.config import (
    IConfiguration,
    Configuration,
    ConfigurationBuilder,
    Options,
    # OptionsBuilder is typically used internally by ServiceCollection.configure
)
```

## `IConfiguration`

An abstract base class defining the interface for accessing configuration values.

```python
class IConfiguration(ABC):
    @abstractmethod
    def get(self, key: str) -> Any:
        pass

    @abstractmethod
    def get_section(self, section: str) -> "IConfiguration":
        pass
```

- **`get(key: str) -> Any`**: Retrieves a configuration value by its key. Keys can be colon-separated to access nested values (e.g., `"parent:child"`). Returns `None` if the key is not found.
- **`get_section(section: str) -> "IConfiguration"`**: Retrieves a subsection of the configuration as a new `IConfiguration` instance. If the section does not exist or is not a dictionary-like structure, an empty `Configuration` object is returned.

## `Configuration`

A concrete implementation of `IConfiguration` that holds configuration data in a dictionary.

### Initialization

```python
config_data = {"setting1": "value1", "nested": {"setting2": 123}}
config = Configuration(config_data)
```
- `data: Dict[str, Any]`: The dictionary containing the configuration data.

### Methods

Implements `get(key: str)` and `get_section(section: str)` as defined in `IConfiguration`.

## `ConfigurationBuilder`

Provides a way to build an `IConfiguration` object from various sources.

### Initialization

```python
builder = ConfigurationBuilder()
```

### Methods

- **`add_json_file(path: str) -> "ConfigurationBuilder"`**
  Adds configuration data from a JSON file. If the file does not exist, it's skipped.
  - `path`: The path to the JSON file.
  - Returns the `ConfigurationBuilder` instance for chaining.

- **`add_env_variables(prefix: str = "") -> "ConfigurationBuilder"`**
  Adds configuration data from environment variables.
  - `prefix` (optional): If provided, only environment variables starting with this prefix are added (the prefix is stripped from the key).
  - Returns the `ConfigurationBuilder` instance for chaining.

- **`add_dictionary(dictionary: Dict[str, Any]) -> "ConfigurationBuilder"`**
  Adds configuration data from a Python dictionary.
  - `dictionary`: The dictionary containing configuration key-value pairs.
  - Returns the `ConfigurationBuilder` instance for chaining.

- **`build() -> IConfiguration`**
  Builds the `IConfiguration` object from all added sources. Later sources override earlier ones if keys conflict.
  - Returns: An `IConfiguration` instance (specifically, a `Configuration` object).

## `Options[T]`

A generic wrapper class used to provide strongly-typed access to configuration options.
Instances of `Options[MyOptionsClass]` are typically registered and resolved from the DI container via `ServiceCollection.configure()`.

### Initialization

Usually done by the DI system.

```python
class Options(Generic[T]):
    def __init__(self, value: T):
        self._value = value
```
- `value: T`: The instance of the strongly-typed options class.

### Properties

- **`value: T`** (read-only property)
  Returns the underlying instance of the strongly-typed options class.

  Example usage after resolving from DI:
  ```python
  # Assuming MySettings is a class and Options[MySettings] is registered
  my_settings_options = provider.get_service(Options[MySettings])
  actual_settings = my_settings_options.value
  print(actual_settings.some_property)
  ```

## `OptionsBuilder[T]` (Internal Usage)

This class is primarily used internally by `ServiceCollection.configure()` to create and bind options objects. It's generally not directly instantiated by users.

- **`__init__(self, options_type: Type[T])`**
- **`bind_configuration(configuration: IConfiguration, section: Optional[str] = None) -> "OptionsBuilder[T]"`**
- **`build() -> T`**: Creates an instance of `options_type` and populates its fields from the bound configuration section. It attempts to match camelCase configuration keys to snake_case attributes on the `options_type` instance. 