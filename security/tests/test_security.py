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
    assert not sec.is_permitted(sec.STATES, sec.DELETE, 'ejc369@nyu.edu')


def test_unconfigured_feature_is_open():
    assert sec.is_permitted('unconfigured', sec.READ, '')


def test_required_security_checks():
    assert not sec.is_permitted(sec.PEOPLE, sec.CREATE, 'ejc369@nyu.edu')
    assert sec.is_permitted(sec.PEOPLE, sec.CREATE,
                            'ejc369@nyu.edu', login=True)
