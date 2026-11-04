import security.security as sec


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


def test_required_security_checks():
    assert not sec.is_permitted(sec.PEOPLE, sec.CREATE, 'ejc369@nyu.edu')
    assert sec.is_permitted(sec.PEOPLE, sec.CREATE,
                            'ejc369@nyu.edu', login=True)


def test_state_update_permissions():
    assert sec.is_permitted(sec.STATES, sec.UPDATE, 'ejc369@nyu.edu')
    assert not sec.is_permitted(sec.STATES, sec.UPDATE, 'other@nyu.edu')


def test_city_create_permissions():
    assert sec.is_permitted(sec.CITIES, sec.CREATE, 'ejc369@nyu.edu')
    assert not sec.is_permitted(sec.CITIES, sec.CREATE, 'other@nyu.edu')


def test_listing_create_permissions():
    assert sec.is_permitted(sec.LISTINGS, sec.CREATE, 'ejc369@nyu.edu')
    assert not sec.is_permitted(sec.LISTINGS, sec.CREATE, 'other@nyu.edu')
    assert not sec.is_permitted(sec.LISTINGS, sec.DELETE, 'ejc369@nyu.edu')
