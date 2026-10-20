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
