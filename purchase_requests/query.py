"""
Queries on purchase requests, stored in MongoDB through data/db_connect.py.
Each request is one document, identified by its request ID.
"""
import uuid

import data.db_connect as dbc
from data.db_connect import needs_db

COLLECT = 'purchase_requests'

REQUEST_ID = 'request_id'
LISTING_ID = 'listing_id'
BUYER_ID = 'buyer_id'
SELLER_ID = 'seller_id'
MESSAGE = 'message'
STATUS = 'status'

PENDING = 'pending'
ACCEPTED = 'accepted'
REJECTED = 'rejected'
CANCELLED = 'cancelled'
# The statuses a pending request can be changed to:
NEW_STATUSES = (ACCEPTED, REJECTED, CANCELLED)


def _clean(doc: dict) -> dict:
    """
    Return a copy of a request without Mongo's internal ID.
    """
    return {key: val for key, val in doc.items() if key != dbc.MONGO_ID}


@needs_db
def create(listing_id: str, buyer_id: str, seller_id: str,
           message: str = ''):
    """
    Send a new purchase request. It starts out pending.
    Raises ValueError if an ID is missing or the buyer is the seller.
    """
    for name, val in ((LISTING_ID, listing_id), (BUYER_ID, buyer_id),
                      (SELLER_ID, seller_id)):
        if not val:
            raise ValueError(f'{name} is required.')
    if buyer_id == seller_id:
        raise ValueError('You cannot request your own listing.')
    request = {
        REQUEST_ID: uuid.uuid4().hex,
        LISTING_ID: listing_id,
        BUYER_ID: buyer_id,
        SELLER_ID: seller_id,
        MESSAGE: message,
        STATUS: PENDING,
    }
    # Mongo adds an _id to what it stores, so store a copy:
    dbc.create(COLLECT, dict(request))
    return request


@needs_db
def read(buyer_id: str = None, seller_id: str = None, status: str = None):
    """
    Return a list of purchase requests. With no arguments, return all.
    buyer_id gives a buyer's outgoing requests, seller_id a seller's
    incoming ones, and status narrows either by status.
    """
    filters = {BUYER_ID: buyer_id, SELLER_ID: seller_id, STATUS: status}
    filters = {key: val for key, val in filters.items() if val}
    return [req for req in dbc.read(COLLECT)
            if all(req.get(key) == val for key, val in filters.items())]


@needs_db
def exists(request_id: str):
    """
    Check if a purchase request exists.
    """
    return dbc.read_one(COLLECT, {REQUEST_ID: request_id}) is not None


@needs_db
def update_status(request_id: str, status: str):
    """
    Accept, reject, or cancel a pending request. Returns the updated request.
    Raises ValueError for an invalid status, an unknown request, or a
    request that is no longer pending.
    """
    if status not in NEW_STATUSES:
        raise ValueError('Status must be one of: '
                         + ', '.join(NEW_STATUSES) + '.')
    current = dbc.read_one(COLLECT, {REQUEST_ID: request_id})
    if current is None:
        raise ValueError(f'Request {request_id} not found.')
    if current[STATUS] != PENDING:
        raise ValueError('Only pending requests can be changed; '
                         + f'this one is {current[STATUS]}.')
    dbc.update(COLLECT, {REQUEST_ID: request_id}, {STATUS: status})
    return _clean({**current, STATUS: status})
