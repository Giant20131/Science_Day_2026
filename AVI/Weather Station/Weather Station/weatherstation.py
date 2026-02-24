import requests
import time
from flask import Flask, jsonify, render_template
from retry_requests import retry
import openmeteo_requests
import requests_cache

# ---------------- CONFIG ----------------
LATITUDE = 19.2664
LONGITUDE = 73.0821

UPDATE_INTERVAL = 120  # seconds
PORT = 5000
# --------------------------------------

app = Flask(__name__)
weather_cache = {}
last_update = 0

cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

def fetch_weather():
    """Fetch weather data from Open-Meteo"""
    global weather_cache, last_update
    responses = openmeteo.weather_api(
        "https://api.open-meteo.com/v1/forecast",
        params = {
            	"latitude": 19.2437,
	            "longitude": 73.1355,
	            "daily": ["weather_code", "precipitation_hours", "precipitation_probability_max", "precipitation_sum", "rain_sum", "temperature_2m_min", "temperature_2m_max", "apparent_temperature_max"],
	            "current": ["temperature_2m", "rain", "relative_humidity_2m", "precipitation", "wind_speed_10m", "weather_code", "is_day", "pressure_msl"],
	            "timezone": "auto",
	            "past_days": 3,
	            "forecast_days": 3,
	            "wind_speed_unit": "kn",
})
    response = responses[0]
    
    current = response.Current()
    daily    =  response.Daily()
    weather_cache ={ 
    'current_temperature_2m' : round(current.Variables(0).Value(),2),
    'current_rain' : current.Variables(1).Value(),
    'current_relative_humidity_2m' :current.Variables(2).Value(),
    'current_precipitation' : current.Variables(3).Value(),
    'current_wind_speed_10m' : round(current.Variables(4).Value(),2),
    'current_weather_code' : current.Variables(5).Value(),
    'current_is_day' : current.Variables(6).Value(),
    'current_pressure_msl': round(current.Variables(7).Value(),2),
    "weather_code":daily.Variables(0).ValuesAsNumpy(),
    "precipitation_hours":daily.Variables(1).ValuesAsNumpy(),
    "precipitation_probability_max":daily.Variables(2).ValuesAsNumpy(),
    "precipitation_sum":daily.Variables(3).ValuesAsNumpy(),
    "rain_sum":daily.Variables(4).ValuesAsNumpy(),
    "temperature_2m_min":daily.Variables(5).ValuesAsNumpy(), 
    "temperature_2m_max":daily.Variables(6).ValuesAsNumpy(),
    "apparent_temperature_max":daily.Variables(7).ValuesAsNumpy()

    }

    last_update = time.time()


def update_weather_if_needed():
    if time.time() - last_update > UPDATE_INTERVAL or not weather_cache:
        fetch_weather()

# ---------------- API ROUTES ----------------

@app.route("/api/current")
def api_current():
    update_weather_if_needed()
    return jsonify({
        "temp": weather_cache["current_temperature_2m"],
        "humidity": weather_cache["current_relative_humidity_2m"],
        "weather_code": weather_cache["current_weather_code"]
    })


@app.route("/api/wind")
def api_wind():
    update_weather_if_needed()
    return jsonify({
        "wind_speed": weather_cache["current_wind_speed_10m"],
        "pressure": weather_cache["current_pressure_msl"]
    })
def api_rain():
    update_weather_if_needed()
    return jsonify( {
        "rain": weather_cache.get("rain"),
        "precipitation": weather_cache.get("precipitation")
    })


@app.route("/api/forecast")
def api_forecast():
    # simple placeholder logic
    return jsonify({
        "min_temp": weather_cache.get("temp") - 2,
        "max_temp": weather_cache.get("temp") + 3,
        "rain": weather_cache.get("rain")
    })



@app.route("/")
def home():
    update_weather_if_needed()
    return render_template(
        "index.html",**weather_cache)

# ---------------- MAIN ----------------

if __name__ == "__main__":
    fetch_weather()
    app.run(host="0.0.0.0", port=PORT, debug=True)
