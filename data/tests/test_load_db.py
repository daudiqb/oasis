"""CSV import validation and repeat-run behavior without a live database."""
from unittest.mock import patch

import pytest

import data.load_db as ld


def test_load_bundled_files_twice():
    stored = {'states': [], 'cities': []}

    def find(collection, filt):
        return next((record for record in stored[collection]
                     if all(record[key] == value
                            for key, value in filt.items())), None)

    def insert(collection, record):
        stored[collection].append(record)
        return object()

    with patch.object(ld.dbc, 'read_one', side_effect=find), \
            patch.object(ld.dbc, 'create', side_effect=insert):
        assert ld.load_database() == {'states': 50, 'cities': 3}
        stored['states'][0]['name'] = 'Existing name'
        assert ld.load_database() == {'states': 0, 'cities': 0}
    assert stored['states'][0]['name'] == 'Existing name'
    assert {city['state_code'] for city in stored['cities']} == {'NY', 'NJ'}


@pytest.mark.parametrize('contents', [
    'wrong,columns\n',
    'name,state_code,latitude,longitude\nCity,NY,invalid,-74\n',
    'name,state_code,latitude,longitude\nCity,NY,91,-74\n',
    'name,state_code,latitude,longitude\nCity,NY,nan,-74\n',
    'name,state_code,latitude,longitude\nCity,ZZ,40,-74\n',
    'name,state_code,latitude,longitude\nCity,NY,40,-74\nCity,NY,40,-74\n',
])
def test_invalid_cities_never_write(tmp_path, contents):
    source = tmp_path / 'cities.csv'
    source.write_text(contents)
    with patch.object(ld.dbc, 'create') as insert:
        with pytest.raises(ValueError):
            ld.load_database(cities_file=source)
    insert.assert_not_called()


def test_missing_states_never_write(tmp_path):
    with patch.object(ld.dbc, 'create') as insert:
        with pytest.raises(FileNotFoundError):
            ld.load_database(states_file=tmp_path / 'missing.csv')
    insert.assert_not_called()


def test_database_unavailable():
    with patch.object(ld.dbc, 'read_one', return_value=None), \
            patch.object(ld.dbc, 'create', return_value=None):
        with pytest.raises(RuntimeError, match='unavailable'):
            ld.load_database()


def test_bundled_paths_independent_of_working_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert len(ld.read_cities()) == 3
