from unittest.mock import patch

import pytest

import cities.load as ld
import cities.query as qry

TEST_CITIES = (
    {qry.NAME: 'Loader Test City', qry.STATE_CODE: 'NY',
     qry.LATITUDE: 40.0, qry.LONGITUDE: -74.0},
)


@pytest.fixture
def test_cities():
    yield TEST_CITIES
    for city in TEST_CITIES:
        qry.delete(city[qry.NAME], city[qry.STATE_CODE])


def test_sample_cities_are_valid():
    for city in ld.SAMPLE_CITIES:
        assert qry.check_valid_city(**city)


def test_load_cities_adds_missing(test_cities):
    assert ld.load_cities(test_cities) == len(test_cities)
    for city in test_cities:
        assert qry.exists(city[qry.NAME], city[qry.STATE_CODE])


def test_load_cities_skips_existing(test_cities):
    ld.load_cities(test_cities)
    assert ld.load_cities(test_cities) == 0


@patch('data.db_connect.is_db_up', return_value=False, autospec=True)
def test_load_cities_db_down(mock_is_db_up):
    assert ld.load_cities(TEST_CITIES) is None


@patch('cities.load.load_cities', return_value=3, autospec=True)
def test_main(mock_load, capsys):
    ld.main()
    assert 'Added 3 sample cities.' in capsys.readouterr().out


@patch('cities.load.load_cities', return_value=None, autospec=True)
def test_main_db_down(mock_load, capsys):
    ld.main()
    assert 'Database is down' in capsys.readouterr().out
