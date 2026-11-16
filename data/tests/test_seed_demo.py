"""Demo data checks and repeat-run behavior without a live database."""
from unittest.mock import patch

import pytest

import data.seed_demo as sd
import listings.query as lqry
import purchase_requests.query as prqry


def fake_db(stored):
    def find(collection, filt):
        return next((rec for rec in stored.setdefault(collection, [])
                     if all(rec[key] == val for key, val in filt.items())),
                    None)

    def insert(collection, record):
        stored.setdefault(collection, []).append(record)
        return object()

    return (patch.object(sd.dbc, 'read_one', side_effect=find),
            patch.object(sd.dbc, 'create', side_effect=insert))


def test_seed_twice_adds_nothing_the_second_time():
    stored = {}
    find, insert = fake_db(stored)
    with find, insert:
        first = sd.seed()
        second = sd.seed()
    assert first == {lqry.COLLECT: 4, prqry.COLLECT: 5}
    assert second == {lqry.COLLECT: 0, prqry.COLLECT: 0}
    assert len(stored[lqry.COLLECT]) == 4
    assert len(stored[prqry.COLLECT]) == 5


def test_demo_requests_match_their_listings():
    by_id = {item[lqry.LISTING_ID]: item for item in sd.DEMO_LISTINGS}
    for req in sd.DEMO_REQUESTS:
        listing = by_id[req[prqry.LISTING_ID]]
        assert req[prqry.SELLER_ID] == listing[lqry.SELLER_ID]
        assert req[prqry.BUYER_ID] != req[prqry.SELLER_ID]
        assert req[prqry.STATUS] in (prqry.PENDING,) + prqry.NEW_STATUSES
        if req[prqry.STATUS] == prqry.ACCEPTED:
            assert listing[lqry.STATUS] == lqry.SOLD


def test_demo_ids_are_unique():
    listing_ids = [item[lqry.LISTING_ID] for item in sd.DEMO_LISTINGS]
    request_ids = [req[prqry.REQUEST_ID] for req in sd.DEMO_REQUESTS]
    assert len(set(listing_ids)) == len(listing_ids)
    assert len(set(request_ids)) == len(request_ids)


def test_invalid_listing_never_writes():
    bad = [{**sd.LAMP, lqry.PRICE: -1}]
    with patch.object(sd.dbc, 'create') as insert:
        with pytest.raises(ValueError):
            sd.seed(listings=bad, requests=[])
    insert.assert_not_called()


def test_database_down_raises():
    with patch.object(sd.dbc, 'read_one', return_value=None), \
            patch.object(sd.dbc, 'create', return_value=None):
        with pytest.raises(RuntimeError):
            sd.seed()
