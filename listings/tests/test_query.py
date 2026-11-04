from unittest.mock import patch

import pytest

import listings.query as qry

VALID = ('Desk Lamp', 15.5, 'Brooklyn', 'NY', 'seller1')


def test_check_valid_listing():
    assert qry.check_valid_listing(*VALID) is True


@pytest.mark.parametrize('title, price, city, state_code, seller_id', [
    ('', 15.5, 'Brooklyn', 'NY', 'seller1'),
    ('Desk Lamp', -1, 'Brooklyn', 'NY', 'seller1'),
    ('Desk Lamp', 'free', 'Brooklyn', 'NY', 'seller1'),
    ('Desk Lamp', 15.5, '', 'NY', 'seller1'),
    ('Desk Lamp', 15.5, 'Brooklyn', 'NYC', 'seller1'),
    ('Desk Lamp', 15.5, 'Brooklyn', 'NY', ''),
])
def test_check_valid_listing_invalid(title, price, city, state_code,
                                     seller_id):
    with pytest.raises(ValueError):
        qry.check_valid_listing(title, price, city, state_code, seller_id)


@pytest.fixture
def fake_db(monkeypatch):
    """
    Replace the database calls with an in-memory list,
    so these tests do not need MongoDB running.
    """
    store = []

    def fake_read_one(collection, filt, **kwargs):
        return next((dict(doc) for doc in store
                     if all(doc.get(key) == val
                            for key, val in filt.items())), None)

    monkeypatch.setattr(qry.dbc, 'read_one', fake_read_one)
    monkeypatch.setattr(qry.dbc, 'is_db_up', lambda: True)
    monkeypatch.setattr(qry.dbc, 'connect_db', lambda: None)
    monkeypatch.setattr(qry.dbc, 'create',
                        lambda collection, doc, **kwargs: store.append(doc))
    monkeypatch.setattr(qry.dbc, 'read',
                        lambda collection, **kwargs: [dict(d) for d in store])
    return store


def test_create(fake_db):
    listing = qry.create(*VALID)
    assert listing[qry.STATUS] == qry.AVAILABLE
    assert listing[qry.TITLE] == 'Desk Lamp'
    assert listing[qry.DESCRIPTION] == ''
    assert len(fake_db) == 1


def test_create_with_description(fake_db):
    listing = qry.create(*VALID, description='Barely used')
    assert listing[qry.DESCRIPTION] == 'Barely used'


def test_create_invalid_does_not_store(fake_db):
    with pytest.raises(ValueError):
        qry.create('', 15.5, 'Brooklyn', 'NY', 'seller1')
    assert fake_db == []


def test_read(fake_db):
    qry.create(*VALID)
    qry.create('Mini Fridge', 40, 'Jersey City', 'NJ', 'seller2')
    assert len(qry.read()) == 2


def test_exists(fake_db):
    listing = qry.create(*VALID)
    assert qry.exists(listing[qry.LISTING_ID]) is True


def test_exists_false(fake_db):
    assert qry.exists('nope') is False


def test_read_one(fake_db):
    listing = qry.create(*VALID)
    found = qry.read_one(listing[qry.LISTING_ID])
    assert found[qry.TITLE] == listing[qry.TITLE]
    assert found[qry.LISTING_ID] == listing[qry.LISTING_ID]


def test_read_one_strips_mongo_id(fake_db):
    listing = qry.create(*VALID)
    fake_db[0][qry.dbc.MONGO_ID] = 'some-mongo-id'
    assert qry.dbc.MONGO_ID not in qry.read_one(listing[qry.LISTING_ID])


def test_read_one_missing(fake_db):
    assert qry.read_one('nope') is None


@patch('data.db_connect.is_db_up', return_value=False, autospec=True)
def test_db_down(mock_is_db_up):
    assert qry.create(*VALID) is None
    assert qry.read() is None
    assert qry.exists('x') is None
    assert qry.read_one('x') is None
