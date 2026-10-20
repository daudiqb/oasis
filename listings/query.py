"""
Query functions for the listings collection.
"""

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
