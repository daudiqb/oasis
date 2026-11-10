"""Integration tests: these use MongoDB, without the state_store mock."""
import pytest

import states.query as qry


def test_read_temporary_state(temp_state):
    code, state = temp_state
    assert qry.exists(code) is True
    assert qry.read_one(code) == state
    assert qry.read()[code] == state


def test_update_temporary_state(temp_state):
    code, state = temp_state
    expected = {**state, 'name': 'Updated Test State'}
    assert qry.update(code, name=expected['name']) == expected
    assert qry.read_one(code) == expected


def test_delete_temporary_state(temp_state):
    code, _ = temp_state
    assert qry.delete(code) is True
    assert qry.read_one(code) is None
    assert qry.delete(code) is False


def test_duplicate_temporary_state(temp_state):
    code, state = temp_state
    with pytest.raises(ValueError, match='already exists'):
        qry.create(**qry.TEST_STATE)
    assert qry.read_one(code) == state
