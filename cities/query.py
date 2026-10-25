"""
Query functions for the cities collection
"""
from data.db_connect import is_db_up

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


CITY_TEST_DATA = [
    {NAME: 'Brooklyn', STATE_CODE: 'NY',
     LATITUDE: 40.6782, LONGITUDE: -73.9442},
    {NAME: 'Manhattan', STATE_CODE: 'NY',
     LATITUDE: 40.7831, LONGITUDE: -73.9712},
    {NAME: 'Jersey City', STATE_CODE: 'NJ',
     LATITUDE: 40.7178, LONGITUDE: -74.0431},
]


def read():
    """
    Return a list of all cities.
    Returns None if the database is down.
    """
    if not is_db_up():
        return None
    return CITY_TEST_DATA


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
    Add a new city and return it.
    Returns None if the database is down.
    """
    check_valid_city(name, state_code, latitude, longitude)
    if not is_db_up():
        return None
    city = {
        NAME: name,
        STATE_CODE: state_code,
        LATITUDE: latitude,
        LONGITUDE: longitude,
    }
    CITY_TEST_DATA.append(city)
    return city


def delete(name: str, state_code: str):
    """
    Delete a city by name and state code.
    Returns True if deleted, False if not found, None if the DB is down.
    """
    if not is_db_up():
        return None
    for city in CITY_TEST_DATA:
        if city[NAME] == name and city[STATE_CODE] == state_code:
            CITY_TEST_DATA.remove(city)
            return True
    return False


def exists(name: str, state_code: str):
    """
    Check if a city exists.
    Returns None if the database is down.
    """
    if not is_db_up():
        return None
    return any(city[NAME] == name and city[STATE_CODE] == state_code
               for city in CITY_TEST_DATA)


def read_one(name: str, state_code: str):
    """
    Return one city, or None if it is missing or the database is down.
    """
    if not is_db_up():
        return None
    for city in CITY_TEST_DATA:
        if city[NAME] == name and city[STATE_CODE] == state_code:
            return city
    return None
