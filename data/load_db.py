"""Load bundled geographic CSVs without replacing existing records."""
import argparse
import csv
from math import isfinite
from pathlib import Path

import cities.query as cqry
import data.db_connect as dbc
from states.load import DEFAULT_FILE as STATES_FILE, load_states

CITIES_FILE = (Path(__file__).resolve().parent.parent
               / 'cities' / 'raw_data' / 'cities.csv')


def read_cities(file_path=CITIES_FILE):
    """Parse and validate a cities CSV before writing any records."""
    cities = []
    seen = set()
    with open(file_path, newline='', encoding='utf-8') as source:
        reader = csv.DictReader(source)
        fields = {'name', 'state_code', 'latitude', 'longitude'}
        if not fields.issubset(reader.fieldnames or []):
            raise ValueError('Cities CSV needs name, state_code, latitude, '
                             'and longitude columns.')
        for row in reader:
            city = {key: (row.get(key) or '').strip() for key in fields}
            city['latitude'] = float(city['latitude'])
            city['longitude'] = float(city['longitude'])
            cqry.check_valid_city(**city)
            if not all(isfinite(city[key])
                       for key in ('latitude', 'longitude')):
                raise ValueError('City coordinates must be finite.')
            identity = (city['name'], city['state_code'])
            if identity in seen:
                raise ValueError(f'Duplicate city: {identity}.')
            seen.add(identity)
            cities.append(city)
    return cities


def load_database(states_file=STATES_FILE, cities_file=CITIES_FILE):
    """Validate both files, then insert missing states and cities."""
    states = load_states(states_file)
    cities = read_cities(cities_file)
    codes = {state['state_code'] for state in states}
    if any(city['state_code'] not in codes for city in cities):
        raise ValueError('Every city must belong to a state '
                         'in the states CSV.')
    counts = {}
    for collection, records, keys in (
            ('states', states, ('state_code',)),
            ('cities', cities, ('name', 'state_code'))):
        added = 0
        for record in records:
            filt = {key: record[key] for key in keys}
            if dbc.read_one(collection, filt) is None:
                if dbc.create(collection, dict(record)) is None:
                    raise RuntimeError('Database unavailable during import.')
                added += 1
        counts[collection] = added
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--states-csv', type=Path, default=STATES_FILE)
    parser.add_argument('--cities-csv', type=Path, default=CITIES_FILE)
    args = parser.parse_args()
    counts = load_database(args.states_csv, args.cities_csv)
    print(f"Added {counts['states']} states and {counts['cities']} cities.")


if __name__ == '__main__':
    main()
