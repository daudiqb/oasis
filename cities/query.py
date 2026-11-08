"""
Query functions for the cities collection, stored in MongoDB
through data/db_connect.py.
"""
import data.db_connect as dbc
from data.db_connect import needs_db

CITIES_COLLECT = 'cities'

NAME = 'name'
STATE_CODE = 'state_code'
LATITUDE = 'latitude'
LONGITUDE = 'longitude'

STATE_CODE_LEN = 2
MIN_LATITUDE = -90
MAX_LATITUDE = 90
MIN_LONGITUDE = -180
MAX_LONGITUDE = 180

TEST_CITY = {
    NAME: 'Test City',
    STATE_CODE: 'NY',
    LATITUDE: 40.0,
    LONGITUDE: -74.0,
}


def city_filter(name: str, state_code: str) -> dict:
    """
    Return the MongoDB filter that finds one city.
    """
    return {NAME: name, STATE_CODE: state_code}


@needs_db
def read():
    """
    Return a list of all cities.
    Returns None if the database is down.
    """
    return dbc.read(CITIES_COLLECT)


def check_valid_city(name: str, state_code: str,
                     latitude: float, longitude: float):
    """
    Raise ValueError if any city field is invalid.
    Returns True if the city is valid.
    """
    if not isinstance(name, str) or not name:
        raise ValueError('City name must be a non-empty string.')
    if not isinstance(state_code, str) or len(state_code) != STATE_CODE_LEN:
        raise ValueError(f'State code must be {STATE_CODE_LEN} letters.')
    if not isinstance(latitude, (int, float)) \
            or not MIN_LATITUDE <= latitude <= MAX_LATITUDE:
        raise ValueError('Latitude must be between -90 and 90.')
    if not isinstance(longitude, (int, float)) \
            or not MIN_LONGITUDE <= longitude <= MAX_LONGITUDE:
        raise ValueError('Longitude must be between -180 and 180.')
    return True


def create(name: str, state_code: str, latitude: float, longitude: float):
    """
    Add a new city to the database and return it.
    Returns None if the database is down.
    """
    check_valid_city(name, state_code, latitude, longitude)
    city = {
        NAME: name,
        STATE_CODE: state_code,
        LATITUDE: latitude,
        LONGITUDE: longitude,
    }
    if dbc.create(CITIES_COLLECT, dict(city)) is None:
        return None
    return city


@needs_db
def delete(name: str, state_code: str):
    """
    Delete a city by name and state code.
    Returns True if deleted, False if not found, None if the DB is down.
    """
    return dbc.delete(CITIES_COLLECT, city_filter(name, state_code)) > 0


@needs_db
def exists(name: str, state_code: str):
    """
    Check if a city exists.
    Returns None if the database is down.
    """
    return read_one(name, state_code) is not None


@needs_db
def read_one(name: str, state_code: str):
    """
    Return one city, or None if it is missing or the database is down.
    """
    city = dbc.read_one(CITIES_COLLECT, city_filter(name, state_code))
    if city is not None:
        del city[dbc.MONGO_ID]
    return city
