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
            qry.check_valid_state(state_code, 0, 'Capital', 1, 'State')
        mock_exists.assert_not_called()


@pytest.mark.parametrize('population', [True, False, -1, 1.5, '10', None])
def test_invalid_population(population):
    with pytest.raises(ValueError, match='Population must be'):
        qry.check_valid_state('TS', population, 'Capital', 1, 'State')


@pytest.mark.parametrize('population', [0, 1])
def test_valid_population_boundaries(population):
    assert qry.check_valid_state('TS', population, 'Capital', 1, 'State')


def test_duplicate_state_code():
    with pytest.raises(ValueError, match='already exists'):
        qry.check_valid_state('AL', 0, 'Capital', 1, 'State')


def test_check_valid_state():
    ret = qry.check_valid_state(TEST_ST['state_code'],
                                TEST_ST['population'],
                                TEST_ST['capital'],
                                TEST_ST['area_sq_miles'],
                                TEST_ST['name'])
    assert ret


def test_check_valid_state_bad_pop():
    with pytest.raises(ValueError):
        qry.check_valid_state(TEST_ST['state_code'],
                              -23423,
                              TEST_ST['capital'],
                              TEST_ST['area_sq_miles'],
                              TEST_ST['name'])


def test_check_valid_state_code_too_short():
    with pytest.raises(ValueError):
        qry.check_valid_state('',
                              TEST_ST['population'],
                              TEST_ST['capital'],
                              TEST_ST['area_sq_miles'],
                              TEST_ST['name'])


def test_check_valid_state_code_too_long():
    with pytest.raises(ValueError):
        qry.check_valid_state('X' * qry.STATE_CODE_LEN * 2,
                              TEST_ST['population'],
                              TEST_ST['capital'],
                              TEST_ST['area_sq_miles'],
                              TEST_ST['name'])


def test_query():
    states = qry.read()
    assert isinstance(states, dict)
