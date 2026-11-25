from unittest.mock import patch

import pytest

import cities.query as qry

TEST_CITY = qry.TEST_CITY


@pytest.fixture
def temp_city():
    city = qry.create(TEST_CITY[qry.NAME],
                      TEST_CITY[qry.STATE_CODE],
                      TEST_CITY[qry.LATITUDE],
                      TEST_CITY[qry.LONGITUDE])
    yield city
    qry.delete(city[qry.NAME], city[qry.STATE_CODE])


def test_read(temp_city):
    cities = qry.read()
    assert isinstance(cities, list)
    assert temp_city in cities


@patch('data.db_connect.is_db_up', return_value=False, autospec=True)
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


def test_create(temp_city):
    assert temp_city in qry.read()


def test_delete():
    city = qry.create(TEST_CITY[qry.NAME],
                      TEST_CITY[qry.STATE_CODE],
                      TEST_CITY[qry.LATITUDE],
                      TEST_CITY[qry.LONGITUDE])
    assert qry.delete(city[qry.NAME], city[qry.STATE_CODE])
    assert city not in qry.read()


def test_delete_missing_city():
    assert qry.delete('No Such City', 'ZZ') is False


def test_create_duplicate(temp_city):
    with pytest.raises(ValueError):
        qry.create(TEST_CITY[qry.NAME],
                   TEST_CITY[qry.STATE_CODE],
                   TEST_CITY[qry.LATITUDE],
                   TEST_CITY[qry.LONGITUDE])


@patch('data.db_connect.is_db_up', return_value=False, autospec=True)
def test_create_db_down(mock_is_db_up):
    assert qry.create(TEST_CITY[qry.NAME],
                      TEST_CITY[qry.STATE_CODE],
                      TEST_CITY[qry.LATITUDE],
                      TEST_CITY[qry.LONGITUDE]) is None


@patch('cities.query.dbc.create', return_value=None, autospec=True)
def test_create_db_down_during_write(mock_create):
    assert qry.create(TEST_CITY[qry.NAME],
                      TEST_CITY[qry.STATE_CODE],
                      TEST_CITY[qry.LATITUDE],
                      TEST_CITY[qry.LONGITUDE]) is None


@patch('data.db_connect.is_db_up', return_value=False, autospec=True)
def test_delete_db_down(mock_is_db_up):
    assert qry.delete(TEST_CITY[qry.NAME], TEST_CITY[qry.STATE_CODE]) is None


def test_exists(temp_city):
    assert qry.exists(temp_city[qry.NAME], temp_city[qry.STATE_CODE])


def test_exists_missing_city():
    assert qry.exists('No Such City', 'ZZ') is False


@patch('data.db_connect.is_db_up', return_value=False, autospec=True)
def test_exists_db_down(mock_is_db_up):
    assert qry.exists(TEST_CITY[qry.NAME], TEST_CITY[qry.STATE_CODE]) is None


def test_read_one(temp_city):
    city = qry.read_one(temp_city[qry.NAME], temp_city[qry.STATE_CODE])
    assert city == temp_city


def test_read_one_missing_city():
    assert qry.read_one('No Such City', 'ZZ') is None


@patch('data.db_connect.is_db_up', return_value=False, autospec=True)
def test_read_one_db_down(mock_is_db_up):
    assert qry.read_one(TEST_CITY[qry.NAME],
                        TEST_CITY[qry.STATE_CODE]) is None


def test_update(temp_city):
    updated = qry.update(temp_city[qry.NAME], temp_city[qry.STATE_CODE],
                         latitude=41.0)
    assert updated[qry.LATITUDE] == 41.0
    assert updated[qry.LONGITUDE] == temp_city[qry.LONGITUDE]
    assert qry.read_one(temp_city[qry.NAME],
                        temp_city[qry.STATE_CODE]) == updated


def test_update_no_changes(temp_city):
    assert qry.update(temp_city[qry.NAME],
                      temp_city[qry.STATE_CODE]) == temp_city


@pytest.mark.parametrize('changes', [
    {qry.NAME: 'New Name'},
    {qry.STATE_CODE: 'NJ'},
    {qry.LATITUDE: qry.MAX_LATITUDE + 1},
    {qry.LONGITUDE: 'west'},
])
def test_update_invalid(temp_city, changes):
    with pytest.raises(ValueError):
        qry.update(temp_city[qry.NAME], temp_city[qry.STATE_CODE], **changes)
    assert qry.read_one(temp_city[qry.NAME],
                        temp_city[qry.STATE_CODE]) == temp_city


def test_update_missing_city():
    with pytest.raises(ValueError):
        qry.update('No Such City', 'ZZ', latitude=41.0)


@patch('data.db_connect.is_db_up', return_value=False, autospec=True)
def test_update_db_down(mock_is_db_up):
    assert qry.update(TEST_CITY[qry.NAME], TEST_CITY[qry.STATE_CODE],
                      latitude=41.0) is None
