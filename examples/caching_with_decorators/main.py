# examples/caching_with_decorators/main.py
import time
from wd.di import ServiceCollection
from .services import IExternalWeatherService, SlowExternalWeatherService
from .decorators import create_caching_weather_decorator_factory

def main():
    print("--- Caching Decorator Example ---")

    services = ServiceCollection()

    # Register the slow weather service
    services.add_singleton(IExternalWeatherService, SlowExternalWeatherService)

    # Create a caching decorator factory with a short cache duration for demo purposes
    caching_factory = create_caching_weather_decorator_factory(cache_duration_seconds=5)
    
    # Decorate the weather service with the caching layer
    services.decorate(IExternalWeatherService, caching_factory)

    provider = services.build_service_provider()

    weather_service = provider.get_service(IExternalWeatherService)
    slow_weather_service_instance = provider.get_service(SlowExternalWeatherService) # Get direct instance for call count

    print("\n--- First call for London (should be slow and cache miss) ---")
    temp_london1 = weather_service.get_current_temperature("London")
    print(f"Reported temperature for London: {temp_london1}°C")
    print(f"API call count: {slow_weather_service_instance.get_api_call_count()}") # type: ignore

    print("\n--- Second call for London (should be fast from cache) ---")
    temp_london2 = weather_service.get_current_temperature("London")
    print(f"Reported temperature for London: {temp_london2}°C")
    print(f"API call count: {slow_weather_service_instance.get_api_call_count()}") # type: ignore

    print("\n--- First call for New York (should be slow and cache miss) ---")
    temp_ny1 = weather_service.get_current_temperature("New York")
    print(f"Reported temperature for New York: {temp_ny1}°C")
    print(f"API call count: {slow_weather_service_instance.get_api_call_count()}") # type: ignore

    print(f"\n--- Waiting for {7} seconds to ensure London cache expires... ---")
    time.sleep(7)

    print("\n--- Third call for London (should be slow again due to cache expiry) ---")
    temp_london3 = weather_service.get_current_temperature("London")
    print(f"Reported temperature for London: {temp_london3}°C")
    print(f"API call count: {slow_weather_service_instance.get_api_call_count()}") # type: ignore

    print("\n--- Second call for New York (should still be fast from cache) ---")
    temp_ny2 = weather_service.get_current_temperature("New York") # NY cache (5s) might be stale or not depending on timing
    print(f"Reported temperature for New York: {temp_ny2}°C")
    print(f"API call count: {slow_weather_service_instance.get_api_call_count()}") # type: ignore

    print("\n--- Example Complete ---")

if __name__ == "__main__":
    main() 