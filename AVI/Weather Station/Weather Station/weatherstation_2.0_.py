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
    daily    = response.Daily()

    # current variables
    current_temperature_2m =       current.Variables(0).Value()
    current_rain =                 current.Variables(1).Value()
    current_relative_humidity_2m = current.Variables(2).Value()
    current_precipitation =        current.Variables(3).Value()
    current_wind_speed_10m =       current.Variables(4).Value()
    current_weather_code =         current.Variables(5).Value()
    current_is_day =               current.Variables(6).Value()
    current_pressure_msl=          current.Variables(7).Value()
    # Daily variables are arrays (one value per day). Grab today's value (index 0).
    daily_weather_code = daily.Variables(0).ValuesAsNumpy()
    daily_precipitation_hours = daily.Variables(1).ValuesAsNumpy()
    daily_precipitation_probability_max = daily.Variables(2).ValuesAsNumpy()
    daily_precipitation_sum = daily.Variables(3).ValuesAsNumpy()
    daily_rain_sum = daily.Variables(4).ValuesAsNumpy()
    daily_temperature_2m_min = daily.Variables(5).ValuesAsNumpy()
    daily_temperature_2m_max = daily.Variables(6).ValuesAsNumpy()
    daily_apparent_temperature_max = daily.Variables(7).ValuesAsNumpy()
    weather_cache ={ 
    'day': "Mon" if time.localtime()[6]==0 else("Tue" if time.localtime()[6]==1 else("Wed" if time.localtime()[6] == 2 else("Thu" if time.localtime()[6] == 3 else("Fri" if time.localtime()[6]==4 else("Sat" if time.localtime()[6]==5 else("Sun" if time.localtime()[6] == 6 else(None))))))),
    "date": int(time.localtime()[2]),
    "month": 'Jan' if time.localtime()[1] == 1 else("Feb" if time.localtime()[1]==2 else('Mar' if time.localtime()[1]==3 else('Apr' if time.localtime()[1]==4 else('May' if time.localtime()[1]==5 else('Jun' if time.localtime()[1]==6 else('Jul' if time.localtime()[1]==7 else('Aug'if time.localtime()[1]==8 else('Sep' if time.localtime()[1]==9 else('Oct' if time.localtime()[1]==10 else('Nov' if time.localtime()[1]==11 else('Dec' if time.localtime()[1]==12 else(None)))))))))))),
    'current_temperature_2m' : round(current_temperature_2m,2),
    'current_rain' : current_rain,
    'current_relative_humidity_2m' :current_relative_humidity_2m,
    'current_precipitation' : current_precipitation,
    'current_wind_speed_10m' : round(current_wind_speed_10m,2),
    # check for weather according to ww code
    'current_weather_code' : "Clear sky" if current_weather_code<1 else ("Mainly clear, partly cloudy, and overcast" if current_weather_code<4 else("Fog and depositing rime fog" if current_weather_code<50 else("Drizzle: Light, moderate, and dense intensity" if current_weather_code<56 else("Freezing Drizzle: Light and dense intensity" if current_weather_code<60 else("Rain: Slight, moderate and heavy intensity" if current_weather_code<66 else("Freezing Rain: Light and heavy intensity" if current_weather_code<70 else("Snow fall: Slight, moderate, and heavy intensity" if current_weather_code<76 else("Snow grains" if current_weather_code == 77 else("Rain showers: Slight, moderate, and violent" if current_weather_code<83 else("Snow showers slight and heavy" if current_weather_code<87 else("Thunderstorm: Slight or moderate" if current_weather_code == 95 else ("Thunderstorm with slight and heavy hail" if current_weather_code< 100 else("Couldn't Fetch Weather") )))))))))))),
    'current_is_day' : "day" if current.Variables(6).Value()==1 else("night"),
    'current_pressure_msl': round(current.Variables(7).Value(),2),
    "daily_weather_code": daily_weather_code,
    "daily_precipitation_hours": daily_precipitation_hours,
    "daily_precipitation_probability_max":daily_precipitation_probability_max,
    "daily_precipitation_sum": daily_precipitation_sum,
    "daily_rain_sum": daily_rain_sum,
    "daily_temperature_2m_min": daily_temperature_2m_min,
    "daily_temperature_2m_max": daily_temperature_2m_max,
    "daily_apparent_temperature_max": daily_apparent_temperature_max,
    "today_weather_code":"Clear sky" if daily_weather_code[0]<1 else ("Mainly clear, partly cloudy, and overcast" if daily_weather_code[0]<4 else("Fog and depositing rime fog" if daily_weather_code[0]<50 else("Drizzle: Light, moderate, and dense intensity" if daily_weather_code[0]<56 else("Freezing Drizzle: Light and dense intensity" if daily_weather_code[0]<60 else("Rain: Slight, moderate and heavy intensity" if daily_weather_code[0]<66 else("Freezing Rain: Light and heavy intensity" if daily_weather_code[0]<70 else("Snow fall: Slight, moderate, and heavy intensity" if daily_weather_code[0]<76 else("Snow grains" if daily_weather_code[0] == 77 else("Rain showers: Slight, moderate, and violent" if daily_weather_code[0]<83 else("Snow showers slight and heavy" if daily_weather_code[0]<87 else("Thunderstorm: Slight or moderate" if daily_weather_code[0] == 95 else ("Thunderstorm with slight and heavy hail" if daily_weather_code[0]< 100 else("Couldn't Fetch Weather") )))))))))))),
    "today_precipitation_hours": float(daily_precipitation_hours[0]),
    "today_precipitation_probability_max": float(daily_precipitation_probability_max[0]),
    "today_precipitation_sum": float(daily_precipitation_sum[0]),
    "today_rain_sum": float(daily_rain_sum[0]),
    "today_temperature_2m_min": round(float(daily_temperature_2m_min[0]), 2),
    "today_temperature_2m_max": round(float(daily_temperature_2m_max[0]), 2),
    "today_apparent_temperature_max": round(float(daily_apparent_temperature_max[0]), 2)

    }

    # ---- Build daily forecast cards (past + future) ----
    past_days = 3
    total_days = len(daily_temperature_2m_max)

    daily_cards = []

    now = time.localtime()

    for i in range(total_days):
        day_offset = i - past_days
        day_time = time.localtime(time.time() + day_offset * 86400)

        daily_cards.append({
            "label": (
                "Today" if day_offset == 0 else
                "Yesterday" if day_offset == -1 else
                f"{day_offset:+d} days"
            ),
            "day": time.strftime("%a", day_time),
            "date": day_time.tm_mday,
            "month": time.strftime("%b", day_time),
            "weather": (
                "Clear sky" if daily_weather_code[i] < 1 else
                "Cloudy" if daily_weather_code[i] < 4 else
                "Rain" if daily_weather_code[i] < 70 else
                "Storm"
            ),
            "t_min": round(float(daily_temperature_2m_min[i]), 1),
            "t_max": round(float(daily_temperature_2m_max[i]), 1),
            "rain": round(float(daily_rain_sum[i]), 1),
            "precip_hours": round(float(daily_precipitation_hours[i]), 1),
            "precip_prob": round(float(daily_precipitation_probability_max[i]), 0)
        })

    weather_cache["daily_cards"] = daily_cards


    last_update = time.time()


