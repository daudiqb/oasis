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


@patch('server.endpoints.cqry.read_one',
       return_value={'name': 'Brooklyn', 'state_code': 'NY'},
       autospec=True)
@patch('server.endpoints.cqry.exists', return_value=True, autospec=True)
def test_get_city(mock_exists, mock_read_one):
    resp = TEST_CLIENT.get(f'{ep.CITIES_EP}/NY/Brooklyn')
    assert resp.status_code == OK
    assert resp.get_json() == {ep.CITY_RESP: mock_read_one.return_value}
    mock_exists.assert_called_once_with('Brooklyn', 'NY')


@patch('server.endpoints.cqry.read_one', autospec=True)
@patch('server.endpoints.cqry.exists', return_value=False, autospec=True)
def test_get_city_not_found(mock_exists, mock_read_one):
    resp = TEST_CLIENT.get(f'{ep.CITIES_EP}/NY/Nowhere')
    assert resp.status_code == NOT_FOUND
    mock_read_one.assert_not_called()


@patch('server.endpoints.cqry.read_one', autospec=True)
@patch('server.endpoints.cqry.exists', return_value=None, autospec=True)
def test_get_city_db_unavailable(mock_exists, mock_read_one):
    resp = TEST_CLIENT.get(f'{ep.CITIES_EP}/NY/Brooklyn')
    assert resp.status_code == SERVICE_UNAVAILABLE


@patch('server.endpoints.cqry.read_one', return_value=None, autospec=True)
@patch('server.endpoints.cqry.exists', return_value=True, autospec=True)
def test_get_city_db_unavailable_during_read(mock_exists, mock_read_one):
    resp = TEST_CLIENT.get(f'{ep.CITIES_EP}/NY/Brooklyn')
    assert resp.status_code == SERVICE_UNAVAILABLE


FAKE_LISTING = {'listing_id': 'L1', 'title': 'Desk Lamp', 'description': '',
                'price': 15.5, 'city': 'Brooklyn', 'state_code': 'NY',
                'seller_id': 'seller1', 'status': 'available'}


@patch('server.endpoints.lqry.read', return_value=[FAKE_LISTING],
       autospec=True)
def test_get_listings(mock_read):
    resp = TEST_CLIENT.get(ep.LISTINGS_EP)
    assert resp.status_code == OK
    assert resp.get_json()[ep.LISTINGS_RESP] == [FAKE_LISTING]


@patch('server.endpoints.lqry.read', return_value=None, autospec=True)
def test_get_listings_db_unavailable(mock_read):
    resp = TEST_CLIENT.get(ep.LISTINGS_EP)
    assert resp.status_code == SERVICE_UNAVAILABLE


STATE_HEADERS = {ep.USER_EMAIL_HEADER: 'ejc369@nyu.edu'}


def test_post_state():
    with patch.dict(ep.sqry.STATE_TEST_DATA, {}, clear=True):
        with patch('server.endpoints.sec.is_permitted',
                   return_value=True) as allow:
            resp = TEST_CLIENT.post(ep.STATES_EP, headers=STATE_HEADERS,
                                    json={'state_code': 'TS', 'name': 'Test'})
        assert resp.status_code == CREATED
        assert resp.get_json()[ep.STATE_RESP] == {
            'name': 'Test', 'population': 0, 'capital': '',
            'area_sq_miles': 0.0}
        allow.assert_called_once_with('states', 'create', 'ejc369@nyu.edu')
        assert TEST_CLIENT.get(f'{ep.STATES_EP}/TS').status_code == OK


def test_post_state_all_fields():
    with patch.dict(ep.sqry.STATE_TEST_DATA, {}, clear=True):
        resp = TEST_CLIENT.post(ep.STATES_EP, headers=STATE_HEADERS,
                                json=ep.sqry.TEST_STATE)
        assert resp.status_code == CREATED
        expected = dict(ep.sqry.TEST_STATE)
        expected.pop('state_code')
        assert resp.get_json()[ep.STATE_RESP] == expected


def test_post_state_missing_header():
    for headers in ({}, {ep.USER_EMAIL_HEADER: '   '}):
        with patch('server.endpoints.sqry.create') as create:
            with patch('server.endpoints.sec.is_permitted') as allow:
                resp = TEST_CLIENT.post(ep.STATES_EP, headers=headers, json={})
        assert resp.status_code == 401
        allow.assert_not_called()
        create.assert_not_called()


def test_post_state_denied():
    with patch('server.endpoints.sqry.create') as create:
        resp = TEST_CLIENT.post(ep.STATES_EP,
                                headers={ep.USER_EMAIL_HEADER:
                                         'other@nyu.edu'},
                                json={'state_code': 'TS', 'name': 'Test'})
    assert resp.status_code == 403
    create.assert_not_called()


