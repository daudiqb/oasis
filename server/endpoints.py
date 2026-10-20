"""
This is the file containing all of the endpoints for our flask app.
The endpoint called `endpoints` will return all available endpoints.
"""
from http import HTTPStatus

from flask import Flask, request
from flask_restx import Resource, Api, fields  # Namespace
from flask_cors import CORS

import werkzeug.exceptions as wz

import states.query as sqry
import cities.query as cqry
import purchase_requests.query as prqry

app = Flask(__name__)
CORS(app)
api = Api(app)

ENDPOINT_EP = '/endpoints'
ENDPOINT_RESP = 'Available endpoints'
HELLO_EP = '/hello'
HELLO_RESP = 'hello'
STATES_EP = '/states'
STATES_RESP = 'States:'
STATE_EP = f'{STATES_EP}/<state_code>'
STATE_RESP = 'State'
CITIES_EP = '/cities'
CITIES_RESP = 'Cities'
MESSAGE = 'Message'


@api.route(HELLO_EP)
class HelloWorld(Resource):
    """
    The purpose of the HelloWorld class is to have a simple test to see if the
    app is working at all.
    """
    def get(self):
        """
        A trivial endpoint to see if the server is running.
        """
        return {HELLO_RESP: 'world'}


@api.route(ENDPOINT_EP)
class Endpoints(Resource):
    """
    This class will serve as live, fetchable documentation of what endpoints
    are available in the system.
    """
    def get(self):
        """
        The `get()` method will return a sorted list of available endpoints.
        """
        endpoints = sorted(rule.rule for rule in api.app.url_map.iter_rules())
        return {"Available endpoints": endpoints}


@api.route(STATES_EP)
class States(Resource):
    """
    The get method will return a list of all states in the database.
    """
    @api.response(HTTPStatus.OK.value, 'Success')
    @api.response(HTTPStatus.SERVICE_UNAVAILABLE.value, 'Service Unavailable')
    def get(self):
        """
        The get method will return a list of all states in the database.
        """
        states = sqry.read()
        if states is None:
            raise wz.ServiceUnavailable('Database may be down.')
        return {STATES_RESP: states}


@api.route(STATE_EP)
class State(Resource):
    """Read a single state by its code."""

    @api.response(HTTPStatus.OK.value, 'Success')
    @api.response(HTTPStatus.NOT_FOUND.value, 'Not Found')
    @api.response(HTTPStatus.SERVICE_UNAVAILABLE.value, 'Service Unavailable')
    def get(self, state_code):
        """Return one state, 404 if missing, or 503 if the DB is down."""
        state_exists = sqry.exists(state_code)
        if state_exists is None:
            raise wz.ServiceUnavailable('Database may be down.')
        if not state_exists:
            raise wz.NotFound(f'State {state_code} not found.')
        state = sqry.read_one(state_code)
        if state is None:
            raise wz.ServiceUnavailable('Database may be down.')
        return {STATE_RESP: state}


@api.route(CITIES_EP)
class Cities(Resource):
    """
    Endpoint for reading all cities.
    """
    @api.response(HTTPStatus.OK.value, 'Success')
    @api.response(HTTPStatus.SERVICE_UNAVAILABLE.value, 'Service Unavailable')
    def get(self):
        """
        Return all cities in the database.
        """
        cities = cqry.read()
        if cities is None:
            raise wz.ServiceUnavailable('Database may be down.')
        return {CITIES_RESP: cities}


PURCHASE_REQUESTS_EP = '/purchase-requests'
PURCHASE_REQUEST_EP = f'{PURCHASE_REQUESTS_EP}/<request_id>'
PURCHASE_REQUESTS_RESP = 'Purchase requests'
PURCHASE_REQUEST_RESP = 'Purchase request'

PURCHASE_REQUEST_CREATE_FLDS = api.model('CreatePurchaseRequest', {
    prqry.LISTING_ID: fields.String(required=True),
    prqry.BUYER_ID: fields.String(required=True),
    prqry.SELLER_ID: fields.String(required=True),
    prqry.MESSAGE: fields.String(),
})

PURCHASE_REQUEST_UPDATE_FLDS = api.model('UpdatePurchaseRequest', {
    prqry.STATUS: fields.String(required=True),
})


@api.route(PURCHASE_REQUESTS_EP)
class PurchaseRequests(Resource):
    """
    Send purchase requests, and view them.
    """
    @api.doc(params={prqry.BUYER_ID: 'Outgoing requests of this buyer',
                     prqry.SELLER_ID: 'Incoming requests of this seller',
                     prqry.STATUS: 'Only requests with this status'})
    @api.response(HTTPStatus.OK.value, 'Success')
    @api.response(HTTPStatus.SERVICE_UNAVAILABLE.value, 'Service Unavailable')
    def get(self):
        """
        Return purchase requests. Use buyer_id for a buyer's outgoing
        requests and seller_id for a seller's incoming ones.
        """
        requests = prqry.read(buyer_id=request.args.get(prqry.BUYER_ID),
                              seller_id=request.args.get(prqry.SELLER_ID),
                              status=request.args.get(prqry.STATUS))
        if requests is None:
            raise wz.ServiceUnavailable('Database may be down.')
        return {PURCHASE_REQUESTS_RESP: requests}

    @api.expect(PURCHASE_REQUEST_CREATE_FLDS)
    @api.response(HTTPStatus.CREATED.value, 'Created')
    @api.response(HTTPStatus.BAD_REQUEST.value, 'Bad Request')
    @api.response(HTTPStatus.SERVICE_UNAVAILABLE.value, 'Service Unavailable')
    def post(self):
        """
        Send a request to buy a listing.
        """
        data = request.get_json(silent=True) or {}
        try:
            new_request = prqry.create(data.get(prqry.LISTING_ID),
                                       data.get(prqry.BUYER_ID),
                                       data.get(prqry.SELLER_ID),
                                       data.get(prqry.MESSAGE, ''))
        except ValueError as err:
            raise wz.BadRequest(str(err))
        if new_request is None:
            raise wz.ServiceUnavailable('Database may be down.')
        return {MESSAGE: 'Purchase request sent.',
                PURCHASE_REQUEST_RESP: new_request}, HTTPStatus.CREATED


@api.route(PURCHASE_REQUEST_EP)
class PurchaseRequest(Resource):
    """
    Operations on a single purchase request.
    """
    @api.expect(PURCHASE_REQUEST_UPDATE_FLDS)
    @api.response(HTTPStatus.OK.value, 'Success')
    @api.response(HTTPStatus.BAD_REQUEST.value, 'Bad Request')
    @api.response(HTTPStatus.NOT_FOUND.value, 'Not Found')
    @api.response(HTTPStatus.SERVICE_UNAVAILABLE.value, 'Service Unavailable')
    def patch(self, request_id):
        """
        Accept, reject, or cancel a pending purchase request.
        """
        data = request.get_json(silent=True) or {}
        request_exists = prqry.exists(request_id)
        if request_exists is None:
            raise wz.ServiceUnavailable('Database may be down.')
        if not request_exists:
            raise wz.NotFound(f'Purchase request {request_id} not found.')
        try:
            updated = prqry.update_status(request_id,
                                          data.get(prqry.STATUS))
        except ValueError as err:
            raise wz.BadRequest(str(err))
        if updated is None:
            raise wz.ServiceUnavailable('Database may be down.')
        return {MESSAGE: 'Purchase request updated.',
                PURCHASE_REQUEST_RESP: updated}
