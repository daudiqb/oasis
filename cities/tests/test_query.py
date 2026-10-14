from unittest.mock import patch

import cities.query as qry


def test_read():
    cities = qry.read()
    assert isinstance(cities, list)
    assert len(cities) > 0
    assert qry.NAME in cities[0]


@patch('cities.query.is_db_up', return_value=False, autospec=True)
def test_read_db_down(mock_is_db_up):
    assert qry.read() is None
