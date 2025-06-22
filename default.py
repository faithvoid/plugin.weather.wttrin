# -*- coding: utf-8 -*-
import sys
import json
import urllib2
import xbmc
import xbmcgui
import datetime

# Helper function for the below date formatting function to parse current date data.
def ordinal(n):
    if 10 <= n % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return str(n) + suffix

# Format date from "2025-06-23" to "June 26th, 2025"
def format_forecast_date(date_str):
    dt = datetime.datetime.strptime(date_str, '%Y-%m-%d')
    month_name = dt.strftime('%B')  # Full month name
    day = ordinal(dt.day)
    year = dt.year
    return "%s %s, %d" % (month_name, day, year)

# Grab icon data from OpenWeatherMap by converting WTTR weather codes to OpenWeatherMap codes
def map_wttr_code_to_owm_icon(code):
    mapping = {
        "113": "01d",
        "116": "02d",
        "119": "03d",
        "122": "04d",
        "143": "50d",
        "176": "09d",
        "179": "13d",
        "182": "13d",
        "185": "13d",
        "200": "11d",
        "227": "13d",
        "230": "13d",
        "248": "50d",
        "260": "50d",
        "263": "09d",
        "266": "10d",
        "281": "13d",
        "284": "13d",
        "293": "09d",
        "296": "10d",
        "299": "09d",
        "302": "10d",
        "305": "09d",
        "308": "10d",
        "311": "13d",
        "314": "13d",
        "317": "13d",
        "320": "13d",
        "323": "13d",
        "326": "13d",
        "329": "13d",
        "332": "13d",
        "335": "13d",
        "338": "13d",
        "350": "13d",
        "353": "09d",
        "356": "10d",
        "359": "09d",
        "362": "13d",
        "365": "13d",
        "368": "13d",
        "371": "13d",
        "374": "13d",
        "377": "13d",
        "386": "11d",
        "389": "11d",
        "392": "11d",
        "395": "13d",
    }
    return mapping.get(str(code), "01d")  # default clear day icon

# Get location city name from XBMC (currently needs to be in advancedsettings.xml! guisettings.xml seems to re-generate itself when modified, and editing from Weather Settings freezes.)
city_name = xbmc.getInfoLabel("Weather.Location")
if not city_name:
    xbmcgui.Dialog().ok("Weather Error", "No location found")
    sys.exit(1)

#Get temperature unit from currently set XBMC4Xbox region
unit_key = xbmc.getRegion('tempunit').upper()
if unit_key not in ('C', 'F'):
    unit_key = 'C'  # default to Celsius if invalid or missing

unit_symbol = u"°C" if unit_key == "C" else u"°F"

#Get speed unit (kmh, mph) from currently set XBMC4Xbox region
speedunit_key = xbmc.getRegion('speedunit').upper()
if speedunit_key not in ('kmh', 'mph'):
    speedunit_key = 'kmh'  # default to Celsius if invalid or missing

speedunit_symbol = "km/h" if speedunit_key == "kmh" else "mph"

# URL encode city name for query
location = urllib2.quote(city_name)

# Fetch weather data from wttr.in by sending a request with the current location
url = "http://wttr.in/{}?format=j1".format(location)

try:
    response = urllib2.urlopen(url, timeout=5)
    data = response.read()
    weather = json.loads(data)
except Exception as e:
    xbmc.log("Weather Error", xbmc.LOGERROR)
    weather = None

# Set skin properties on the Weather window
window = xbmcgui.Window(12600)

if weather:
    current = weather['current_condition'][0]
    hourly = weather['weather'][0]['hourly'][4]

    # Current conditions with unit appended
    temp = current['temp_' + unit_key]
    feels_like = current['FeelsLike' + unit_key] + unit_symbol
    dew_point = hourly['DewPoint' + unit_key] + unit_symbol
    desc = current['weatherDesc'][0]['value']
    humidity = current['humidity']
    uv_index = hourly['uvIndex']
    if speedunit_key == "MPH":
        wind = hourly['WindGustMiles'] + " " + speedunit_symbol
    else:
        wind = hourly['WindGustKmph'] + " " + speedunit_symbol

    weather_code = current.get('weatherCode')

    # Map wttr.in weather code to OpenWeatherMap icon code and build icon URL
    owm_icon_code = map_wttr_code_to_owm_icon(weather_code)
    icon_url = "http://openweathermap.org/img/wn/{}@2x.png".format(owm_icon_code)

    window.setProperty("Current.Temperature", temp)
    window.setProperty("Current.Condition", desc)
    window.setProperty("Current.Humidity", humidity + "%")
    window.setProperty("Current.FeelsLike", feels_like)
    window.setProperty("Current.ConditionIcon", icon_url)
    window.setProperty("Current.UVIndex", uv_index)
    window.setProperty("Current.DewPoint", dew_point)
    window.setProperty("Current.Wind", wind)
    window.setProperty("Current.Location", city_name)

    # Forecast (next 3 days, unfortunately the day 4 will always be blank with wttr.in as it doesn't expose that info!)
    for i, day in enumerate(weather['weather'][0:3]):
        high = "High: " + day['maxtemp' + unit_key]
        low = "Low: " + day['mintemp' + unit_key]
        outlook = day['hourly'][4]['weatherDesc'][0]['value']

        forecast_code = day['hourly'][4].get('weatherCode')
        forecast_icon_code = map_wttr_code_to_owm_icon(forecast_code)
        forecast_icon_url = "http://openweathermap.org/img/wn/{}@2x.png".format(forecast_icon_code)

        window.setProperty("Day%d.HighTemp" % i, high)
        window.setProperty("Day%d.LowTemp" % i, low)
        window.setProperty("Day%d.Outlook" % i, outlook)
        window.setProperty("Day%d.OutlookIcon" % i, forecast_icon_url)
        window.setProperty("Day%d.Title" % i, format_forecast_date(day['date']))
else:
    window.setProperty("Current.Condition", "")
    window.setProperty("Current.Temperature", "")
