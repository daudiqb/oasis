"""Public state field metadata and helper behavior."""
import pytest

import states.fields as fields
import states.query as qry


def test_dictionary_matches_state_record():
    metadata = fields.get_flds()
    assert set(metadata) == set(qry.TEST_STATE)
    assert set(fields.get_fld_names()) == set(metadata)
    assert {name for name, info in metadata.items() if info['required']} == {
        'state_code', 'name'}
    for name, info in metadata.items():
        assert fields.get_disp_name(name) == info['disp_name']
        assert info['type'] in {'string', 'integer', 'number'}
        assert info['description']


def test_optional_defaults_match_creation_defaults():
    metadata = fields.get_flds()
    assert metadata['population']['default'] == 0
    assert metadata['capital']['default'] == ''
    assert metadata['area_sq_miles']['default'] == 0.0


def test_returned_metadata_is_independent():
    metadata = fields.get_flds()
    metadata['name']['disp_name'] = 'Changed'
    metadata.clear()
    names = fields.get_fld_names()
    names.clear()
    assert fields.get_disp_name('name') == 'Name'
    assert 'name' in fields.get_fld_names()


def test_unknown_field_label():
    with pytest.raises(KeyError):
        fields.get_disp_name('unknown')
