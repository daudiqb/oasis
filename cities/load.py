"""
Load sample cities into MongoDB so the API server has cities to show.
Run it from the oasis folder with:  python -m cities.load
"""
import cities.query as qry

SAMPLE_CITIES = (
    {qry.NAME: 'Brooklyn', qry.STATE_CODE: 'NY',
     qry.LATITUDE: 40.6782, qry.LONGITUDE: -73.9442},
    {qry.NAME: 'Manhattan', qry.STATE_CODE: 'NY',
     qry.LATITUDE: 40.7831, qry.LONGITUDE: -73.9712},
    {qry.NAME: 'Jersey City', qry.STATE_CODE: 'NJ',
     qry.LATITUDE: 40.7178, qry.LONGITUDE: -74.0431},
)


def load_cities(cities=SAMPLE_CITIES):
    """
    Add each city that is not already in the database.
    Returns how many cities were added, or None if the DB is down.
    """
    added = 0
    for city in cities:
        found = qry.exists(city[qry.NAME], city[qry.STATE_CODE])
        if found is None:
            return None
        if not found:
            qry.create(**city)
            added += 1
    return added


def main():
    added = load_cities()
    if added is None:
        print('Database is down; no cities loaded.')
    else:
        print(f'Added {added} sample cities.')


if __name__ == '__main__':
    main()
