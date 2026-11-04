from unittest.mock import patch

import pytest

from states.load import load_states, main
import states.query as qry


EXPECTED_CODES = set('AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA '
                     'ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK '
                     'OR PA RI SC SD TN TX UT VT VA WA WV WI WY'.split())


def test_load_all_50_states():
    states = load_states()
    assert len(states) == 50
    assert {state['state_code'] for state in states} == EXPECTED_CODES
    assert next(state for state in states if state['state_code'] == 'NY') == {
        'state_code': 'NY', 'name': 'New York', 'population': 0,
        'capital': '', 'area_sq_miles': 0.0,
    }


def test_query_contains_all_states():
    assert set(qry.STATE_TEST_DATA) == EXPECTED_CODES
    assert qry.STATE_TEST_DATA['TX']['name'] == 'Texas'
    assert qry.STATE_TEST_DATA['AL']['capital'] == 'Montgomery'


def test_default_path_independent_of_working_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert len(load_states()) == 50


def test_custom_csv(tmp_path):
    source = tmp_path / 'states.csv'
    source.write_text('Abbrev,State\nNY,New York\nDC,District of Columbia\n'
                      'PR,Puerto Rico\n', encoding='utf-8')
    assert load_states(source) == [{
        'state_code': 'NY', 'name': 'New York', 'population': 0,
        'capital': '', 'area_sq_miles': 0.0,
    }]


@pytest.mark.parametrize('contents', [
    '', 'Code,Name\nNY,New York\n', 'Abbrev,State\nN,New York\n',
    'Abbrev,State\nny,New York\n', 'Abbrev,State\nNY,\n',
    'Abbrev,State\nNY\n', 'Abbrev,State\nNY,New York\nNY,Duplicate\n',
])
def test_invalid_csv(tmp_path, contents):
    source = tmp_path / 'states.csv'
    source.write_text(contents, encoding='utf-8')
    with pytest.raises(ValueError):
        load_states(source)


def test_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_states(tmp_path / 'missing.csv')


def test_main_defaults_to_bundled_csv(capsys):
    with patch('sys.argv', ['load.py']):
        main()
    assert len(capsys.readouterr().out.splitlines()) == 50
