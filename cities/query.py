"""
Query functions for the cities collection
"""
from data.db_connect import is_db_up

NAME = 'name'
STATE_CODE = 'state_code'
LATITUDE = 'latitude'
LONGITUDE = 'longitude'

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
