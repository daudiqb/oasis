"""
Load a small demo marketplace: listings and purchase requests.
Run `make load_db` first so the cities exist, then `make seed_demo`.
Records that already exist (same ID) are left alone, so it is safe
to run again.
"""
import data.db_connect as dbc
import listings.query as lqry
import purchase_requests.query as prqry


def _listing(num, title, price, city, state_code, seller_id, status):
    return {
        lqry.LISTING_ID: f'demo-listing-{num}',
        lqry.TITLE: title,
        lqry.DESCRIPTION: f'Demo item: {title}.',
        lqry.PRICE: price,
        lqry.CITY: city,
        lqry.STATE_CODE: state_code,
        lqry.SELLER_ID: seller_id,
        lqry.STATUS: status,
    }


def _request(num, listing, buyer_id, message, status):
    return {
        prqry.REQUEST_ID: f'demo-request-{num}',
        prqry.LISTING_ID: listing[lqry.LISTING_ID],
        prqry.BUYER_ID: buyer_id,
        prqry.SELLER_ID: listing[lqry.SELLER_ID],
        prqry.MESSAGE: message,
        prqry.STATUS: status,
    }


LAMP = _listing(1, 'Desk lamp', 15.0, 'Brooklyn', 'NY', 'alice',
                lqry.AVAILABLE)
BIKE = _listing(2, 'Used bike', 120.0, 'Manhattan', 'NY', 'bob',
                lqry.SOLD)
BOOKS = _listing(3, 'Textbook bundle', 40.0, 'Jersey City', 'NJ', 'carol',
                 lqry.AVAILABLE)
CHAIR = _listing(4, 'Office chair', 55.0, 'Brooklyn', 'NY', 'alice',
                 lqry.AVAILABLE)

DEMO_LISTINGS = [LAMP, BIKE, BOOKS, CHAIR]
DEMO_REQUESTS = [
    _request(1, LAMP, 'bob', 'Is it still available?', prqry.PENDING),
    _request(2, LAMP, 'carol', 'Can I pick it up today?', prqry.PENDING),
    _request(3, BIKE, 'alice', 'I would like the bike.', prqry.ACCEPTED),
    _request(4, BOOKS, 'bob', 'Would you take $30?', prqry.REJECTED),
    _request(5, CHAIR, 'carol', 'Never mind, found one.', prqry.CANCELLED),
]


def seed(listings=None, requests=None):
    """
    Validate the demo data, then insert the records that are missing.
    Returns how many records were added to each collection.
    """
    listings = DEMO_LISTINGS if listings is None else listings
    requests = DEMO_REQUESTS if requests is None else requests
    for item in listings:
        lqry.check_valid_listing(item[lqry.TITLE], item[lqry.PRICE],
                                 item[lqry.CITY], item[lqry.STATE_CODE],
                                 item[lqry.SELLER_ID])
    counts = {}
    for collection, key, records in (
            (lqry.COLLECT, lqry.LISTING_ID, listings),
            (prqry.COLLECT, prqry.REQUEST_ID, requests)):
        added = 0
        for record in records:
            if dbc.read_one(collection, {key: record[key]}) is None:
                if dbc.create(collection, dict(record)) is None:
                    raise RuntimeError('Database unavailable while seeding.')
                added += 1
        counts[collection] = added
    return counts


def main():
    counts = seed()
    print(f'Added {counts[lqry.COLLECT]} listings and '
          f'{counts[prqry.COLLECT]} purchase requests.')


if __name__ == '__main__':
    main()
