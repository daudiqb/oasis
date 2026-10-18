from unittest.mock import patch

import pytest

import purchase_requests.query as qry


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

    monkeypatch.setattr(qry, 'is_db_up', lambda: True)
    monkeypatch.setattr(qry.dbc, 'connect_db', lambda: None)
    monkeypatch.setattr(qry.dbc, 'create',
                        lambda collection, doc, **kwargs: store.append(doc))
    monkeypatch.setattr(qry.dbc, 'read',
                        lambda collection, **kwargs: [dict(d) for d in store])
    monkeypatch.setattr(qry.dbc, 'read_one', fake_read_one)
    monkeypatch.setattr(qry.dbc, 'update', fake_update)
    return store


def test_create(fake_db):
    req = qry.create('L1', 'buyer1', 'seller1', 'Is it still available?')
    assert req[qry.STATUS] == qry.PENDING
    assert req[qry.LISTING_ID] == 'L1'
    assert req[qry.MESSAGE] == 'Is it still available?'
    assert qry.exists(req[qry.REQUEST_ID])
    assert len(fake_db) == 1


@pytest.mark.parametrize('listing_id, buyer_id, seller_id',
                         [('', 'b', 's'), ('L1', None, 's'), ('L1', 'b', '')])
def test_create_missing_id(fake_db, listing_id, buyer_id, seller_id):
    with pytest.raises(ValueError, match='required'):
        qry.create(listing_id, buyer_id, seller_id)
    assert fake_db == []


def test_create_own_listing(fake_db):
    with pytest.raises(ValueError, match='own listing'):
        qry.create('L1', 'same', 'same')


def test_read_filters(fake_db):
    qry.create('L1', 'buyer1', 'seller1')
    qry.create('L2', 'buyer2', 'seller1')
    qry.create('L3', 'buyer1', 'seller2')
    assert len(qry.read()) == 3
    assert len(qry.read(buyer_id='buyer1')) == 2
    assert len(qry.read(seller_id='seller1')) == 2
    assert len(qry.read(buyer_id='buyer1', seller_id='seller2')) == 1
    assert qry.read(status=qry.ACCEPTED) == []


def test_exists_false(fake_db):
    assert qry.exists('nope') is False


@pytest.mark.parametrize('status', qry.NEW_STATUSES)
def test_update_status(fake_db, status):
    req = qry.create('L1', 'buyer1', 'seller1')
    updated = qry.update_status(req[qry.REQUEST_ID], status)
    assert updated[qry.STATUS] == status
    assert qry.read(status=status)[0][qry.REQUEST_ID] == req[qry.REQUEST_ID]


def test_update_status_invalid(fake_db):
    req = qry.create('L1', 'buyer1', 'seller1')
    with pytest.raises(ValueError, match='Status must be'):
        qry.update_status(req[qry.REQUEST_ID], 'banana')


def test_update_status_only_when_pending(fake_db):
    req = qry.create('L1', 'buyer1', 'seller1')
    qry.update_status(req[qry.REQUEST_ID], qry.REJECTED)
    with pytest.raises(ValueError, match='Only pending'):
        qry.update_status(req[qry.REQUEST_ID], qry.ACCEPTED)


def test_update_status_not_found(fake_db):
    with pytest.raises(ValueError, match='not found'):
        qry.update_status('nope', qry.ACCEPTED)


@patch('purchase_requests.query.is_db_up', return_value=False, autospec=True)
def test_db_down(mock_is_db_up):
    assert qry.create('L1', 'buyer1', 'seller1') is None
    assert qry.read() is None
    assert qry.exists('x') is None
    assert qry.update_status('x', qry.ACCEPTED) is None
