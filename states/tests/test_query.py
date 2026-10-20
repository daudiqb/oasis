from unittest.mock import patch

import pytest

import states.query as qry

TEST_ST = qry.TEST_STATE


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
    with patch('states.query.is_db_up', return_value=True):
        assert qry.read_one(state_code) == expected


def test_read_one_missing_state():
    with patch('states.query.is_db_up', return_value=True):
        assert qry.read_one('ZZ') is None


def test_read_one_database_down():
    with patch('states.query.is_db_up', return_value=False):
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
def test_create_optional_fields(optional, expected):
    with patch.dict(qry.STATE_TEST_DATA, {}, clear=True):
        with patch('states.query.is_db_up', return_value=True):
            state = qry.create('TS', 'Test State', **optional)
            assert state == {'name': 'Test State', **expected}
            assert qry.read_one('TS') == state


def test_create_invalid_name():
    with patch.dict(qry.STATE_TEST_DATA, {}, clear=True):
        with pytest.raises(ValueError, match='State name must be'):
            qry.create('TS', '')
        assert 'TS' not in qry.STATE_TEST_DATA


def test_query():
    states = qry.read()
    assert isinstance(states, dict)
