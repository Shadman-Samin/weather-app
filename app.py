import os
import requests
import datetime
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
from dotenv import load_dotenv
import logging

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

logging.basicConfig(level=logging.ERROR,
                    format='%(asctime)s - %(levelname)s - %(message)s')

API_KEY = os.getenv('API_KEY')
PEXELS_API_KEY = os.getenv('PEXELS_API_KEY')

BASE_URL = "http://api.openweathermap.org/data/2.5/weather?"
FORECAST_URL = "http://api.openweathermap.org/data/2.5/forecast?"
GEO_URL = "http://api.openweathermap.org/geo/1.0/direct?"
PEXELS_URL = "https://api.pexels.com/v1/search?query={}&per_page=1"

if not API_KEY:
    logging.error("OpenWeatherMap API key is not set in the environment variables.")

def get_coordinates(city):
    if not API_KEY:
        return None, None, city
    url = f"{GEO_URL}q={city}&limit=1&appid={API_KEY}"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        if data:
            location_name = data[0]['name']
            if 'country' in data[0]:
                location_name += f", {data[0]['country']}"
            return data[0]['lat'], data[0]['lon'], location_name
        else:
            flash(f"Could not find coordinates for {city}. Check the city name.", 'error')
            return None, None, city
    except Exception as e:
        logging.exception("An error occurred during geocoding:")
        flash("An unexpected error occurred. Please try again.", 'error')
        return None, None, city

def get_city_image(city):
    if not PEXELS_API_KEY:
        return None

    headers = {'Authorization': PEXELS_API_KEY}
    try:
        query = city.split(',')[0] + " landscape architecture city"
        response = requests.get(PEXELS_URL.format(query), headers=headers, timeout=5)
        response.raise_for_status()
        image_data = response.json()

        if image_data.get("photos"):
            return image_data["photos"][0]["src"]["original"]
        return None
    except Exception as e:
        logging.error(f"Error fetching image from Pexels: {e}")
        return None

def get_weather_effect(description):
    if not description:
        return 'default-effect'
    description = description.lower()
    if 'rain' in description or 'drizzle' in description: return 'rainy-effect'
    elif 'clear' in description: return 'sunny-effect'
    elif 'cloud' in description or 'fog' in description or 'mist' in description: return 'cloudy-effect'
    elif 'snow' in description or 'sleet' in description: return 'snowy-effect'
    elif 'thunderstorm' in description: return 'stormy-effect'
    elif 'haze' in description: return 'hazy-effect'
    else: return 'default-effect'

def format_datetime_with_offset(timestamp, offset):
    if not timestamp: return "N/A"
    try:
        # timestamp is in UTC, offset is in seconds
        dt_object = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc) + datetime.timedelta(seconds=offset)
        return dt_object.strftime('%H:%M')
    except Exception as e:
        return "N/A"

def get_wind_direction_string(degrees):
    directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    index = round(degrees / (360. / len(directions))) % len(directions)
    return directions[index]

def save_search_history(city):
    if "search_history" not in session:
        session["search_history"] = []
    
    history = session["search_history"]
    history = [item for item in history if item['city'].lower() != city.lower()]
    history.insert(0, {"city": city, "timestamp": datetime.datetime.now().isoformat()})
    session["search_history"] = history[:10]

def get_weather_data(latitude, longitude):
    if not API_KEY:
        flash("Weather data is unavailable. Please check the API key.", 'error')
        return None
    url = f"{BASE_URL}lat={latitude}&lon={longitude}&appid={API_KEY}&units=metric"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        flash("Error fetching weather data.", 'error')
        return None

def get_forecast_data(latitude, longitude, offset):
    if not API_KEY:
        return []
    url = f"{FORECAST_URL}lat={latitude}&lon={longitude}&appid={API_KEY}&units=metric"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        forecasts = []
        seen_dates = set()
        for item in data.get("list", []):
            dt_txt = item.get("dt_txt", "")
            
            # Apply offset to get local time for forecast date
            dt = datetime.datetime.strptime(dt_txt, '%Y-%m-%d %H:%M:%S')
            dt = dt.replace(tzinfo=datetime.timezone.utc) + datetime.timedelta(seconds=offset)
            date = dt.strftime('%Y-%m-%d')
            hour = dt.strftime('%H')
            
            if date not in seen_dates and "11" <= hour <= "14":
                seen_dates.add(date)
                forecasts.append({
                    "date": dt.strftime('%a, %b %d'),
                    "temperature": round(item["main"]["temp"]),
                    "description": item["weather"][0]["description"].title(),
                    "icon": item["weather"][0]["icon"]
                })
        if not forecasts:
             for i in range(0, len(data.get("list", [])), 8):
                 item = data["list"][i]
                 dt = datetime.datetime.strptime(item.get("dt_txt", ""), '%Y-%m-%d %H:%M:%S')
                 dt = dt.replace(tzinfo=datetime.timezone.utc) + datetime.timedelta(seconds=offset)
                 forecasts.append({
                    "date": dt.strftime('%a, %b %d'),
                    "temperature": round(item["main"]["temp"]),
                    "description": item["weather"][0]["description"].title(),
                    "icon": item["weather"][0]["icon"]
                })
        return forecasts[:5]
    except Exception as e:
        logging.error(f"Error fetching forecast: {e}")
        return []