def update_weather_if_needed():
    if time.time() - last_update > UPDATE_INTERVAL or not weather_cache:
        fetch_weather()

# ---------------- API ROUTES ----------------

@app.route("/api/current")
def api_current():
    update_weather_if_needed()
    return jsonify({
        "temp:": str(weather_cache["current_temperature_2m"])+" C",        
        "humidity:":str( weather_cache["current_relative_humidity_2m"])+" %",
        "weather:":str(weather_cache["current_weather_code"].split(",")[0])
    })


@app.route("/api/wind")
def api_wind():
    update_weather_if_needed()
    return jsonify({
        "wind_speed:":str( weather_cache["current_wind_speed_10m"])+" kn",
        "pressure": str(weather_cache["current_pressure_msl"])+" hPa"
    })

@app.route("/api/rain")
def api_rain():
    update_weather_if_needed()

    rain_val = None
    if weather_cache["current_rain"] > 0:
        rain_val = f"{weather_cache['current_rain']} mm"
    elif weather_cache["today_rain_sum"] > 0:
        rain_val = f"Day's rain {weather_cache['today_rain_sum']} mm"

    precip_val = None
    if weather_cache["current_precipitation"] > 0:
        precip_val = f"{weather_cache['current_precipitation']} mm"
    elif weather_cache["today_precipitation_sum"] > 0:
        precip_val = f"Day's precipitation {weather_cache['today_precipitation_sum']} mm"

    return jsonify({
        "rain:": rain_val,
        "precipitation:": precip_val
    })


@app.route("/api/forecast")
def api_forecast():
    # simple placeholder logic
    return jsonify({
        "max_temp": str(weather_cache["today_temperature_2m_max"]) +" C",
        "min_temp": str(weather_cache["today_temperature_2m_min"])+" C",
        'today_weather_status': str(weather_cache["today_weather_code"].split(",")[0])
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
