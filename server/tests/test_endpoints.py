from http.client import (
    CREATED,
    BAD_REQUEST,
    NOT_FOUND,
    OK,
    SERVICE_UNAVAILABLE,
)

from unittest.mock import patch

import server.endpoints as ep

TEST_CLIENT = ep.app.test_client()


def test_hello():
    resp = TEST_CLIENT.get(ep.HELLO_EP)
    resp_json = resp.get_json()
    assert ep.HELLO_RESP in resp_json


def test_get_states():
    resp = TEST_CLIENT.get(ep.STATES_EP)
    assert resp.status_code == OK
    resp_json = resp.get_json()
    assert ep.STATES_RESP in resp_json
    assert isinstance(resp_json[ep.STATES_RESP], dict)


@patch('states.query.is_db_up', return_value=False, autospec=True)
def test_get_states_db_unavailable(mock_is_db_up):
    resp = TEST_CLIENT.get(ep.STATES_EP)
    assert resp.status_code == SERVICE_UNAVAILABLE


@patch('server.endpoints.sqry.read_one',
       return_value={'name': 'Alabama', 'capital': 'Montgomery'},
       autospec=True)
@patch('server.endpoints.sqry.exists', return_value=True, autospec=True)
def test_get_state(mock_exists, mock_read_one):
    resp = TEST_CLIENT.get(f'{ep.STATES_EP}/AL')
    assert resp.status_code == OK
    assert resp.get_json() == {ep.STATE_RESP: mock_read_one.return_value}
    mock_exists.assert_called_once_with('AL')
    mock_read_one.assert_called_once_with('AL')


@patch('server.endpoints.sqry.read_one', autospec=True)
@patch('server.endpoints.sqry.exists', return_value=False, autospec=True)
def test_get_state_not_found(mock_exists, mock_read_one):
    resp = TEST_CLIENT.get(f'{ep.STATES_EP}/ZZ')
    assert resp.status_code == NOT_FOUND
    mock_exists.assert_called_once_with('ZZ')
    mock_read_one.assert_not_called()


@patch('server.endpoints.sqry.read_one', autospec=True)
@patch('server.endpoints.sqry.exists', return_value=None, autospec=True)
def test_get_state_db_unavailable(mock_exists, mock_read_one):
    resp = TEST_CLIENT.get(f'{ep.STATES_EP}/AL')
    assert resp.status_code == SERVICE_UNAVAILABLE
    mock_read_one.assert_not_called()


@patch('server.endpoints.sqry.read_one', return_value=None, autospec=True)
@patch('server.endpoints.sqry.exists', return_value=True, autospec=True)
def test_get_state_db_unavailable_during_read(mock_exists, mock_read_one):
    resp = TEST_CLIENT.get(f'{ep.STATES_EP}/AL')
    assert resp.status_code == SERVICE_UNAVAILABLE
    mock_read_one.assert_called_once_with('AL')


def test_get_cities():
    resp = TEST_CLIENT.get(ep.CITIES_EP)
    assert resp.status_code == OK
    resp_json = resp.get_json()
    assert ep.CITIES_RESP in resp_json
    assert isinstance(resp_json[ep.CITIES_RESP], list)


@patch('cities.query.is_db_up', return_value=False, autospec=True)
def test_get_cities_db_unavailable(mock_is_db_up):
    resp = TEST_CLIENT.get(ep.CITIES_EP)
    assert resp.status_code == SERVICE_UNAVAILABLE


FAKE_PR = {'request_id': 'abc', 'listing_id': 'L1', 'buyer_id': 'b1',
           'seller_id': 's1', 'message': '', 'status': 'pending'}


@patch('server.endpoints.prqry.read', return_value=[FAKE_PR], autospec=True)
def test_get_purchase_requests(mock_read):
    resp = TEST_CLIENT.get(f'{ep.PURCHASE_REQUESTS_EP}?buyer_id=b1')
    assert resp.status_code == OK
    assert resp.get_json()[ep.PURCHASE_REQUESTS_RESP] == [FAKE_PR]
    mock_read.assert_called_once_with(buyer_id='b1', seller_id=None,
                                      status=None)


@patch('server.endpoints.prqry.read', return_value=None, autospec=True)
def test_get_purchase_requests_db_unavailable(mock_read):
    resp = TEST_CLIENT.get(ep.PURCHASE_REQUESTS_EP)
    assert resp.status_code == SERVICE_UNAVAILABLE


@patch('server.endpoints.prqry.create', return_value=FAKE_PR, autospec=True)
def test_post_purchase_request(mock_create):
    body = {'listing_id': 'L1', 'buyer_id': 'b1', 'seller_id': 's1'}
    resp = TEST_CLIENT.post(ep.PURCHASE_REQUESTS_EP, json=body)
    assert resp.status_code == CREATED
    assert resp.get_json()[ep.PURCHASE_REQUEST_RESP] == FAKE_PR


@patch('server.endpoints.prqry.create', side_effect=ValueError('bad'),
       autospec=True)
def test_post_purchase_request_invalid(mock_create):
    resp = TEST_CLIENT.post(ep.PURCHASE_REQUESTS_EP, json={})
    assert resp.status_code == BAD_REQUEST


@patch('server.endpoints.prqry.create', return_value=None, autospec=True)
def test_post_purchase_request_db_unavailable(mock_create):
    resp = TEST_CLIENT.post(ep.PURCHASE_REQUESTS_EP, json={})
    assert resp.status_code == SERVICE_UNAVAILABLE


@patch('server.endpoints.prqry.update_status',
       return_value={**FAKE_PR, 'status': 'accepted'}, autospec=True)
@patch('server.endpoints.prqry.exists', return_value=True, autospec=True)
def test_patch_purchase_request(mock_exists, mock_update):
    resp = TEST_CLIENT.patch(f'{ep.PURCHASE_REQUESTS_EP}/abc',
                             json={'status': 'accepted'})
    assert resp.status_code == OK
    assert resp.get_json()[ep.PURCHASE_REQUEST_RESP]['status'] == 'accepted'


@patch('server.endpoints.prqry.exists', return_value=False, autospec=True)
def test_patch_purchase_request_not_found(mock_exists):
    resp = TEST_CLIENT.patch(f'{ep.PURCHASE_REQUESTS_EP}/nope',
                             json={'status': 'accepted'})
    assert resp.status_code == NOT_FOUND


@patch('server.endpoints.prqry.update_status', side_effect=ValueError('bad'),
       autospec=True)
@patch('server.endpoints.prqry.exists', return_value=True, autospec=True)
def test_patch_purchase_request_invalid(mock_exists, mock_update):
    resp = TEST_CLIENT.patch(f'{ep.PURCHASE_REQUESTS_EP}/abc',
                             json={'status': 'banana'})
    assert resp.status_code == BAD_REQUEST


@patch('server.endpoints.prqry.exists', return_value=None, autospec=True)
def test_patch_purchase_request_db_unavailable(mock_exists):
    resp = TEST_CLIENT.patch(f'{ep.PURCHASE_REQUESTS_EP}/abc',
                             json={'status': 'accepted'})
    assert resp.status_code == SERVICE_UNAVAILABLE
