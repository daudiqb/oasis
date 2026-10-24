from unittest.mock import patch

import data.db_connect as dbc


@dbc.needs_db
def double(num):
    return num * 2


@patch('data.db_connect.connect_db', autospec=True)
@patch('data.db_connect.is_db_up', return_value=True, autospec=True)
def test_needs_db_runs_function_when_db_up(mock_is_db_up, mock_connect):
    assert double(21) == 42
    mock_connect.assert_called_once_with()


@patch('data.db_connect.connect_db', autospec=True)
@patch('data.db_connect.is_db_up', return_value=False, autospec=True)
def test_needs_db_returns_none_when_db_down(mock_is_db_up, mock_connect):
    assert double(21) is None
    mock_connect.assert_not_called()


def test_needs_db_keeps_function_name():
    assert double.__name__ == 'double'
