"""State cache behavior using isolated MongoDB helper mocks."""
from unittest.mock import patch

import pytest

import states.query as qry

pytestmark = pytest.mark.usefixtures('state_store')


def test_reads_share_one_database_load():
    with patch.object(qry.dbc, 'read', wraps=qry.dbc.read) as read:
        assert 'AL' in qry.read()
        assert qry.read_one('AL')['name'] == 'Alabama'
        assert qry.exists('AL') is True
        assert qry.exists('ZZ') is False
        assert qry.read_one('ZZ') is None
    read.assert_called_once_with(qry.COLLECT)


def test_empty_collection_is_cached(state_store):
    state_store.clear()
    with patch.object(qry.dbc, 'read', wraps=qry.dbc.read) as read:
        assert qry.read() == {}
        assert qry.read() == {}
        assert qry.exists('AL') is False
    read.assert_called_once_with(qry.COLLECT)


def test_returned_records_cannot_change_cache():
    states = qry.read()
    states['AL']['name'] = 'Changed'
    states.clear()
    state = qry.read_one('AL')
    state['name'] = 'Changed again'
    assert qry.read_one('AL')['name'] == 'Alabama'


def test_external_writes_require_explicit_refresh(state_store):
    qry.read()
    state_store['AL']['name'] = 'Changed outside query module'
    assert qry.read_one('AL')['name'] == 'Alabama'
    qry.clear_cache()
    assert qry.read_one('AL')['name'] == 'Changed outside query module'


@pytest.mark.parametrize('operation', ['create', 'update', 'delete'])
def test_successful_writes_refresh_cache(operation):
    qry.read()
    with patch.object(qry.dbc, 'read', wraps=qry.dbc.read) as read:
        if operation == 'create':
            qry.create('TS', 'Test State')
            assert qry.read_one('TS')['name'] == 'Test State'
        elif operation == 'update':
            qry.update('AL', name='New Name')
            assert qry.read_one('AL')['name'] == 'New Name'
        else:
            assert qry.delete('AL') is True
            assert qry.exists('AL') is False
    read.assert_called_once_with(qry.COLLECT)


@pytest.mark.parametrize('operation', ['create', 'update', 'delete'])
def test_unavailable_write_keeps_cached_records(operation):
    original = qry.read()
    with patch.object(qry.dbc, operation, return_value=None):
        if operation == 'create':
            assert qry.create('TS', 'Test State') is None
        elif operation == 'update':
            assert qry.update('AL', name='New Name') is None
        else:
            assert qry.delete('AL') is None
    with patch.object(qry.dbc, 'read') as read:
        assert qry.read() == original
    read.assert_not_called()


def test_failed_load_can_be_retried():
    with patch.object(qry.dbc, 'read', return_value=None):
        assert qry.read() is None
        assert qry.exists('AL') is None
    assert qry.read_one('AL')['name'] == 'Alabama'


def test_warm_cache_preserves_database_down_behavior():
    qry.read()
    with patch.object(qry.dbc, 'is_db_up', return_value=False):
        assert qry.read() is None
        assert qry.read_one('AL') is None
        assert qry.exists('AL') is None


def test_rejected_update_preserves_cache():
    original = qry.read()
    with patch.object(qry.dbc, 'read') as read:
        with pytest.raises(ValueError):
            qry.update('AL', name='')
        assert qry.read() == original
    read.assert_not_called()
