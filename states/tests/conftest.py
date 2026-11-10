"""Fixtures for tests that exercise the real MongoDB connection."""
import pytest
from pymongo import timeout
from pymongo.errors import ServerSelectionTimeoutError

import data.db_connect as dbc
import states.query as qry


@pytest.fixture
def temp_state():
    """Create a temporary state in MongoDB and remove it after each test."""
    code = qry.TEST_STATE['state_code']
    try:
        with timeout(1):
            existing = qry.read_one(code)
    except ServerSelectionTimeoutError:
        pytest.skip('MongoDB is unavailable; start local MongoDB '
                    'to run this test.')
    if existing is not None:
        pytest.fail(f'Temporary state {code} already exists; '
                    'refusing to replace it.')
    state = qry.create(**qry.TEST_STATE)
    try:
        yield code, state
    finally:
        # Direct cleanup also works when the test already deleted the state.
        dbc.delete(qry.COLLECT, {qry.STATE_CODE: code})
