import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Generic, Optional, Type, TypeVar

T = TypeVar("T")


class IConfiguration(ABC):
    """Defines the contract for application configuration.

    This interface provides a way to access configuration values, typically
    key-value pairs, and to retrieve specific sections of the configuration
    as new [IConfiguration][wd.di.config.IConfiguration] instances.
    """
    @abstractmethod
    def get(self, key: str) -> any:
        """Gets a configuration value by key.

        Args:
            key: The key of the configuration value. Keys can be hierarchical,
                often separated by a colon (e.g., "Parent:Child:Value").

        Returns:
            The configuration value if found, otherwise None or a type-specific
            default if the implementation supports it.
        """

    @abstractmethod
    def get_section(self, section: str) -> "IConfiguration":
        """Gets a configuration subsection.

        Args:
            section: The key of the configuration section.

        Returns:
            An [IConfiguration][wd.di.config.IConfiguration] instance representing the specified section.
            If the section does not exist, it might return an empty configuration
            or raise an error, depending on the implementation.
        """


class Configuration(IConfiguration):
    """A basic dictionary-backed implementation of [IConfiguration][wd.di.config.IConfiguration].

    This class holds configuration data in a dictionary and provides methods
    to access values and sections based on string keys.

    Attributes:
        _data (Dict[str, Any]): The underlying dictionary holding configuration data.
    """
    def __init__(self, data: dict[str, any]):
        """Initializes a new Configuration instance.

        Args:
            data: A dictionary containing the configuration data.
        """
        self._data = data

    def get(self, key: str) -> any:
        """Retrieves a configuration value for the given key.

        Keys can be hierarchical, separated by colons (e.g., "Logging:LogLevel:Default").

        Args:
            key: The configuration key.

        Returns:
            The value associated with the key if found; otherwise, `None`.
        """
        keys = key.split(":")
        current = self._data
        for k in keys:
            if not isinstance(current, dict) or k not in current:
                return None
            current = current[k]
        return current

    def get_section(self, section: str) -> "IConfiguration":
        """Retrieves a subsection of the configuration.

        Args:
            section: The key of the section to retrieve.

        Returns:
            A new [Configuration][wd.di.config.Configuration] instance representing the requested section.
            If the section key does not point to a dictionary, an empty
            [Configuration][wd.di.config.Configuration] is returned.
        """
        value = self.get(section)
        if isinstance(value, dict):
            return Configuration(value)
        return Configuration({})


class ConfigurationBuilder:
    """Builds an [IConfiguration][wd.di.config.IConfiguration] object from various sources.

    This builder allows for a layered configuration approach, where configuration
    data can be loaded from JSON files, environment variables, and dictionaries.
    Later sources can override values from earlier ones.

    Attributes:
        _sources (Dict[str, Any]): A dictionary accumulating configuration data
            from all added sources.
    """
    def __init__(self):
        """Initializes a new ConfigurationBuilder."""
        self._sources: dict[str, any] = {}

    def add_json_file(self, path: str) -> "ConfigurationBuilder":
        """Adds configuration values from a JSON file.

        If the file at the specified path exists, it is read, parsed as JSON,
        and its contents are merged into the builder's sources.

        Args:
            path: The file system path to the JSON configuration file.

        Returns:
            The [ConfigurationBuilder][wd.di.config.ConfigurationBuilder] instance for fluent chaining.
        """
        if Path.exists(path):
            with open(path, "r") as f:
                self._sources.update(json.load(f))
        return self

    def add_env_variables(self, prefix: str = "") -> "ConfigurationBuilder":
        """Adds configuration values from environment variables.

        Args:
            prefix: An optional prefix. If provided, only environment variables
                starting with this prefix will be added. The prefix itself will be
                removed from the key used in the configuration.

        Returns:
            The [ConfigurationBuilder][wd.di.config.ConfigurationBuilder] instance for fluent chaining.
        """
        for key, value in os.environ.items():
            if prefix and not key.startswith(prefix):
                continue
            config_key = key
            if prefix:
                config_key = key[len(prefix) :]
            self._sources[config_key] = value
        return self

    def add_dictionary(self, dictionary: Dict[str, Any]) -> "ConfigurationBuilder":
        """Adds configuration values from a dictionary.

        The provided dictionary's key-value pairs are merged into the builder's sources.

        Args:
            dictionary: A dictionary containing configuration key-value pairs.

        Returns:
            The [ConfigurationBuilder][wd.di.config.ConfigurationBuilder] instance for fluent chaining.
        """
        self._sources.update(dictionary)
        return self

    def build(self) -> IConfiguration:
        """Builds the [IConfiguration][wd.di.config.IConfiguration] instance.

        Combines all added sources into a single [Configuration][wd.di.config.Configuration] object.

        Returns:
            An [IConfiguration][wd.di.config.IConfiguration] instance containing the merged configuration data.
        """
        return Configuration(self._sources)


