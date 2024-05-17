import requests
from pgeocode import Nominatim
from requests import HTTPError
import math
from datetime import datetime, timedelta
from collections import defaultdict

DEFAULT_ZIP_CODE = "80223"
BASE_URL = "https://api.weather.gov/"
# We don't need this to make the call but adding here per their suggestion to identify the user
USER_HEADERS={
    "User-Agent": "barneshm Weather API Demo"
}

def get_lat_lon_from_zip(zip_code):
    nomi = Nominatim('us')
    location = nomi.query_postal_code(zip_code)
    if location.empty:
        return None
    # round these to 4 decimal places so api call doesn't error out according to the documentation
    return round(location.latitude, 4), round(location.longitude, 4)

# we could add more error handling here but for simplicity we'll just raise an exception
def check_response(response):
    if not response.ok:
        error_data = response.json()
        raise HTTPError(f"Error occurred while trying to call weather api: {error_data['status']} {error_data['detail']} {error_data['correlationId']}")

#this may not be accounting for all factors due to the curvature of the earth but should be close enough for this use case
def find_distance_pythagorean(lat1, lon1, lat2, lon2):
    # get our target lat and lon and ones from list and calculate the distance between them
    lat_diff = lat2 - lat1
    lon_diff = lon2 - lon1
    return math.sqrt(lat_diff ** 2 + lon_diff ** 2)

def get_station_observations(station_id, start_time, end_time):
    try:
        observations_url = f"{BASE_URL}/stations/{station_id}/observations?start={start_time}&end={end_time}"
        response = requests.get(observations_url, headers=USER_HEADERS)
        check_response(response)
        observations_data = response.json()

        observations = observations_data.get('features', [])
        if not observations:
            raise Exception("No observations found")

        return observations
    except Exception as e:
        print(f"Error in get_station_observations: {e}")
        return None

def process_daily_temps(observations):
    #using a defaultdict so we don't have to check if the key exists before updating
    daily_temps = defaultdict(lambda: {"min": float('inf'), "max": float('-inf')})

    # I think using these max and min values for temp are correct because the minTempLast24Hours and
    #     # maxTempLast24Hours are always null from API. Not sure if this is a bug.
    for observation in observations:
        properties = observation.get('properties', {})
        temp_dict = properties.get('temperature', {})
        temp = temp_dict.get('value') if temp_dict else None
        timestamp = properties.get('timestamp')

        if timestamp and temp is not None:
            try:
                # Parse timestamp
                observation_datetime = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S%z")

                observation_date = observation_datetime.date()

                # Get current max and min in our dict
                current_max_temp = daily_temps[observation_date]["max"]
                current_min_temp = daily_temps[observation_date]["min"]

                # if we find a temp that is bigger than our current max, update it
                # use the date as our key so we don't have duplicate days
                if temp > current_max_temp:
                    daily_temps[observation_date]["max"] = temp
                #if we find a temp that is smaller than our current min, update it
                if temp < current_min_temp:
                    daily_temps[observation_date]["min"] = temp

            except ValueError as e:
                print(f"Error parsing timestamp: {e}")
                continue

    # make a list with date and then the daily high and low temps
    data = []
    for date, temps in daily_temps.items():
        data.append({"day": str(date), "high": temps["max"], "low": temps["min"]})
    return data

def get_closest_weather_station(lat, lon):
    station_url = f"{BASE_URL}points/{lat},{lon}"
    try:
        response = requests.get(station_url, headers=USER_HEADERS)
        check_response(response)
        response_data = response.json()
        grid_id = response_data.get('properties', {}).get('gridId')
        grid_x = response_data.get('properties', {}).get('gridX')
        grid_y = response_data.get('properties', {}).get('gridY')

        if not grid_id or not grid_x or not grid_y:
            raise Exception("Error occurred while trying to get grid points information")
        # We could log these values as info futher detail but printing for simplicity
        print(f"Closest weather station found: {grid_id} {grid_x} {grid_y}")

        station_url = f"{BASE_URL}gridpoints/{grid_id}/{grid_x},{grid_y}/stations"
        response = requests.get(station_url, headers=USER_HEADERS)
        check_response(response)
        response_data = response.json()

        stations = response_data.get('features', [])
        if not stations:
            raise Exception(f"No weather stations found for gridpoints {grid_id} {grid_x} {grid_y}")

        min_distance = float('inf')
        closest_station = None

        #we are assuming the list of statinos is small enough to iterate through all of them
        # for enhancement it may be good to filter out based on some min/max bounds
        for station in stations:
            station_coords = station.get('geometry', {}).get('coordinates', [])
            if len(station_coords) != 2:
                continue

            station_lat, station_lon = station_coords[1], station_coords[0]

            distance = find_distance_pythagorean(lat, lon, station_lat, station_lon)

            if distance < min_distance:
                min_distance = distance
                closest_station = station

        if not closest_station:
            raise Exception("Failed to find the closest weather station")

        station_properties = closest_station.get('properties', {})
        station_id = station_properties.get('stationIdentifier')

        if not station_id:
            raise Exception("Failed to find the station identifier")

        return station_id

    except Exception as e:
        # mormally we'd log this as an error but printing for simplicity
        print(f"Error occurred trying to find weather station: {e}")
        return None
def get_weather_data(zip_code=DEFAULT_ZIP_CODE):
   try:
        lat_lon = get_lat_lon_from_zip(zip_code)
        if lat_lon is None:
            raise Exception("Error occurred while trying to get lat/lon from zip code")
        lat, lon = lat_lon
        station_id = get_closest_weather_station(lat, lon)

        #get last 7 days so we don't have a large data set
        end_date = datetime.utcnow().date() - timedelta(days=1)
        start_date = end_date - timedelta(days=7)

        start_time = datetime.combine(start_date, datetime.min.time()).isoformat() + "Z"
        end_time = datetime.combine(end_date, datetime.max.time()).isoformat() + "Z"

        observations = get_station_observations(station_id, start_time, end_time)

        weather_data = process_daily_temps(observations)

        print(weather_data)

   except Exception as e:
    print(f"Error getting weather data: {e}")
    return None

#replace with desired zip or leave as Denver area
weather_data = get_weather_data()