def test_post_state_invalid():
    bodies = [None, [], 'state', {}, {'state_code': 'TS'},
              {'state_code': 'TOO', 'name': 'Test'},
              {'state_code': 'TS', 'name': ' '},
              {'state_code': 'TS', 'name': 'Test', 'population': -1},
              {'state_code': 'AL', 'name': 'Duplicate'}]
    for body in bodies:
        resp = TEST_CLIENT.post(ep.STATES_EP, headers=STATE_HEADERS, json=body)
        assert resp.status_code == BAD_REQUEST


@patch('states.query.is_db_up', return_value=False)
def test_post_state_db_unavailable(mock_db):
    resp = TEST_CLIENT.post(ep.STATES_EP, headers=STATE_HEADERS,
                            json={'state_code': 'TS', 'name': 'Test'})
    assert resp.status_code == SERVICE_UNAVAILABLE


@patch('server.endpoints.sqry.update',
       return_value={'name': 'Updated'}, autospec=True)
@patch('server.endpoints.sqry.exists', return_value=True, autospec=True)
@patch('server.endpoints.sec.is_permitted', return_value=True, autospec=True)
def test_put_state_uses_update(mock_allow, mock_exists, mock_update):
    resp = TEST_CLIENT.put(f'{ep.STATES_EP}/AL', headers=STATE_HEADERS,
                           json={'name': 'Updated'})
    assert resp.status_code == OK
    assert resp.get_json() == {ep.MESSAGE: 'State updated.',
                               ep.STATE_RESP: mock_update.return_value}
    mock_allow.assert_called_once_with('states', 'update', 'ejc369@nyu.edu')
    mock_exists.assert_called_once_with('AL')
    mock_update.assert_called_once_with('AL', name='Updated')


def test_put_state_partial_and_empty():
    original = ep.sqry.STATE_TEST_DATA['AL'].copy()
    with patch.dict(ep.sqry.STATE_TEST_DATA, {'AL': original}, clear=True):
        updates = ({'population': 0}, {},
                   {'capital': '', 'area_sq_miles': 12.5, 'name': 'Updated'})
        for changes in updates:
            expected = {**ep.sqry.STATE_TEST_DATA['AL'], **changes}
            resp = TEST_CLIENT.put(f'{ep.STATES_EP}/AL',
                                   headers=STATE_HEADERS, json=changes)
            assert resp.status_code == OK
            assert resp.get_json()[ep.STATE_RESP] == expected
            assert TEST_CLIENT.get(f'{ep.STATES_EP}/AL').get_json() == {
                ep.STATE_RESP: expected}


def test_put_state_invalid_body():
    original = ep.sqry.STATE_TEST_DATA['AL'].copy()
    for body in (None, [], 'state', {'state_code': 'NY'},
                 {'state_code': 'AL'}, {'unknown': 1}, {'name': ''},
                 {'name': 'Updated', 'population': -1}):
        resp = TEST_CLIENT.put(f'{ep.STATES_EP}/AL', headers=STATE_HEADERS,
                               json=body)
        assert resp.status_code == BAD_REQUEST
        assert ep.sqry.STATE_TEST_DATA['AL'] == original
    resp = TEST_CLIENT.put(f'{ep.STATES_EP}/AL', headers=STATE_HEADERS,
                           data='{broken', content_type='application/json')
    assert resp.status_code == BAD_REQUEST


def test_put_state_missing_or_denied_header():
    for headers, status in (({}, 401),
                            ({ep.USER_EMAIL_HEADER: '  '}, 401),
                            ({ep.USER_EMAIL_HEADER: 'other@nyu.edu'}, 403)):
        with patch('server.endpoints.sqry.update') as update:
            resp = TEST_CLIENT.put(f'{ep.STATES_EP}/AL', headers=headers,
                                   json={'name': 'Updated'})
        assert resp.status_code == status
        update.assert_not_called()


@patch('server.endpoints.sqry.update', autospec=True)
def test_put_state_not_found(mock_update):
    resp = TEST_CLIENT.put(f'{ep.STATES_EP}/ZZ', headers=STATE_HEADERS,
                           json={'name': 'Missing'})
    assert resp.status_code == NOT_FOUND
    mock_update.assert_not_called()


@patch('states.query.is_db_up', return_value=False)
@patch('server.endpoints.sqry.update', autospec=True)
def test_put_state_db_unavailable(mock_update, mock_db):
    resp = TEST_CLIENT.put(f'{ep.STATES_EP}/AL',
                           headers=STATE_HEADERS, json={})
    assert resp.status_code == SERVICE_UNAVAILABLE
    mock_update.assert_not_called()


@patch('server.endpoints.sqry.update', return_value=None, autospec=True)
@patch('server.endpoints.sqry.exists', return_value=True, autospec=True)
def test_put_state_db_unavailable_during_update(mock_exists, mock_update):
    resp = TEST_CLIENT.put(f'{ep.STATES_EP}/AL',
                           headers=STATE_HEADERS, json={})
    assert resp.status_code == SERVICE_UNAVAILABLE
    mock_update.assert_called_once_with('AL')
