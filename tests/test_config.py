import pytest
from dataclasses import dataclass
from wd.di.config import (
    Configuration,
    ConfigurationBuilder,
    Options,
    OptionsBuilder,
    IConfiguration,
)
from wd.di import ServiceCollection


@dataclass
class DatabaseOptions:
    connection_string: str = ""
    max_connections: int = 10


@dataclass
class AppSettings:
    name: str = ""
    version: str = ""


def test_configuration_get():
    config = Configuration(
        {
            "database": {
                "connectionString": "test-connection",
                "maxConnections": 5,
            },
            "app": {"name": "TestApp", "version": "1.0.0"},
        }
    )

    assert config.get("database:connectionString") == "test-connection"
    assert config.get("app:name") == "TestApp"
    assert config.get("nonexistent") is None
    assert config.get("database:nonexistent") is None


def test_configuration_get_section():
    config = Configuration(
        {
            "database": {
                "connectionString": "test-connection",
                "maxConnections": 5,
            }
        }
    )

    section = config.get_section("database")
    assert section.get("connectionString") == "test-connection"
    assert section.get("maxConnections") == 5


def test_configuration_builder():
    builder = ConfigurationBuilder()
    config = (
        builder.add_dictionary(
            {
                "database": {
                    "connectionString": "test-connection",
                    "maxConnections": 5,
                }
            }
        )
        .add_dictionary({"app": {"name": "TestApp"}})
        .build()
    )

    assert config.get("database:connectionString") == "test-connection"
    assert config.get("app:name") == "TestApp"


def test_options_builder():
    config = Configuration(
        {"database": {"connectionString": "test-connection", "maxConnections": 5}}
    )

    builder = OptionsBuilder(DatabaseOptions)
    options = builder.bind_configuration(config, "database").build()

    assert options.connection_string == "test-connection"
    assert options.max_connections == 5


def test_options_di_integration():
    services = ServiceCollection()

    config = Configuration(
        {
            "database": {"connectionString": "test-connection", "maxConnections": 5},
            "app": {"name": "TestApp", "version": "1.0.0"},
        }
    )

    services.add_singleton_factory(IConfiguration, lambda sp: config)
    services.configure(DatabaseOptions, section="database")
    services.configure(AppSettings, section="app")

    provider = services.build_service_provider()

    db_options = provider.get_service(Options[DatabaseOptions])
    app_options = provider.get_service(Options[AppSettings])

    assert db_options.value.connection_string == "test-connection"
    assert db_options.value.max_connections == 5
    assert app_options.value.name == "TestApp"
    assert app_options.value.version == "1.0.0"


def test_options_without_configuration():
    services = ServiceCollection()

    services.configure(DatabaseOptions)
    provider = services.build_service_provider()

    with pytest.raises(Exception, match="Configuration service not registered"):
        provider.get_service(Options[DatabaseOptions])


def test_options_missing_section():
    services = ServiceCollection()

    config = Configuration({})
    services.add_singleton_factory(IConfiguration, lambda sp: config)
    services.configure(DatabaseOptions, section="database")
    provider = services.build_service_provider()

    db_options = provider.get_service(Options[DatabaseOptions])
    assert db_options.value.connection_string == ""
    assert db_options.value.max_connections == 10
