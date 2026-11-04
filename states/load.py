#!/usr/bin/env python3
"""Load the 50 U.S. states from the bundled CSV."""

import csv
from pathlib import Path
import sys


DEFAULT_FILE = Path(__file__).resolve().parent / 'raw_data' / 'states.csv'
NON_STATE_CODES = {'DC', 'PR'}


def load_states(file_path=DEFAULT_FILE):
    """Return state records using the query schema, excluding DC and PR.

    The CSV supplies codes and names; other state fields use create() defaults.
    File errors and invalid or duplicate records raise without returning a
    partial result.
    """
    states = []
    seen = set()
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        if not {'Abbrev', 'State'}.issubset(reader.fieldnames or []):
            raise ValueError('CSV must contain Abbrev and State columns.')
        for row in reader:
            code = (row.get('Abbrev') or '').strip()
            name = (row.get('State') or '').strip()
            if code in NON_STATE_CODES:
                continue
            if (len(code) != 2 or not code.isascii() or not code.isalpha()
                    or not code.isupper() or not name):
                raise ValueError('Each state needs a two-letter code '
                                 'and name.')
            if code in seen:
                raise ValueError(f'Duplicate state code: {code}.')
            seen.add(code)
            states.append({
                'state_code': code, 'name': name, 'population': 0,
                'capital': '', 'area_sq_miles': 0.0,
            })
    return states


def main():
    """Print normalized states from the bundled CSV or an optional path."""
    file_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_FILE
    for state in load_states(file_path):
        print(state)


if __name__ == '__main__':
    main()
