#!/usr/bin/env python3

from math import isfinite

from data.db_connect import is_db_up


STATE_CODE_LEN = 2

TEST_STATE = {
    "state_code": "TS",
    "population": 1000000,
    "capital": "Test Capital",
    "area_sq_miles": 50000,
    "name": 'Test State',
}

STATE_TEST_DATA = {
    "AL": {
        "population": 4903185,
        "capital": "Montgomery",
        "area_sq_miles": 52420,
        "name": 'Alabama',
    },
    "AK": {
        "population": 731545,
        "capital": "Juneau",
        "area_sq_miles": 665384,
        "name": 'Alaska',
    },
    "AZ": {
        "population": 7278717,
        "capital": "Phoenix",
        "area_sq_miles": 113990,
        "name": 'Arizona',
    },
    # Add more states as needed
}


def read():
    """
    Return a list of all states in the test data.
    """
    if not is_db_up():
        print("Database is down.")
        return None
    return STATE_TEST_DATA


def read_one(state_code: str):
    """
    Return state details, or None if the code is missing or the DB is down.
    """
    if not is_db_up():
        print("Database is down.")
        return None
    return STATE_TEST_DATA.get(state_code)


def exists(state_code: str):
    """
    Check if a state exists in the test data.
    """
    if not is_db_up():
        print("Database is down.")
        return None
    return state_code in STATE_TEST_DATA


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


def create(state_code: str, name: str, population: int = 0,
           capital: str = '', area_sq_miles: float = 0.0):
    """
    Create a state; omitted population/capital/area default to 0/empty/0.0.
    """
    # check_valid_state raises ValueError if the state is invalid, so we don't
    # need to check the return value
    check_valid_state(state_code, name, population, capital, area_sq_miles)
    if not is_db_up():
        print("Database is down.")
        return None
    STATE_TEST_DATA[state_code] = {
        "population": population,
        "capital": capital,
        "area_sq_miles": area_sq_miles,
        "name": name,
    }
    return STATE_TEST_DATA[state_code]


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
    if not is_db_up():
        return None
    current = STATE_TEST_DATA.get(state_code)
    if current is None:
        raise ValueError(f'State {state_code} not found.')
    updated = {**current, **changes}
    if not isinstance(updated['name'], str) or not updated['name'].strip():
        raise ValueError('State name must be a non-empty string.')
    population = updated['population']
    if (not isinstance(population, int) or isinstance(population, bool)
            or population < 0):
        raise ValueError('Population must be a non-negative integer.')
    if not isinstance(updated['capital'], str):
        raise ValueError('Capital must be a string.')
    area = updated['area_sq_miles']
    if (not isinstance(area, (int, float)) or isinstance(area, bool)
            or area < 0 or not isfinite(area)):
        raise ValueError('Area must be a finite non-negative number.')
    STATE_TEST_DATA[state_code] = updated
    return updated


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
