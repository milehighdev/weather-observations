import requests
from pgeocode import Nominatim
from requests import HTTPError

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
        raise HTTPError(f"Error occurred while trying to check weather api: {error_data['status']} {error_data['detail']} {error_data['correlationId']}")

def get_closest_weather_station(lat, lon):
    station_url = f"{BASE_URL}points/{lat},{lon}"
    try:
        response = requests.get(station_url, headers=USER_HEADERS)
        check_response(response)
        response_data = response.json()
        print(response_data)
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
        print(response_data)

        stations = response_data.get('features', [])
        if not stations:
            raise Exception(f"No weather stations found for gridpoints {grid_id} {grid_x} {grid_y}")


    except Exception as e:
        # mormally we'd log this as an error but printing for simplicity
        print(f"Error occurred trying to find weather station: {e}")
        return None
def get_weather_data(zip_code=DEFAULT_ZIP_CODE):
    lat_lon = get_lat_lon_from_zip(zip_code)
    if lat_lon is None:
        raise Exception("Error occurred while trying to get lat/lon from zip code")
    lat, lon = lat_lon
    station_data = get_closest_weather_station(lat, lon)


#replace with desired zip or leave as Denver area
get_weather_data()