def process_weather_data(weather_data, city, latitude, longitude):
    try:
        main_data = weather_data["main"]
        weather_info = weather_data["weather"][0]
        wind_data = weather_data["wind"]
        sys_data = weather_data["sys"]
        timezone_offset = weather_data.get("timezone", 0)

        sunrise_time = format_datetime_with_offset(sys_data.get("sunrise"), timezone_offset)
        sunset_time = format_datetime_with_offset(sys_data.get("sunset"), timezone_offset)
        wind_direction_string = get_wind_direction_string(wind_data.get("deg", 0))

        now_utc = datetime.datetime.now(datetime.timezone.utc)
        local_time = now_utc + datetime.timedelta(seconds=timezone_offset)

        processed_data = {
            "city": city,
            "latitude": latitude,
            "longitude": longitude,
            "temperature": round(main_data["temp"]),
            "feels_like": round(main_data["feels_like"]),
            "humidity": main_data["humidity"],
            "pressure": main_data["pressure"],
            "visibility": weather_data.get("visibility", 0) / 1000,
            "cloudiness": weather_data.get("clouds", {}).get("all", 0),
            "rain_last_3h": weather_data.get("rain", {}).get("3h", 0) if isinstance(weather_data.get("rain"), dict) else 0,
            "wind_speed": wind_data["speed"],
            "wind_direction": wind_data.get("deg", 0),
            "wind_direction_string": wind_direction_string,
            "description": weather_info["description"].title(),
            "icon": weather_info["icon"],
            "sunrise": sunrise_time,
            "sunset": sunset_time,
            "timezone_offset": timezone_offset,
            "last_updated": local_time.strftime('%a, %I:%M %p')
        }
        return processed_data
    except Exception as e:
        logging.error(f"Error processing weather data: {e}")
        return None

@app.route('/api/suggestions')
def suggestions():
    query = request.args.get('q', '').strip()
    if not query or not API_KEY:
        return jsonify([])
    
    url = f"{GEO_URL}q={query}&limit=5&appid={API_KEY}"
    try:
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            data = response.json()
            results = []
            seen = set()
            for item in data:
                name = item.get('name')
                country = item.get('country')
                state = item.get('state', '')
                
                parts = [name]
                if state: parts.append(state)
                if country: parts.append(country)
                
                full_name = ", ".join(parts)
                if full_name not in seen:
                    seen.add(full_name)
                    results.append({"name": full_name, "lat": item.get('lat'), "lon": item.get('lon')})
            return jsonify(results)
    except Exception as e:
        pass
    return jsonify([])

@app.route("/", methods=["GET", "POST"])
def index():
    weather_data = None
    city_image = None
    weather_effect = None
    
    if request.method == "POST":
        city = request.form.get("city", "").strip()
        if not city:
            flash("Please enter a city name.", 'error')
        else:
            latitude, longitude, actual_city = get_coordinates(city)
            if latitude and longitude:
                raw_weather = get_weather_data(latitude, longitude)
                if raw_weather and "main" in raw_weather:
                    if not actual_city or actual_city == city:
                         c_name = raw_weather.get('name', city)
                         country = raw_weather.get('sys', {}).get('country', '')
                         actual_city = f"{c_name}, {country}" if country else c_name

                    weather_data = process_weather_data(raw_weather, actual_city, latitude, longitude)
                    if weather_data:
                        # Fetch forecast and city image in PARALLEL
                        with ThreadPoolExecutor(max_workers=2) as executor:
                            forecast_future = executor.submit(get_forecast_data, latitude, longitude, weather_data['timezone_offset'])
                            image_future = executor.submit(get_city_image, actual_city)
                            weather_data["forecast"] = forecast_future.result()
                            city_image = image_future.result()
                        weather_effect = get_weather_effect(weather_data["description"])
                        save_search_history(actual_city)
                else:
                    flash("City not found or API request failed.", 'error')

    elif request.args.get('lat') and request.args.get('lon'):
        try:
            latitude = float(request.args.get('lat'))
            longitude = float(request.args.get('lon'))
            raw_weather = get_weather_data(latitude, longitude)
            if raw_weather and "main" in raw_weather:
                c_name = raw_weather.get('name', 'Unknown Location')
                country = raw_weather.get('sys', {}).get('country', '')
                actual_city = f"{c_name}, {country}" if country else c_name
                
                weather_data = process_weather_data(raw_weather, actual_city, latitude, longitude)
                if weather_data:
                    # Fetch forecast and city image in PARALLEL
                    with ThreadPoolExecutor(max_workers=2) as executor:
                        forecast_future = executor.submit(get_forecast_data, latitude, longitude, weather_data['timezone_offset'])
                        image_future = executor.submit(get_city_image, actual_city)
                        weather_data["forecast"] = forecast_future.result()
                        city_image = image_future.result()
                    weather_effect = get_weather_effect(weather_data["description"])
                    save_search_history(actual_city)
            else:
                flash("Invalid coordinates or API request failed.", 'error')
        except ValueError:
            flash("Invalid latitude or longitude.", 'error')

    search_history = session.get("search_history", [])
    
    return render_template(
        "index.html",
        weather_data=weather_data,
        city_image=city_image,
        weather_effect=weather_effect,
        search_history=search_history
    )

@app.route('/clear_history')
def clear_history():
    session['search_history'] = []
    return redirect(url_for('index'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template("500.html"), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)