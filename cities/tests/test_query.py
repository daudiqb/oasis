from unittest.mock import patch

import pytest

import cities.query as qry

TEST_CITY = qry.TEST_CITY


def test_read():
    cities = qry.read()
    assert isinstance(cities, list)
    assert len(cities) > 0
    assert qry.NAME in cities[0]


@patch('cities.query.is_db_up', return_value=False, autospec=True)
def test_read_db_down(mock_is_db_up):
    assert qry.read() is None


def test_check_valid_city():
    assert qry.check_valid_city(TEST_CITY[qry.NAME],
                                TEST_CITY[qry.STATE_CODE],
                                TEST_CITY[qry.LATITUDE],
                                TEST_CITY[qry.LONGITUDE])


def test_check_valid_city_blank_name():
    with pytest.raises(ValueError):
        qry.check_valid_city('',
                             TEST_CITY[qry.STATE_CODE],
                             TEST_CITY[qry.LATITUDE],
                             TEST_CITY[qry.LONGITUDE])


def test_check_valid_city_state_code_too_long():
    with pytest.raises(ValueError):
        qry.check_valid_city(TEST_CITY[qry.NAME],
                             'X' * (qry.STATE_CODE_LEN * 2),
                             TEST_CITY[qry.LATITUDE],
                             TEST_CITY[qry.LONGITUDE])


def test_check_valid_city_bad_latitude():
    with pytest.raises(ValueError):
        qry.check_valid_city(TEST_CITY[qry.NAME],
                             TEST_CITY[qry.STATE_CODE],
                             qry.MAX_LATITUDE + 1,
                             TEST_CITY[qry.LONGITUDE])


def test_check_valid_city_bad_longitude():
    with pytest.raises(ValueError):
        qry.check_valid_city(TEST_CITY[qry.NAME],
                             TEST_CITY[qry.STATE_CODE],
                             TEST_CITY[qry.LATITUDE],
                             qry.MIN_LONGITUDE - 1)
        