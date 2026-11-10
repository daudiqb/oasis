from unittest.mock import patch

import pytest

import states.query as qry

TEST_ST = qry.TEST_STATE


@pytest.fixture(autouse=True)
def mock_connection(state_store):
    with patch('data.db_connect.connect_db') as connect:
        yield connect


@pytest.mark.parametrize('function, args', [
    (qry.read, ()), (qry.read_one, ('AL',)), (qry.exists, ('AL',)),
    (qry.create, ('TS', 'Test State')), (qry.update, ('AL',)),
    (qry.delete, ('AL',)),
])
def test_queries_skip_work_when_database_down(
        function, args, mock_connection, state_store):
    original = {code: state.copy()
                for code, state in state_store.items()}
    with patch('data.db_connect.is_db_up', return_value=False):
        assert function(*args) is None
    mock_connection.assert_not_called()
    assert state_store == original


def test_read_connects_through_shared_decorator(mock_connection, state_store):
    with patch('data.db_connect.is_db_up', return_value=True):
        assert qry.read() == state_store
    assert mock_connection.called


@pytest.mark.parametrize('state_code, expected', [
    ('AL', {
        'population': 4903185,
        'capital': 'Montgomery',
        'area_sq_miles': 52420,
        'name': 'Alabama',
    }),
    ('AK', {
        'population': 731545,
        'capital': 'Juneau',
        'area_sq_miles': 665384,
        'name': 'Alaska',
    }),
])
def test_read_one_existing_state(state_code, expected):
    with patch('data.db_connect.is_db_up', return_value=True):
        assert qry.read_one(state_code) == expected


def test_read_one_missing_state():
    with patch('data.db_connect.is_db_up', return_value=True):
        assert qry.read_one('ZZ') is None


def test_read_one_database_down():
    with patch('data.db_connect.is_db_up', return_value=False):
        assert qry.read_one('AL') is None


@pytest.mark.parametrize('state_code', [None, 12, [], {}, '', 'TOO'])
def test_invalid_state_code_before_duplicate_lookup(state_code):
    with patch('states.query.exists') as mock_exists:
        with pytest.raises(ValueError, match='State code must be'):
            qry.check_valid_state(state_code, 'State')
        mock_exists.assert_not_called()


@pytest.mark.parametrize('name', [None, 12, [], {}, '', '   '])
def test_invalid_state_name(name):
    with patch('states.query.exists') as mock_exists:
        with pytest.raises(ValueError, match='State name must be'):
            qry.check_valid_state('TS', name)
        mock_exists.assert_not_called()


@pytest.mark.parametrize('population', [True, False, -1, 1.5, '10', None])
def test_invalid_population(population):
    with pytest.raises(ValueError, match='Population must be'):
        qry.check_valid_state('TS', 'State', population=population)


@pytest.mark.parametrize('population', [0, 1])
def test_valid_population_boundaries(population):
    assert qry.check_valid_state('TS', 'State', population=population)


def test_duplicate_state_code():
    with pytest.raises(ValueError, match='already exists'):
        qry.check_valid_state('AL', 'Alabama')


def test_check_valid_state_only_required_fields():
    assert qry.check_valid_state('TS', 'Test State')


def test_check_valid_state_all_fields():
    assert qry.check_valid_state(**TEST_ST)


@pytest.mark.parametrize('function', [qry.check_valid_state, qry.create])
@pytest.mark.parametrize('kwargs', [
    {}, {'state_code': 'TS'}, {'name': 'Test State'},
])
def test_required_arguments(function, kwargs):
    with pytest.raises(TypeError):
        function(**kwargs)


@pytest.mark.parametrize('optional, expected', [
    ({}, {'population': 0, 'capital': '', 'area_sq_miles': 0.0}),
    ({'population': 42},
     {'population': 42, 'capital': '', 'area_sq_miles': 0.0}),
    ({'capital': 'Test Capital'},
     {'population': 0, 'capital': 'Test Capital', 'area_sq_miles': 0.0}),
    ({'area_sq_miles': 12.5},
     {'population': 0, 'capital': '', 'area_sq_miles': 12.5}),
    ({'population': 42, 'capital': 'Test Capital', 'area_sq_miles': 12.5},
     {'population': 42, 'capital': 'Test Capital', 'area_sq_miles': 12.5}),
])
def test_create_optional_fields(optional, expected, state_store):
    with patch.dict(state_store, {}, clear=True):
        with patch('data.db_connect.is_db_up', return_value=True):
            state = qry.create('TS', 'Test State', **optional)
            assert state == {'name': 'Test State', **expected}
            assert qry.read_one('TS') == state


