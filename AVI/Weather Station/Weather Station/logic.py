import openmeteo_requests

import pandas as pd
import requests_cache
from retry_requests import retry

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

# Make sure all required weather variables are listed here
# The order of variables in hourly or daily is important to assign them correctly below
url = "https://api.open-meteo.com/v1/forecast"
params = {
	"latitude": 19.2437,
	"longitude": 73.1355,
	"daily": ["weather_code", "precipitation_hours", "precipitation_probability_max", "precipitation_sum", "rain_sum", "temperature_2m_min", "temperature_2m_max", "apparent_temperature_max"],
	"current": ["temperature_2m", "rain", "relative_humidity_2m", "precipitation", "wind_speed_10m", "weather_code", "is_day", "pressure_msl"],
	"timezone": "auto",
	"past_days": 3,
	"forecast_days": 3,
	"wind_speed_unit": "kn",
}
responses = openmeteo.weather_api(url, params=params)

# Process first location. Add a for-loop for multiple locations or weather models
response = responses[0]
print(f"Coordinates: {response.Latitude()}°N {response.Longitude()}°E")
print(f"Elevation: {response.Elevation()} m asl")
print(f"Timezone: {response.Timezone()}{response.TimezoneAbbreviation()}")
print(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()}s")

# Process current data. The order of variables needs to be the same as requested.
current = response.Current()
current_temperature_2m = current.Variables(0).Value()
current_rain = current.Variables(1).Value()
current_relative_humidity_2m = current.Variables(2).Value()
current_precipitation = current.Variables(3).Value()
current_wind_speed_10m = current.Variables(4).Value()
current_weather_code = current.Variables(5).Value()
current_is_day = current.Variables(6).Value()
current_pressure_msl = current.Variables(7).Value()

print(f"\nCurrent time: {current.Time()}")
print(f"Current temperature_2m: {current_temperature_2m}")
print(f"Current rain: {current_rain}")
print(f"Current relative_humidity_2m: {current_relative_humidity_2m}")
print(f"Current precipitation: {current_precipitation}")
print(f"Current wind_speed_10m: {current_wind_speed_10m}")
print(f"Current weather_code: {current_weather_code}")
print(f"Current is_day: {current_is_day}")
print(f"Current pressure_msl: {current_pressure_msl}")

# Process daily data. The order of variables needs to be the same as requested.
daily = response.Daily()
daily_weather_code = daily.Variables(0).ValuesAsNumpy()
daily_precipitation_hours = daily.Variables(1).ValuesAsNumpy()
daily_precipitation_probability_max = daily.Variables(2).ValuesAsNumpy()
daily_precipitation_sum = daily.Variables(3).ValuesAsNumpy()
daily_rain_sum = daily.Variables(4).ValuesAsNumpy()
daily_temperature_2m_min = daily.Variables(5).ValuesAsNumpy()
daily_temperature_2m_max = daily.Variables(6).ValuesAsNumpy()
daily_apparent_temperature_max = daily.Variables(7).ValuesAsNumpy()

daily_data = {"date": pd.date_range(
	start = pd.to_datetime(daily.Time() + response.UtcOffsetSeconds(), unit = "s", utc = True),
	end =  pd.to_datetime(daily.TimeEnd() + response.UtcOffsetSeconds(), unit = "s", utc = True),
	freq = pd.Timedelta(seconds = daily.Interval()),
	inclusive = "left"
)}

daily_data["weather_code"] = daily_weather_code
daily_data["precipitation_hours"] = daily_precipitation_hours
daily_data["precipitation_probability_max"] = daily_precipitation_probability_max
daily_data["precipitation_sum"] = daily_precipitation_sum
daily_data["rain_sum"] = daily_rain_sum
daily_data["temperature_2m_min"] = daily_temperature_2m_min
daily_data["temperature_2m_max"] = daily_temperature_2m_max
daily_data["apparent_temperature_max"] = daily_apparent_temperature_max

daily_dataframe = pd.DataFrame(data = daily_data)
print("\nDaily data\n", daily_dataframe)
