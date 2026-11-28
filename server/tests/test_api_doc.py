"""
Keeps docs/api.md honest: every endpoint in the Swagger spec has its own
section there, and each section mentions every status code the spec lists.
"""
import re
from pathlib import Path

import pytest

import server.endpoints as ep

DOC = Path(__file__).resolve().parents[2] / 'docs' / 'api.md'
HTTP_METHODS = ('get', 'post', 'put', 'patch', 'delete')
HEADING = re.compile(r'^### `([A-Z]+) (\S+)`\s*$', re.MULTILINE)


@pytest.fixture(scope='module')
def spec():
    return ep.app.test_client().get('/swagger.json').get_json()


@pytest.fixture(scope='module')
def sections():
    """Map (METHOD, path) to the text of its '### `METHOD /path`' section."""
    text = DOC.read_text()
    found = {}
    heads = list(HEADING.finditer(text))
    for i, head in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        next_h2 = text.find('\n## ', head.end())
        if next_h2 != -1:
            end = min(end, next_h2)
        found[(head.group(1), head.group(2))] = text[head.end():end]
    return found


def spec_ops(spec):
    return {(method.upper(), path): op
            for path, item in spec['paths'].items()
            for method, op in item.items() if method in HTTP_METHODS}


def test_doc_exists_and_is_not_a_stub():
    assert len(DOC.read_text()) > 3000


def test_every_endpoint_has_a_section(spec, sections):
    assert set(spec_ops(spec)) == set(sections)


def test_every_endpoint_is_in_the_summary_table(spec):
    text = DOC.read_text()
    for method, path in spec_ops(spec):
        assert f'| {method} | {path} |' in text, f'{method} {path}'


def test_sections_mention_every_status_code(spec, sections):
    for key, op in spec_ops(spec).items():
        for code in op['responses']:
            assert code in sections[key], f'{key[0]} {key[1]} lacks {code}'


def test_header_column_matches_the_spec(spec):
    text = DOC.read_text()
    for (method, path), op in spec_ops(spec).items():
        needs = any(par['name'] == ep.USER_EMAIL_HEADER
                    for par in op.get('parameters', []))
        row = re.search(rf'^\| {method} \| {re.escape(path)} \|.*$', text,
                        re.MULTILINE).group(0)
        assert row.rstrip().endswith('| Yes |' if needs else '| No |'), row


def test_every_tag_has_a_heading(spec):
    text = DOC.read_text()
    for tag in spec['tags']:
        assert f'\n## {tag["name"]}\n' in text, tag['name']