def test_create_invalid_name(state_store):
    with patch.dict(state_store, {}, clear=True):
        with pytest.raises(ValueError, match='State name must be'):
            qry.create('TS', '')
        assert 'TS' not in state_store


def test_query():
    states = qry.read()
    assert isinstance(states, dict)


@pytest.fixture
def state_records(state_store):
    records = {'TS': {key: value for key, value in TEST_ST.items()
                      if key != 'state_code'}}
    with patch.dict(state_store, records, clear=True):
        with patch('data.db_connect.is_db_up', return_value=True):
            yield state_store


@pytest.mark.parametrize('changes', [
    {}, {'name': 'New State'}, {'population': 0}, {'capital': ''},
    {'area_sq_miles': 0}, {'area_sq_miles': 12.5},
    {'name': 'New State', 'population': 42,
     'capital': 'New Capital', 'area_sq_miles': 20},
])
def test_update_partial(state_records, changes):
    original = state_records['TS'].copy()
    assert qry.update('TS', **changes) == {**original, **changes}
    assert qry.read_one('TS') == {**original, **changes}
    assert set(state_records) == {'TS'}


@pytest.mark.parametrize('changes', [
    {'name': None}, {'name': ''}, {'name': '  '}, {'name': 12},
    {'population': None}, {'population': True}, {'population': -1},
    {'population': 1.5}, {'population': '10'},
    {'capital': None}, {'capital': 12},
    {'area_sq_miles': None}, {'area_sq_miles': True},
    {'area_sq_miles': -1}, {'area_sq_miles': '10'},
    {'area_sq_miles': float('nan')}, {'area_sq_miles': float('inf')},
    {'unknown': 'value'}, {'name': 'Valid', 'population': -1},
])
def test_update_invalid_is_atomic(state_records, changes):
    original = state_records['TS'].copy()
    with pytest.raises(ValueError):
        qry.update('TS', **changes)
    assert state_records == {'TS': original}


def test_update_cannot_change_state_code(state_records):
    original = state_records['TS'].copy()
    with pytest.raises(TypeError):
        qry.update('TS', **{'state_code': 'NY', 'name': 'New Name'})
    assert state_records == {'TS': original}


def test_update_missing_state(state_records):
    with pytest.raises(ValueError, match='not found'):
        qry.update('ZZ', name='Missing')
    assert 'ZZ' not in state_records


@pytest.mark.parametrize('state_code', [None, 12, [], {}, '', 'TOO'])
def test_update_invalid_state_code(state_records, state_code):
    with pytest.raises(ValueError, match='State code must be'):
        qry.update(state_code, name='New Name')


def test_update_database_down(state_records):
    original = state_records['TS'].copy()
    with patch('data.db_connect.is_db_up', return_value=False):
        assert qry.update('TS', name='New Name') is None
    assert state_records == {'TS': original}


def test_delete_state_without_cities(state_records):
    with patch('states.query.cqry.read', return_value=[{'state_code': 'NY'}]):
        assert qry.delete('TS') is True
    assert 'TS' not in state_records
    assert qry.read_one('TS') is None


def test_delete_state_with_cities(state_records):
    original = state_records.copy()
    with patch('states.query.cqry.read', return_value=[{'state_code': 'TS'}]):
        with pytest.raises(ValueError, match='still has cities'):
            qry.delete('TS')
    assert state_records == original


def test_delete_missing_state(state_records):
    with patch('states.query.cqry.read') as read_cities:
        assert qry.delete('ZZ') is False
    read_cities.assert_not_called()
    assert 'TS' in state_records


@pytest.mark.parametrize('state_code', [None, 12, [], {}, '', 'TOO'])
def test_delete_invalid_state_code(state_records, state_code):
    with pytest.raises(ValueError, match='State code must be'):
        qry.delete(state_code)
    assert 'TS' in state_records


def test_delete_database_down(state_records):
    with patch('data.db_connect.is_db_up', return_value=False):
        with patch('states.query.cqry.read') as read_cities:
            assert qry.delete('TS') is None
    read_cities.assert_not_called()
    assert 'TS' in state_records


def test_delete_city_query_unavailable(state_records):
    with patch('states.query.cqry.read', return_value=None):
        assert qry.delete('TS') is None
    assert 'TS' in state_records


pytestmark = pytest.mark.usefixtures("state_store")
