"""
Audit of the generated Swagger spec (GET /swagger.json): every route is
documented, and every operation says what it does, how it can fail, and what
it needs. If you add an endpoint, this test tells you what is missing.
"""
import pytest

import server.endpoints as ep

OK = 200
WRITE_METHODS = ('post', 'put', 'patch', 'delete')
HTTP_METHODS = ('get', 'post', 'put', 'patch', 'delete')
# Endpoints that never touch the database:
NO_DB_PATHS = ('/hello', '/endpoints', '/states/fields')
# Routes Flask and flask-restx add themselves (not ours to document):
BUILT_IN_PREFIXES = ('/static', '/swagger', '/swaggerui')


@pytest.fixture(scope='module')
def spec():
    resp = ep.app.test_client().get('/swagger.json')
    assert resp.status_code == OK
    return resp.get_json()


def operations(spec):
    for path, item in spec['paths'].items():
        for method, op in item.items():
            if method in HTTP_METHODS:
                yield path, method, op, item


def param_names(op, item):
    return {par['name'] for par in op.get('parameters', [])
            + item.get('parameters', [])}


def swagger_path(rule):
    """Turn Flask's '<name>' into Swagger's '{name}'."""
    return rule.replace('<', '{').replace('>', '}')


def test_spec_describes_the_api(spec):
    assert spec['info']['title'] == 'Oasis API'
    assert spec['info']['version']
    assert len(spec['info']['description']) > 20


def test_every_route_is_documented(spec):
    documented = {(path, method.upper())
                  for path, method, _, _ in operations(spec)}
    routes = {(swagger_path(rule.rule), method)
              for rule in ep.app.url_map.iter_rules()
              if rule.rule != '/'
              if not rule.rule.startswith(BUILT_IN_PREFIXES)
              for method in rule.methods if method in
              [m.upper() for m in HTTP_METHODS]}
    assert routes == documented


def test_every_operation_has_a_summary(spec):
    for path, method, op, _ in operations(spec):
        summary = op.get('summary', '')
        assert len(summary) >= 10, f'{method.upper()} {path} needs a summary'
        assert '()' not in summary, f'{method.upper()} {path}: {summary}'


def test_every_operation_has_a_tag(spec):
    tags = {ep.TAG_SYSTEM, ep.TAG_STATES, ep.TAG_CITIES, ep.TAG_LISTINGS,
            ep.TAG_PURCHASE_REQUESTS}
    for path, method, op, _ in operations(spec):
        assert set(op.get('tags', [])) & tags, f'{method.upper()} {path}'
        assert 'default' not in op['tags'], f'{method.upper()} {path}'


def test_every_operation_has_a_success_response(spec):
    for path, method, op, _ in operations(spec):
        assert any(code.startswith('2') for code in op['responses']), \
            f'{method.upper()} {path} has no 2xx response'


def test_database_operations_document_503(spec):
    for path, method, op, _ in operations(spec):
        if path not in NO_DB_PATHS:
            assert '503' in op['responses'], f'{method.upper()} {path}'


def test_operations_on_one_record_document_404(spec):
    for path, method, op, _ in operations(spec):
        if '{' in path:
            assert '404' in op['responses'], f'{method.upper()} {path}'


def test_operations_with_a_body_document_400(spec):
    for path, method, op, item in operations(spec):
        if 'payload' in param_names(op, item):
            assert '400' in op['responses'], f'{method.upper()} {path}'


def test_permission_operations_document_the_header(spec):
    for path, method, op, item in operations(spec):
        needs_header = ep.USER_EMAIL_HEADER in param_names(op, item)
        has_auth_codes = {'401', '403'} <= set(op['responses'])
        assert needs_header == has_auth_codes, f'{method.upper()} {path}'


def test_write_operations_are_not_silently_open(spec):
    """
    States, cities and listings are protected, so all their writes need the
    header. Purchase requests are listed so that the gap is visible here and
    this test must be updated when that feature is secured.
    """
    for path, method, op, item in operations(spec):
        if method in WRITE_METHODS and not path.startswith(
                '/purchase-requests'):
            assert ep.USER_EMAIL_HEADER in param_names(op, item), \
                f'{method.upper()} {path}'


def test_every_model_field_is_described(spec):
    assert spec['definitions']
    for name, model in spec['definitions'].items():
        for field, details in model['properties'].items():
            assert details.get('description'), f'{name}.{field}'


def test_status_fields_list_their_allowed_values(spec):
    update = spec['definitions']['UpdatePurchaseRequest']
    assert update['properties']['status']['enum'] == ['accepted',
                                                      'rejected',
                                                      'cancelled']
    listing = spec['definitions']['UpdateListing']
    assert listing['properties']['status']['enum'] == [
        'available', 'pending', 'sold']
