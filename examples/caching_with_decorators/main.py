# examples/caching_with_decorators/main.py
import time
import random
from wd.di import ServiceCollection
from services import IExternalWeatherService, SlowExternalWeatherService
from decorators import create_caching_weather_decorator_factory
from console_utils import Colors # Import Colors from the new utility file

def main():
    print(Colors.format("--- Caching Decorator Example ---", bold=True))

    services = ServiceCollection()

    actual_slow_service = SlowExternalWeatherService()
    services.add_instance(SlowExternalWeatherService, actual_slow_service)
    services.add_instance(IExternalWeatherService, actual_slow_service)

    cache_duration = 7 # try different values to see the effect of the cache
    caching_factory = create_caching_weather_decorator_factory(cache_duration_seconds=cache_duration)
    
    services.decorate(IExternalWeatherService, caching_factory)

    provider = services.build_service_provider()

    weather_service = provider.get_service(IExternalWeatherService)
    slow_weather_service_instance_for_metrics = provider.get_service(SlowExternalWeatherService) 

    total_requests_to_weather_service = 0
    initial_api_calls = slow_weather_service_instance_for_metrics.get_api_call_count()

    def make_request(city_name: str, expected_behavior: str):
        nonlocal total_requests_to_weather_service
        total_requests_to_weather_service += 1
        
        print(f"\n{Colors.format(f'--- Requesting {city_name} ({expected_behavior}) ---', Colors.CYAN)}")
        start_time = time.perf_counter()
        temperature = weather_service.get_current_temperature(city_name)
        end_time = time.perf_counter()
        duration = end_time - start_time
        
        time_color = Colors.GREEN if duration < 0.1 else Colors.YELLOW
        temp_str = Colors.format(f"{temperature}°C", bold=True)
        duration_str = Colors.format(f"{duration:.4f}s", time_color)
        print(f"Reported temperature for {city_name}: {temp_str} (took {duration_str})")
        
        api_calls_str = Colors.format(str(slow_weather_service_instance_for_metrics.get_api_call_count()), Colors.BLUE)
        print(f"Actual API calls so far: {api_calls_str}")

    make_request("London", "should be slow, cache miss")
    make_request("London", "should be fast, from cache")
    make_request("New York", "should be slow, cache miss")

    random_sleep_duration = random.uniform(4.0, 9.0) 
    print(f"\n{Colors.format(f'--- Waiting for {random_sleep_duration:.2f} seconds (cache duration is {cache_duration}s)... ---', Colors.CYAN)}")
    time.sleep(random_sleep_duration)

    make_request("London", "cache likely expired, should be slow")
    make_request("New York", "cache might be warm or cold")

    print(f"\n{Colors.format('--- Example Complete ---', bold=True)}")

    final_api_calls = slow_weather_service_instance_for_metrics.get_api_call_count()
    api_calls_during_run = final_api_calls - initial_api_calls
    cached_requests_served = total_requests_to_weather_service - api_calls_during_run

    print(f"\n{Colors.format('--- Summary ---', bold=True)}")
    total_req_str = Colors.format(str(total_requests_to_weather_service), Colors.BLUE)
    print(f"Total requests made to weather_service: {total_req_str}")
    
    api_calls_color = Colors.YELLOW if api_calls_during_run > 0 else Colors.GREEN
    actual_api_str = Colors.format(str(api_calls_during_run), api_calls_color)
    print(f"Total actual calls to SlowExternalWeatherService API: {actual_api_str}")
    
    saved_calls_color = Colors.GREEN if cached_requests_served > 0 else Colors.YELLOW
    saved_calls_str = Colors.format(str(cached_requests_served), saved_calls_color)
    print(f"Number of requests served from cache (slow API calls saved): {saved_calls_str}")

if __name__ == "__main__":
    main() 