"""
Query functions for the listings collection, stored in MongoDB
through data/db_connect.py.
"""
import uuid
from functools import wraps

import data.db_connect as dbc
from data.db_connect import is_db_up

COLLECT = 'listings'

LISTING_ID = 'listing_id'
TITLE = 'title'
DESCRIPTION = 'description'
PRICE = 'price'
CITY = 'city'
STATE_CODE = 'state_code'
SELLER_ID = 'seller_id'
STATUS = 'status'

AVAILABLE = 'available'
PENDING = 'pending'
SOLD = 'sold'

STATE_CODE_LEN = 2


def check_valid_listing(title: str, price: float, city: str,
                        state_code: str, seller_id: str):
    """
    Raise ValueError if any listing field is invalid.
    Returns True if the listing is valid.
    """
    if not isinstance(title, str) or not title.strip():
        raise ValueError('Title must be a non-empty string.')
    if not isinstance(price, (int, float)) or isinstance(price, bool) \
            or price < 0:
        raise ValueError('Price must be a non-negative number.')
    if not isinstance(city, str) or not city.strip():
        raise ValueError('City must be a non-empty string.')
    if not isinstance(state_code, str) or len(state_code) != STATE_CODE_LEN:
        raise ValueError(f'State code must be {STATE_CODE_LEN} letters.')
    if not isinstance(seller_id, str) or not seller_id.strip():
        raise ValueError('Seller ID must be a non-empty string.')
    return True


def needs_db(fn):
    """
    Decorate any function that needs the database: if the DB is down,
    return None instead of calling the function; otherwise make sure
    we are connected, then call it.

    TODO: switch to the shared data.db_connect.needs_db once Anish's
    A1 lands, so every module uses one copy.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not is_db_up():
            print('Database is down.')
            return None
        dbc.connect_db()
        return fn(*args, **kwargs)
    return wrapper


@needs_db
def create(title: str, price: float, city: str, state_code: str,
           seller_id: str, description: str = ''):
    """
    Create a new listing and return it. It starts out available.
    Raises ValueError if any field is invalid.
    """
    check_valid_listing(title, price, city, state_code, seller_id)
    listing = {
        LISTING_ID: uuid.uuid4().hex,
        TITLE: title,
        DESCRIPTION: description,
        PRICE: price,
        CITY: city,
        STATE_CODE: state_code,
        SELLER_ID: seller_id,
        STATUS: AVAILABLE,
    }
    # Mongo adds an _id to what it stores, so store a copy:
    dbc.create(COLLECT, dict(listing))
    return listing


@needs_db
def read():
    """
    Return a list of all listings.
    """
    return dbc.read(COLLECT)
