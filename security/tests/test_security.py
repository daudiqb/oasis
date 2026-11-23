import pytest

import security.security as sec
import users.query as uqry

# conftest.py turns this off for every test; the DB tests turn it back on.
REAL_READ_FROM_DB = sec.read_from_db


def test_read():
    recs = sec.read()
    assert isinstance(recs, dict)
    for feature in recs:
        assert isinstance(feature, str)
        assert len(feature) > 0


def test_state_create_permissions():
    assert sec.is_permitted(sec.STATES, sec.CREATE, 'ejc369@nyu.edu')
    assert not sec.is_permitted(sec.STATES, sec.CREATE, 'other@nyu.edu')
    assert not sec.is_permitted(sec.STATES, sec.CREATE, '')
    assert sec.is_permitted(sec.STATES, sec.DELETE, 'ejc369@nyu.edu')
    assert not sec.is_permitted(sec.STATES, sec.DELETE, 'other@nyu.edu')
    assert not sec.is_permitted(sec.STATES, sec.DELETE, '')


def test_unconfigured_feature_is_open():
    assert sec.is_permitted('unconfigured', sec.READ, '')


@pytest.fixture
def login_users(monkeypatch):
    """
    Fake the users DB: ejc369@nyu.edu has the auth code 'good-code'.
    """
    stored = {'ejc369@nyu.edu': uqry._hash('good-code')}

    def fake_read_one(collection, filt, **kwargs):
        email = filt[uqry.EMAIL]
        if email in stored:
            return {uqry.EMAIL: email, uqry.AUTH_HASH: stored[email]}

    monkeypatch.setattr(uqry.dbc, 'is_db_up', lambda: True)
    monkeypatch.setattr(uqry.dbc, 'connect_db', lambda: None)
    monkeypatch.setattr(uqry.dbc, 'read_one', fake_read_one)


def test_required_security_checks(login_users):
    assert not sec.is_permitted(sec.PEOPLE, sec.CREATE, 'ejc369@nyu.edu')
    assert sec.is_permitted(sec.PEOPLE, sec.CREATE, 'ejc369@nyu.edu',
                            auth_code='good-code')


def test_login_flag_alone_is_not_enough(login_users):
    assert not sec.is_permitted(sec.PEOPLE, sec.CREATE,
                                'ejc369@nyu.edu', login=True)


def test_wrong_auth_code_is_refused(login_users):
    assert not sec.is_permitted(sec.PEOPLE, sec.CREATE, 'ejc369@nyu.edu',
                                auth_code='bad-code')
    assert not sec.is_permitted(sec.PEOPLE, sec.CREATE, 'ejc369@nyu.edu',
                                auth_code='')


def test_good_code_for_unlisted_user_is_refused(login_users):
    assert not sec.is_permitted(sec.PEOPLE, sec.CREATE, 'other@nyu.edu',
                                auth_code='good-code')


def test_login_refused_when_db_is_down(monkeypatch):
    monkeypatch.setattr(uqry.dbc, 'is_db_up', lambda: False)
    assert not sec.is_permitted(sec.PEOPLE, sec.CREATE, 'ejc369@nyu.edu',
                                auth_code='good-code')


def test_other_checks_still_use_flags(monkeypatch):
    recs = {'vault': {sec.READ: {sec.USER_LIST: ['a@nyu.edu'],
                                 sec.CHECKS: {'dual_factor': True}}}}
    monkeypatch.setattr(sec, 'security_recs', recs)
    assert not sec.is_permitted('vault', sec.READ, 'a@nyu.edu')
    assert sec.is_permitted('vault', sec.READ, 'a@nyu.edu', dual_factor=True)


def test_read_uses_db_records(monkeypatch):
    docs = [{'feature': 'vault',
             sec.READ: {sec.USER_LIST: ['a@nyu.edu']}}]
    monkeypatch.setattr(sec, 'read_from_db', REAL_READ_FROM_DB)
    monkeypatch.setattr(sec.dbc, 'read', lambda collection, **kw: docs)
    assert sec.read() == {'vault': {sec.READ: {sec.USER_LIST:
                                               ['a@nyu.edu']}}}


@pytest.mark.parametrize('db_result', [None, []])
def test_read_falls_back_when_db_is_empty_or_down(monkeypatch, db_result):
    monkeypatch.setattr(sec, 'read_from_db', REAL_READ_FROM_DB)
    monkeypatch.setattr(sec.dbc, 'read', lambda collection, **kw: db_result)
    assert sec.read() == sec.temp_recs


def test_read_falls_back_when_db_errors(monkeypatch):
    def boom(collection, **kwargs):
        raise RuntimeError('no server')

    monkeypatch.setattr(sec, 'read_from_db', REAL_READ_FROM_DB)
    monkeypatch.setattr(sec.dbc, 'read', boom)
    assert sec.read() == sec.temp_recs


def test_state_update_permissions():
    assert sec.is_permitted(sec.STATES, sec.UPDATE, 'ejc369@nyu.edu')
    assert not sec.is_permitted(sec.STATES, sec.UPDATE, 'other@nyu.edu')


def test_city_create_permissions():
    assert sec.is_permitted(sec.CITIES, sec.CREATE, 'ejc369@nyu.edu')
    assert not sec.is_permitted(sec.CITIES, sec.CREATE, 'other@nyu.edu')


def test_city_update_permissions():
    assert sec.is_permitted(sec.CITIES, sec.UPDATE, 'ejc369@nyu.edu')
    assert not sec.is_permitted(sec.CITIES, sec.UPDATE, 'other@nyu.edu')


def test_city_delete_permissions():
    assert sec.is_permitted(sec.CITIES, sec.DELETE, 'ejc369@nyu.edu')
    assert not sec.is_permitted(sec.CITIES, sec.DELETE, 'other@nyu.edu')


def test_listing_create_permissions():
    assert sec.is_permitted(sec.LISTINGS, sec.CREATE, 'ejc369@nyu.edu')
    assert not sec.is_permitted(sec.LISTINGS, sec.CREATE, 'other@nyu.edu')


def test_listing_update_permissions():
    assert sec.is_permitted(sec.LISTINGS, sec.UPDATE, 'ejc369@nyu.edu')
    assert not sec.is_permitted(sec.LISTINGS, sec.UPDATE, 'other@nyu.edu')


def test_listing_delete_permissions():
    assert sec.is_permitted(sec.LISTINGS, sec.DELETE, 'ejc369@nyu.edu')
    assert not sec.is_permitted(sec.LISTINGS, sec.DELETE, 'other@nyu.edu')
