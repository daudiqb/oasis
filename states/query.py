#!/usr/bin/env python3

from math import isfinite

from data.db_connect import needs_db
import cities.query as cqry
import data.db_connect as dbc


STATE_CODE_LEN = 2

TEST_STATE = {
    "state_code": "TS",
    "population": 1000000,
    "capital": "Test Capital",
    "area_sq_miles": 50000,
    "name": 'Test State',
}

COLLECT = 'states'
STATE_CODE = 'state_code'


def _details(record):
    """Keep storage keys out of the public state details."""
    return {key: value for key, value in record.items()
            if key not in {STATE_CODE, dbc.MONGO_ID}}


@needs_db
def read():
    """
    Return state details keyed by state code from MongoDB.
    """
    return {record[STATE_CODE]: _details(record)
            for record in dbc.read(COLLECT)}


@needs_db
def read_one(state_code: str):
    """
    Return state details, or None if the code is missing or the DB is down.
    """
    record = dbc.read_one(COLLECT, {STATE_CODE: state_code})
    return None if record is None else _details(record)


@needs_db
def exists(state_code: str):
    """
    Check if a state exists in MongoDB.
    """
    return dbc.read_one(COLLECT, {STATE_CODE: state_code}) is not None


def check_valid_state(state_code: str, name: str, population: int = 0,
                      capital: str = '', area_sq_miles: float = 0.0):
    """Validate required code/name and optional state details."""
    if not isinstance(state_code, str) or len(state_code) != STATE_CODE_LEN:
        raise ValueError(f"State code must be {STATE_CODE_LEN}-letter string.")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("State name must be a non-empty string.")
    if (not isinstance(population, int) or isinstance(population, bool)
            or population < 0):
        raise ValueError("Population must be a non-negative integer.")
    if exists(state_code):
        raise ValueError(f"State code {state_code} already exists.")
    return True


@needs_db
def create(state_code: str, name: str, population: int = 0,
           capital: str = '', area_sq_miles: float = 0.0):
    """
    Create a state; omitted population/capital/area default to 0/empty/0.0.
    """
    # check_valid_state raises ValueError if the state is invalid, so we don't
    # need to check the return value
    check_valid_state(state_code, name, population, capital, area_sq_miles)
    state = {
        "population": population,
        "capital": capital,
        "area_sq_miles": area_sq_miles,
        "name": name,
    }
    dbc.create(COLLECT, {STATE_CODE: state_code, **state})
    return state


@needs_db
def update(state_code: str, **changes):
    """Partially update a state without changing its code.

    Return the updated record, or None if the database is down.
    Raise ValueError for a missing state or invalid fields. Omitted fields
    remain unchanged; an empty update returns the existing record.
    """
    if not isinstance(state_code, str) or len(state_code) != STATE_CODE_LEN:
        raise ValueError(f"State code must be {STATE_CODE_LEN}-letter string.")
    allowed = {'name', 'population', 'capital', 'area_sq_miles'}
    if changes.keys() - allowed:
        raise ValueError('Only name, population, capital, and area_sq_miles '
                         'can be updated; state code cannot be changed.')
    current = read_one(state_code)
    if current is None:
        raise ValueError(f'State {state_code} not found.')
    updated = {**current, **changes}
    if not isinstance(updated['name'], str) or not updated['name'].strip():
        raise ValueError('State name must be a non-empty string.')
    population = updated.get('population', 0)
    if (not isinstance(population, int) or isinstance(population, bool)
            or population < 0):
        raise ValueError('Population must be a non-negative integer.')
    if not isinstance(updated.get('capital', ''), str):
        raise ValueError('Capital must be a string.')
    area = updated.get('area_sq_miles', 0.0)
    if (not isinstance(area, (int, float)) or isinstance(area, bool)
            or area < 0 or not isfinite(area)):
        raise ValueError('Area must be a finite non-negative number.')
    if changes:
        dbc.update(COLLECT, {STATE_CODE: state_code}, changes)
    return updated


@needs_db
def delete(state_code: str):
    """Delete a state only when it has no cities.

    Return True if deleted, False if missing, or None if either query is
    unavailable. Raise ValueError for an invalid code or remaining cities.
    """
    if not isinstance(state_code, str) or len(state_code) != STATE_CODE_LEN:
        raise ValueError(f"State code must be {STATE_CODE_LEN}-letter string.")
    if not exists(state_code):
        return False
    cities = cqry.read()
    if cities is None:
        return None
    if any(city[cqry.STATE_CODE] == state_code for city in cities):
        raise ValueError(f'State {state_code} still has cities.')
    return bool(dbc.delete(COLLECT, {STATE_CODE: state_code}))


def main():
    states = read()
    for state, data in states.items():
        print(f"State: {state}")
        print(f"Population: {data['population']}")
        print(f"Capital: {data['capital']}")
        print(f"Area (sq miles): {data['area_sq_miles']}")
        print("-" * 40)


if __name__ == "__main__":
    main()
