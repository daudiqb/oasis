import pytest

import users.query as qry


@pytest.fixture
def fake_db(monkeypatch):
    """
    Replace the database calls with an in-memory list,
    so these tests do not need MongoDB running.
    """
    store = []

    def matches(doc, filt):
        return all(doc.get(key) == val for key, val in filt.items())

    def fake_read_one(collection, filt, **kwargs):
        return next((dict(doc) for doc in store if matches(doc, filt)), None)

    def fake_update(collection, filt, update_dict, **kwargs):
        for doc in store:
            if matches(doc, filt):
                doc.update(update_dict)

    monkeypatch.setattr(qry.dbc, 'is_db_up', lambda: True)
    monkeypatch.setattr(qry.dbc, 'connect_db', lambda: None)
    monkeypatch.setattr(qry.dbc, 'create',
                        lambda collection, doc, **kwargs: store.append(doc))
    monkeypatch.setattr(qry.dbc, 'read',
                        lambda collection, **kwargs: [dict(d) for d in store])
    monkeypatch.setattr(qry.dbc, 'read_one', fake_read_one)
    monkeypatch.setattr(qry.dbc, 'update', fake_update)
    return store


def test_create(fake_db):
    user = qry.create('Ann@NYU.edu ', ' Ann ')
    assert user[qry.EMAIL] == 'ann@nyu.edu'
    assert user[qry.NAME] == 'Ann'
    assert len(user[qry.AUTH_CODE]) == 2 * qry.CODE_BYTES
    assert qry.exists('ann@nyu.edu')


def test_code_is_stored_hashed(fake_db):
    user = qry.create('ann@nyu.edu', 'Ann')
    stored = fake_db[0]
    assert user[qry.AUTH_CODE] not in stored.values()
    assert stored[qry.AUTH_HASH] == qry._hash(user[qry.AUTH_CODE])


@pytest.mark.parametrize('email, name', [('', 'Ann'), (None, 'Ann'),
                                         ('no-at-sign', 'Ann'),
                                         ('a@nyu.edu', ''),
                                         ('a@nyu.edu', '  ')])
def test_create_bad_input(fake_db, email, name):
    with pytest.raises(ValueError):
        qry.create(email, name)
    assert fake_db == []


def test_create_duplicate(fake_db):
    qry.create('ann@nyu.edu', 'Ann')
    with pytest.raises(ValueError, match='already registered'):
        qry.create('ANN@nyu.edu', 'Other')
    assert len(fake_db) == 1


def test_read_hides_auth_data(fake_db):
    qry.create('ann@nyu.edu', 'Ann')
    assert qry.read_one('ann@nyu.edu') == {qry.EMAIL: 'ann@nyu.edu',
                                           qry.NAME: 'Ann'}
    assert qry.read() == [{qry.EMAIL: 'ann@nyu.edu', qry.NAME: 'Ann'}]
    assert qry.read_one('nobody@nyu.edu') is None
    assert not qry.exists('nobody@nyu.edu')


def test_verify_auth_code(fake_db):
    user = qry.create('ann@nyu.edu', 'Ann')
    assert qry.verify_auth_code('ann@nyu.edu', user[qry.AUTH_CODE]) is True
    assert qry.verify_auth_code('ANN@nyu.edu', user[qry.AUTH_CODE]) is True
    assert qry.verify_auth_code('ann@nyu.edu', 'wrong') is False
    assert qry.verify_auth_code('ann@nyu.edu', '') is False
    assert qry.verify_auth_code('ann@nyu.edu', None) is False
    assert qry.verify_auth_code('nobody@nyu.edu',
                                user[qry.AUTH_CODE]) is False


def test_new_auth_code_replaces_old(fake_db):
    user = qry.create('ann@nyu.edu', 'Ann')
    fresh = qry.new_auth_code('ann@nyu.edu')
    assert fresh != user[qry.AUTH_CODE]
    assert qry.verify_auth_code('ann@nyu.edu', fresh) is True
    assert qry.verify_auth_code('ann@nyu.edu', user[qry.AUTH_CODE]) is False


def test_new_auth_code_unknown_user(fake_db):
    with pytest.raises(ValueError, match='No such user'):
        qry.new_auth_code('nobody@nyu.edu')


def test_db_down(monkeypatch):
    monkeypatch.setattr(qry.dbc, 'is_db_up', lambda: False)
    assert qry.create('ann@nyu.edu', 'Ann') is None
    assert qry.verify_auth_code('ann@nyu.edu', 'x') is None
