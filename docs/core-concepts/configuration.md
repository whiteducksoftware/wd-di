# Configuration and Options Pattern

WD-DI includes a robust configuration system inspired by .NET's Options pattern. This allows you to bind configuration data (from dictionaries, JSON files, environment variables, etc., though currently focused on dictionary sources) to strongly-typed Python dataclasses. This approach centralizes configuration logic, provides type safety, and makes configuration access clean and maintainable.

---

## Key Components

*   **`IConfiguration`:** An interface (and its concrete implementation `Configuration`) that represents your application's configuration. It can load data from a dictionary and provides methods to access configuration sections.
*   **`Options[T]`:** A generic wrapper class. When you request `Options[MyConfigClass]`, WD-DI provides an instance of `Options` whose `value` attribute holds a populated instance of `MyConfigClass`.
*   **`services.configure(ConfigClass, section_name)`:** A method on `ServiceCollection` used to bind a section of your application's configuration (retrieved from `IConfiguration`) to a specific dataclass (`ConfigClass`).

---

## How It Works

1.  **Define an Options Dataclass:** Create a Python dataclass that represents the structure of a particular configuration section.
    ```python
    from dataclasses import dataclass

    @dataclass
    class DatabaseOptions:
        connection_string: str = ""
        max_connections: int = 10
        timeout: int = 30
    ```
2.  **Provide Configuration Data:** Create a configuration source. Typically, this is a dictionary, which could be loaded from a JSON file, environment variables, or constructed in code.
    ```python
    config_data = {
        "Database": {  # Section name (case-insensitive by default in GetSection)
            "ConnectionString": "your_db_connection_string",
            "MaxConnections": 50
            # Timeout will use the default from DatabaseOptions (30)
        },
        "Logging": {
            "Level": "Information"
        }
    }
    ```
3.  **Register `IConfiguration`:** Add your configuration object (an instance of `Configuration` or your custom `IConfiguration` implementation) to the service collection, usually as a singleton.
    ```python
    from wd.di import create_service_collection
    from wd.di.config import Configuration, IConfiguration

    sc = create_service_collection()
    app_config = Configuration(config_data)
    sc.add_singleton_factory(IConfiguration, lambda _: app_config)
    ```
4.  **Bind Configuration to Options:** Use `sc.configure()` to tell WD-DI how to map a configuration section to your options dataclass.
    ```python
    sc.configure(DatabaseOptions, section="Database")
    ```
    This tells WD-DI: "When `Options[DatabaseOptions]` is requested, find the 'Database' section in `IConfiguration`, create an instance of `DatabaseOptions`, and populate it with data from that section (automatically converting PascalCase/camelCase keys from config to snake_case attributes in the dataclass)."
5.  **Inject `Options[T]` into Services:** In your services, depend on `Options[YourConfigClass]` to access the configured values.
    ```python
    from wd.di.config import Options

    @sc.singleton()
    class DatabaseService:
        def __init__(self, db_options: Options[DatabaseOptions]):
            self.options = db_options.value # Access the populated dataclass instance
            print(f"DB Connection: {self.options.connection_string}")
            print(f"DB Max Connections: {self.options.max_connections}")
            print(f"DB Timeout: {self.options.timeout}") # Will be 30 (default)

    # --- Usage ---
    provider = sc.build_service_provider()
    db_service = provider.get_service(DatabaseService)
    # Expected Output:
    # DB Connection: your_db_connection_string
    # DB Max Connections: 50
    # DB Timeout: 30
    ```

---

## Benefits of the Options Pattern

*   **Strong Typing:** Configuration is accessed via dataclasses, providing attribute access and type checking (if using static analysis). This reduces errors caused by typos in string-based dictionary lookups.
*   **Centralization:** Configuration logic is defined in one place (your options dataclasses and the `configure` calls).
*   **Decoupling:** Services depend on `Options[T]` rather than directly on `IConfiguration` or concrete configuration sources. This makes services more testable, as you can easily provide mock `Options` in tests.
*   **Default Values:** Dataclasses allow you to specify default values for configuration properties, simplifying setup for common scenarios.
*   **Clear Structure:** Configuration is organized into logical sections represented by different options classes.

---

## When to Use

*   For any application settings that might vary between environments (development, staging, production) or need to be managed externally.
*   When you want to provide type-safe access to configuration values within your services.
*   To keep your services decoupled from the specifics of how configuration is loaded and stored.

The Options pattern is a powerful tool for managing application settings in a clean, robust, and maintainable way.
