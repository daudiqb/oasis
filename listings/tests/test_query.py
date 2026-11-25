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

    def fake_update(collection, filt, changes, **kwargs):
        for doc in store:
            if all(doc.get(key) == val for key, val in filt.items()):
                doc.update(changes)

    def fake_delete(collection, filt, **kwargs):
        before = len(store)
        store[:] = [doc for doc in store
                    if not all(doc.get(key) == val
                               for key, val in filt.items())]
        return before - len(store)

    # Every test city exists unless a test says otherwise.
    monkeypatch.setattr(qry.cqry, 'exists', lambda name, code: True)
    monkeypatch.setattr(qry.dbc, 'read_one', fake_read_one)
    monkeypatch.setattr(qry.dbc, 'delete', fake_delete)
    monkeypatch.setattr(qry.dbc, 'update', fake_update)
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


@pytest.fixture
def three_listings(fake_db):
    qry.create(*VALID, description='Barely used')
    qry.create('Mini Fridge', 40, 'Jersey City', 'NJ', 'seller2')
    qry.create('Standing Desk', 120, 'Manhattan', 'NY', 'seller3')
    return fake_db


def titles(listings):
    return sorted(lst[qry.TITLE] for lst in listings)


def test_read_filter_city(three_listings):
    assert titles(qry.read(city='Brooklyn')) == ['Desk Lamp']


def test_read_filter_state(three_listings):
    assert titles(qry.read(state_code='NY')) == ['Desk Lamp',
                                                 'Standing Desk']


def test_read_search_ignores_case(three_listings):
    assert titles(qry.read(search='DESK')) == ['Desk Lamp', 'Standing Desk']


def test_read_search_description(three_listings):
    assert titles(qry.read(search='barely')) == ['Desk Lamp']


def test_read_filters_combine(three_listings):
    assert titles(qry.read(state_code='NY', search='desk',
                           city='Manhattan')) == ['Standing Desk']


def test_read_filter_no_match(three_listings):
    assert qry.read(state_code='CA') == []


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


def test_update_details(fake_db):
    listing = qry.create(*VALID)
    updated = qry.update(listing[qry.LISTING_ID], title='Floor Lamp',
                         price=20)
    assert updated[qry.TITLE] == 'Floor Lamp'
    assert updated[qry.PRICE] == 20
    assert qry.read_one(listing[qry.LISTING_ID])[qry.TITLE] == 'Floor Lamp'


@pytest.mark.parametrize('status', qry.STATUSES)
def test_update_status(fake_db, status):
    listing = qry.create(*VALID)
    updated = qry.update(listing[qry.LISTING_ID], status=status)
    assert updated[qry.STATUS] == status


def test_update_leaves_omitted_fields(fake_db):
    listing = qry.create(*VALID, description='Barely used')
    updated = qry.update(listing[qry.LISTING_ID], price=20)
    assert updated[qry.TITLE] == listing[qry.TITLE]
    assert updated[qry.DESCRIPTION] == 'Barely used'
    assert updated[qry.SELLER_ID] == listing[qry.SELLER_ID]


def test_update_empty_returns_current(fake_db):
    listing = qry.create(*VALID)
    assert qry.update(listing[qry.LISTING_ID]) == listing


@pytest.mark.parametrize('changes', [
    {'listing_id': 'other'},
    {'seller_id': 'someone_else'},
    {'nonsense': 1},
])
def test_update_rejects_protected_fields(fake_db, changes):
    listing = qry.create(*VALID)
    with pytest.raises(ValueError, match='can be updated'):
        qry.update(listing[qry.LISTING_ID], **changes)


@pytest.mark.parametrize('changes', [
    {'price': -1},
    {'title': ''},
    {'state_code': 'NYC'},
    {'status': 'banana'},
    {'description': 5},
])
def test_update_invalid_values(fake_db, changes):
    listing = qry.create(*VALID)
    with pytest.raises(ValueError):
        qry.update(listing[qry.LISTING_ID], **changes)


def test_update_not_found(fake_db):
    with pytest.raises(ValueError, match='not found'):
        qry.update('nope', price=1)


def test_delete(fake_db):
    listing = qry.create(*VALID)
    assert qry.delete(listing[qry.LISTING_ID]) is True
    assert fake_db == []
    assert qry.exists(listing[qry.LISTING_ID]) is False


def test_delete_missing(fake_db):
    assert qry.delete('nope') is False


def test_delete_leaves_other_listings(fake_db):
    keep = qry.create(*VALID)
    drop = qry.create('Mini Fridge', 40, 'Jersey City', 'NJ', 'seller2')
    qry.delete(drop[qry.LISTING_ID])
    assert [doc[qry.LISTING_ID] for doc in fake_db] == [keep[qry.LISTING_ID]]


def test_create_unknown_city(fake_db, monkeypatch):
    monkeypatch.setattr(qry.cqry, 'exists', lambda name, code: False)
    with pytest.raises(ValueError, match='not found'):
        qry.create(*VALID)
    assert fake_db == []


def test_create_checks_city_and_state(fake_db, monkeypatch):
    seen = []
    monkeypatch.setattr(qry.cqry, 'exists',
                        lambda name, code: seen.append((name, code)) or True)
    qry.create(*VALID)
    assert seen == [('Brooklyn', 'NY')]


def test_create_city_check_db_down(fake_db, monkeypatch):
    monkeypatch.setattr(qry.cqry, 'exists', lambda name, code: None)
    assert qry.create(*VALID) is None
    assert fake_db == []


def test_update_to_unknown_city(fake_db, monkeypatch):
    listing = qry.create(*VALID)
    monkeypatch.setattr(qry.cqry, 'exists', lambda name, code: False)
    with pytest.raises(ValueError, match='not found'):
        qry.update(listing[qry.LISTING_ID], city='Atlantis')
    assert qry.read_one(listing[qry.LISTING_ID])[qry.CITY] == 'Brooklyn'


def test_update_to_known_city(fake_db):
    listing = qry.create(*VALID)
    updated = qry.update(listing[qry.LISTING_ID], city='Jersey City',
                         state_code='NJ')
    assert updated[qry.CITY] == 'Jersey City'
    assert qry.read_one(listing[qry.LISTING_ID])[qry.STATE_CODE] == 'NJ'


def test_update_other_fields_skips_city_check(fake_db, monkeypatch):
    listing = qry.create(*VALID)
    monkeypatch.setattr(qry.cqry, 'exists', lambda name, code: False)
    assert qry.update(listing[qry.LISTING_ID], price=5)[qry.PRICE] == 5


def test_update_city_check_db_down(fake_db, monkeypatch):
    listing = qry.create(*VALID)
    monkeypatch.setattr(qry.cqry, 'exists', lambda name, code: None)
    assert qry.update(listing[qry.LISTING_ID], state_code='NJ') is None


@patch('data.db_connect.is_db_up', return_value=False, autospec=True)
def test_db_down(mock_is_db_up):
    assert qry.create(*VALID) is None
    assert qry.read() is None
    assert qry.exists('x') is None
    assert qry.read_one('x') is None
    assert qry.update('x', price=1) is None
    assert qry.delete('x') is None