@dataclass
class ConfigureOptions:
    """Data class for options related to configuration binding.

    Note: This class seems to be defined but not actively used within the provided
    `config.py` snippet for binding options. Its intended purpose might be for
    more advanced configuration scenarios or future enhancements.

    Attributes:
        section (str): The configuration section name.
    """
    section: str


class Options(Generic[T]):
    """A wrapper class for strongly-typed configuration options.

    This class is used to provide access to instances of configuration option
    objects that have been populated from an [IConfiguration][wd.di.config.IConfiguration] source.

    Attributes:
        _value (T): The underlying options instance.

    Generics:
        T: The type of the options class being wrapped.
    """
    def __init__(self, value: T):
        """Initializes a new Options instance.

        Args:
            value: The instance of the options class.
        """
        self._value = value

    @property
    def value(self) -> T:
        """Gets the underlying options instance."""
        return self._value


class OptionsBuilder(Generic[T]):
    """Builds an instance of a strongly-typed options class from configuration data.

    This builder is used by the `ServiceCollection.configure` method to create
    and populate options objects.

    Attributes:
        _options_type (Type[T]): The type of the options class to build.
        _configuration (Optional[[IConfiguration][wd.di.config.IConfiguration]]): The configuration source.
        _section (Optional[str]): The specific section of the configuration to bind from.

    Generics:
        T: The type of the options class to be built.
    """
    def __init__(self, options_type: Type[T]):
        """Initializes a new OptionsBuilder.

        Args:
            options_type: The class type of the options to be built.
        """
        self._options_type = options_type
        self._configuration: Optional[IConfiguration] = None
        self._section: Optional[str] = None

    def bind_configuration(
        self, configuration: IConfiguration, section: Optional[str] = None
    ) -> "OptionsBuilder[T]":
        """Binds the builder to a specific configuration source and section.

        Args:
            configuration: The [IConfiguration][wd.di.config.IConfiguration] source to use for binding.
            section: Optional. The name of the configuration section to bind from.
                If `None`, the root of the configuration is used or a section
                name might be inferred from `_options_type`.

        Returns:
            The [OptionsBuilder][wd.di.config.OptionsBuilder] instance for fluent chaining.
        """
        self._configuration = configuration
        self._section = section
        return self

    def build(self) -> T:
        """Builds and populates the options instance.

        If no configuration is bound, an empty instance of `_options_type` is returned.
        Otherwise, it attempts to populate an instance of `_options_type` using values
        from the bound [IConfiguration][wd.di.config.IConfiguration] (and section, if specified).
        It handles mapping of camelCase configuration keys to snake_case attribute names.

        Returns:
            An instance of the options class `T`, populated with values from the
            configuration if available.
        """
        if self._configuration is None:
            return self._options_type()

        config_section = self._configuration
        if self._section:
            config_section = self._configuration.get_section(self._section)

        instance = self._options_type()
        config_dict = {}

        if hasattr(config_section, "_data"):
            config_dict = config_section._data

        # Convert camelCase to snake_case for property names
        for key, value in config_dict.items():
            snake_key = "".join(
                ["_" + c.lower() if c.isupper() else c for c in key]
            ).lstrip("_")
            if hasattr(instance, snake_key):
                setattr(instance, snake_key, value)

        return instance
