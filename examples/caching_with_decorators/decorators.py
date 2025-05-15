# examples/caching_with_decorators/decorators.py
import time
from typing import Dict, Tuple
from wd.di import ServiceProvider # Assuming ServiceProvider is available for type hinting
from services import IExternalWeatherService

class CachingWeatherServiceDecorator(IExternalWeatherService):
    def __init__(self, inner: IExternalWeatherService, cache_duration_seconds: int = 60):
        self._inner = inner
        self._cache: Dict[str, Tuple[float, float]] = {} # Key: city, Value: (timestamp, temperature)
        self._cache_duration = cache_duration_seconds
        print(f"[CachingWeatherServiceDecorator] Initialized with cache duration: {self._cache_duration}s")

    def get_current_temperature(self, city: str) -> float:
        city_key = city.lower()
        current_time = time.time()

        if city_key in self._cache:
            timestamp, temperature = self._cache[city_key]
            if current_time - timestamp < self._cache_duration:
                print(f"[CachingWeatherServiceDecorator] Cache HIT for {city}. Temp: {temperature}°C")
                return temperature
            else:
                print(f"[CachingWeatherServiceDecorator] Cache STALE for {city}. Re-fetching...")
        else:
            print(f"[CachingWeatherServiceDecorator] Cache MISS for {city}. Fetching from real service...")

        # Cache miss or stale, fetch from inner service
        temperature = self._inner.get_current_temperature(city)
        self._cache[city_key] = (current_time, temperature)
        print(f"[CachingWeatherServiceDecorator] Cached new temperature for {city}: {temperature}°C")
        return temperature

    def clear_cache(self):
        self._cache.clear()
        print("[CachingWeatherServiceDecorator] Cache cleared.")

# Decorator Factory that creates the CachingWeatherServiceDecorator
def create_caching_weather_decorator_factory(cache_duration_seconds: int = 60):
    print(f"[Factory] Creating caching decorator factory with duration: {cache_duration_seconds}s")
    def actual_factory(provider: ServiceProvider, inner: IExternalWeatherService) -> IExternalWeatherService:
        # `provider` is available if the decorator itself needed other services, not used in this simple cache.
        return CachingWeatherServiceDecorator(inner, cache_duration_seconds)
    return actual_factory 