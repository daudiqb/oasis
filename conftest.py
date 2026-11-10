"""Isolated state storage for query and API unit tests."""
from copy import deepcopy
from unittest.mock import patch

import pytest

import data.db_connect as dbc


@pytest.fixture
def state_store():
    records = {
        'AL': {'name': 'Alabama', 'population': 4903185,
               'capital': 'Montgomery', 'area_sq_miles': 52420},
        'AK': {'name': 'Alaska', 'population': 731545,
               'capital': 'Juneau', 'area_sq_miles': 665384},
    }

    def read(collection):
        assert collection == 'states'
        return [dict(state_code=code, **deepcopy(details))
                for code, details in records.items()]

    def read_one(collection, filt):
        assert collection == 'states'
        code = filt['state_code']
        if code in records:
            return dict(state_code=code, _id='mongo-id',
                        **deepcopy(records[code]))

    def create(collection, doc):
        assert collection == 'states'
        stored = dict(doc)
        code = stored.pop('state_code')
        records[code] = deepcopy(stored)
        doc['_id'] = 'mongo-id'

    def update(collection, filt, changes):
        assert collection == 'states'
        records[filt['state_code']].update(deepcopy(changes))

    def delete(collection, filt):
        assert collection == 'states'
        return int(records.pop(filt['state_code'], None) is not None)

    with patch.object(dbc, 'connect_db'), \
            patch.object(dbc, 'read', side_effect=read), \
            patch.object(dbc, 'read_one', side_effect=read_one), \
            patch.object(dbc, 'create', side_effect=create), \
            patch.object(dbc, 'update', side_effect=update), \
            patch.object(dbc, 'delete', side_effect=delete), \
            patch('states.query.cqry.read', new=lambda: []):
        yield records
