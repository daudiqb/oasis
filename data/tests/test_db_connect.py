from unittest.mock import patch

import certifi

import pytest

from pymongo.errors import ServerSelectionTimeoutError

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


@pytest.mark.parametrize('fn, args', [
    (dbc.create, ('cities', {})),
    (dbc.read_one, ('cities', {})),
    (dbc.delete, ('cities', {})),
    (dbc.update, ('cities', {}, {})),
    (dbc.read, ('cities',)),
    (dbc.fetch_all_as_dict, ('name', 'cities')),
])
@patch('data.db_connect.is_db_up', return_value=True, autospec=True)
@patch('data.db_connect.connect_db', autospec=True)
@patch('data.db_connect.client')
def test_db_calls_connect_first(mock_client, mock_connect, mock_is_db_up,
                                fn, args):
    mock_client[dbc.SE_DB]['cities'].find.return_value = []
    fn(*args)
    mock_connect.assert_called_once_with()


@patch('data.db_connect.connect_db', autospec=True)
@patch('data.db_connect.is_db_up', return_value=False, autospec=True)
def test_db_call_returns_none_when_db_down(mock_is_db_up, mock_connect):
    assert dbc.read('cities') is None
    mock_connect.assert_not_called()


@pytest.fixture
def no_client(monkeypatch):
    """
    Start each connect_db() test with no saved connection.
    """
    monkeypatch.setattr(dbc, 'client', None)


@patch('data.db_connect.pm.MongoClient', autospec=True)
def test_connect_db_local(mock_client, no_client, monkeypatch):
    monkeypatch.setenv('CLOUD_MONGO', dbc.LOCAL)
    dbc.connect_db()
    mock_client.assert_called_once_with()


@patch('data.db_connect.pm.MongoClient', autospec=True)
def test_connect_db_cloud(mock_client, no_client, monkeypatch):
    monkeypatch.setenv('CLOUD_MONGO', dbc.CLOUD)
    monkeypatch.setenv('MONGO_PASSWD', 'test-password')
    dbc.connect_db()
    uri = mock_client.call_args.args[0]
    assert uri.startswith(dbc.CLOUD_PROTOCOL)
    assert f'{dbc.CLOUD_USER}:test-password@{dbc.CLOUD_URL}' in uri
    assert mock_client.call_args.kwargs['tlsCAFile'] == certifi.where()


@patch('data.db_connect.pm.MongoClient', autospec=True)
def test_connect_db_cloud_needs_password(mock_client, no_client,
                                         monkeypatch):
    monkeypatch.setenv('CLOUD_MONGO', dbc.CLOUD)
    monkeypatch.delenv('MONGO_PASSWD', raising=False)
    with pytest.raises(ValueError):
        dbc.connect_db()
    mock_client.assert_not_called()


@patch('data.db_connect.connect_db', autospec=True)
def test_is_db_up(mock_connect):
    assert dbc.is_db_up() is True
    mock_connect.return_value.admin.command.assert_called_once_with('ping')


@patch('data.db_connect.connect_db', autospec=True)
def test_is_db_up_when_db_down(mock_connect):
    mock_connect.return_value.admin.command.side_effect = \
        ServerSelectionTimeoutError('no server')
    assert dbc.is_db_up() is False
