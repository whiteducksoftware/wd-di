from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TypeVar, Generic, Type
from dataclasses import dataclass
import json
import os

T = TypeVar("T")


class IConfiguration(ABC):
    @abstractmethod
    def get(self, key: str) -> Any:
        pass

    @abstractmethod
    def get_section(self, section: str) -> "IConfiguration":
        pass


class Configuration(IConfiguration):
    def __init__(self, data: Dict[str, Any]):
        self._data = data

    def get(self, key: str) -> Any:
        keys = key.split(":")
        current = self._data
        for k in keys:
            if not isinstance(current, dict) or k not in current:
                return None
            current = current[k]
        return current

    def get_section(self, section: str) -> "IConfiguration":
        value = self.get(section)
        if isinstance(value, dict):
            return Configuration(value)
        return Configuration({})


class ConfigurationBuilder:
    def __init__(self):
        self._sources: Dict[str, Any] = {}

    def add_json_file(self, path: str) -> "ConfigurationBuilder":
        if os.path.exists(path):
            with open(path, "r") as f:
                self._sources.update(json.load(f))
        return self

    def add_env_variables(self, prefix: str = "") -> "ConfigurationBuilder":
        for key, value in os.environ.items():
            if prefix and not key.startswith(prefix):
                continue
            if prefix:
                key = key[len(prefix) :]
            self._sources[key] = value
        return self

    def add_dictionary(self, dictionary: Dict[str, Any]) -> "ConfigurationBuilder":
        self._sources.update(dictionary)
        return self

    def build(self) -> IConfiguration:
        return Configuration(self._sources)


@dataclass
class ConfigureOptions:
    section: str


class Options(Generic[T]):
    def __init__(self, value: T):
        self._value = value

    @property
    def value(self) -> T:
        return self._value


class OptionsBuilder(Generic[T]):
    def __init__(self, options_type: Type[T]):
        self._options_type = options_type
        self._configuration: Optional[IConfiguration] = None
        self._section: Optional[str] = None

    def bind_configuration(
        self, configuration: IConfiguration, section: Optional[str] = None
    ) -> "OptionsBuilder[T]":
        self._configuration = configuration
        self._section = section
        return self

    def build(self) -> T:
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
