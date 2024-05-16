import requests
from pgeocode import Nominatim
from requests import HTTPError

# replace with desired zip code
DEFAULT_ZIP_CODE = "80223"
BASE_URL = "https://api.weather.gov/"
USER_HEADERS={
    "User-Agent": "Weather API Demo"
}

def get_lat_lon_from_zip(zip_code):
    nomi = Nominatim('us')
    location = nomi.query_postal_code(zip_code)
    if location.empty:
        return None
    # round these to 4 decimal places so it doesn't error out according to the documentation
    return round(location.latitude, 4), round(location.longitude, 4)

def get_closest_weather_station(lat, lon):
    station_url = f"{BASE_URL}points/{lat},{lon}/stations"
    try:
        response = requests.get(station_url, headers=USER_HEADERS)
        if response.status_code != 200:
            raise HTTPError(f"Error occurred while trying to get closest weather station: {response.status_code}")
        return response.json()
    except Exception as e:
        # mormally logging would be here but will print for simplicity
        print(f"Error occurred: {e}")
        return None
def get_weather_data(zip_code=DEFAULT_ZIP_CODE):
    lat_lon = get_lat_lon_from_zip(zip_code)
    if lat_lon is None:
        raise Exception("Error occurred while trying to get lat/lon from zip code")
    lat, lon = lat_lon
    station_data = get_closest_weather_station(lat, lon)



get_weather_data()