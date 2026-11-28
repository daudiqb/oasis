"""
This is the file containing all of the endpoints for our flask app.
The endpoint called `endpoints` will return all available endpoints.
"""
from http import HTTPStatus

from flask import Flask, request
from flask_restx import Resource, Api, fields  # Namespace
from flask_cors import CORS

import werkzeug.exceptions as wz

from server.permissions import USER_EMAIL_HEADER, needs_permission

import security.security as sec
import states.query as sqry
import states.fields as sflds
import cities.query as cqry
import purchase_requests.query as prqry
import listings.query as lqry

app = Flask(__name__)
CORS(app)
api = Api(app, title='Oasis API', version='1.0',
          description='US states and cities, with a marketplace of '
                      + 'listings and purchase requests. See docs/api.md.')

# Each namespace becomes a section (tag) in the Swagger docs. The paths are
# already complete in the *_EP constants, so every namespace is rooted at '/'.
TAG_SYSTEM = 'System'
TAG_STATES = 'States'
TAG_CITIES = 'Cities'
TAG_LISTINGS = 'Listings'
TAG_PURCHASE_REQUESTS = 'Purchase requests'
system_ns = api.namespace(TAG_SYSTEM, path='/',
                          description='Health check and endpoint list')
states_ns = api.namespace(TAG_STATES, path='/',
                          description='US states')
cities_ns = api.namespace(TAG_CITIES, path='/',
                          description='Cities, which belong to a state')
listings_ns = api.namespace(TAG_LISTINGS, path='/',
                            description='Marketplace listings in a city')
purchase_requests_ns = api.namespace(
    TAG_PURCHASE_REQUESTS, path='/',
    description='Requests to buy a listing')

ENDPOINT_EP = '/endpoints'
ENDPOINT_RESP = 'Available endpoints'
HELLO_EP = '/hello'
HELLO_RESP = 'hello'
STATES_EP = '/states'
STATES_RESP = 'States:'
STATE_EP = f'{STATES_EP}/<state_code>'
STATE_RESP = 'State'
STATE_FIELDS_EP = f'{STATES_EP}/fields'
STATE_FIELDS_RESP = 'Fields'
CITIES_EP = '/cities'
CITIES_RESP = 'Cities'
CITY_EP = f'{CITIES_EP}/<state_code>/<name>'
CITY_RESP = 'City'
LISTINGS_EP = '/listings'
LISTINGS_RESP = 'Listings'
LISTING_EP = f'{LISTINGS_EP}/<listing_id>'
LISTING_RESP = 'Listing'
LISTING_CITY_ARG = 'city'
LISTING_STATE_ARG = 'state'
LISTING_SEARCH_ARG = 'search'
MESSAGE = 'Message'

STATE_CREATE_FLDS = api.model('CreateState', {
    'state_code': fields.String(
        required=True, description='Two-letter state code, e.g. NY'),
    'name': fields.String(required=True, description='State name'),
    'population': fields.Integer(description='Population (default 0)'),
    'capital': fields.String(description='Capital city (default empty)'),
    'area_sq_miles': fields.Float(description='Area in square miles'),
})


STATE_UPDATE_FLDS = api.model('UpdateState', {
    'name': fields.String(description='New state name'),
    'population': fields.Integer(description='New population'),
    'capital': fields.String(description='New capital city'),
    'area_sq_miles': fields.Float(description='New area in square miles'),
})


@system_ns.route(HELLO_EP)
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


@system_ns.route(ENDPOINT_EP)
class Endpoints(Resource):
    """
    This class will serve as live, fetchable documentation of what endpoints
    are available in the system.
    """
    def get(self):
        """
        Return a sorted list of the available endpoint paths.
        """
        endpoints = sorted(rule.rule for rule in api.app.url_map.iter_rules())
        return {"Available endpoints": endpoints}


@states_ns.route(STATES_EP)
class States(Resource):
    """
    The get method will return a list of all states in the database.
    """
    @api.response(HTTPStatus.OK.value, 'Success')
    @api.response(HTTPStatus.SERVICE_UNAVAILABLE.value, 'Service Unavailable')
    def get(self):
        """
        Return a list of all states in the database.
        """
        states = sqry.read()
        if states is None:
            raise wz.ServiceUnavailable('Database may be down.')
        return {STATES_RESP: states}

    @api.doc(params={USER_EMAIL_HEADER: {
        'in': 'header', 'required': True, 'description': 'Acting user email',
    }})
    @api.expect(STATE_CREATE_FLDS)
    @api.response(HTTPStatus.CREATED.value, 'Created')
    @api.response(HTTPStatus.BAD_REQUEST.value, 'Bad Request')
    @api.response(HTTPStatus.UNAUTHORIZED.value, 'Missing user email')
    @api.response(HTTPStatus.FORBIDDEN.value, 'Permission denied')
    @api.response(HTTPStatus.SERVICE_UNAVAILABLE.value, 'Service Unavailable')
    @needs_permission(sec.STATES, sec.CREATE)
    def post(self):
        """Create a state when the header identifies a permitted user."""
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            raise wz.BadRequest('Request body must be a JSON object.')
        try:
            state = sqry.create(
                data.get('state_code'), data.get('name'),
                population=data.get('population', 0),
                capital=data.get('capital', ''),
                area_sq_miles=data.get('area_sq_miles', 0.0))
        except ValueError as err:
            raise wz.BadRequest(str(err))
        if state is None:
            raise wz.ServiceUnavailable('Database may be down.')
        return ({MESSAGE: 'State created.', STATE_RESP: state},
                HTTPStatus.CREATED)


@states_ns.route(STATE_FIELDS_EP)
class StateFields(Resource):
    """Describe the public fields of a state record."""

    @api.response(HTTPStatus.OK.value, 'Success')
    def get(self):
        """Return state field metadata without requiring a database."""
        return {STATE_FIELDS_RESP: sflds.get_flds()}


@states_ns.route(STATE_EP)
class State(Resource):
    """Read, update, or delete a single state by its code."""

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

    @api.doc(params={USER_EMAIL_HEADER: {
        'in': 'header', 'required': True, 'description': 'Acting user email',
    }})
    @api.expect(STATE_UPDATE_FLDS)
    @api.response(HTTPStatus.OK.value, 'Updated')
    @api.response(HTTPStatus.BAD_REQUEST.value, 'Bad Request')
    @api.response(HTTPStatus.UNAUTHORIZED.value, 'Missing user email')
    @api.response(HTTPStatus.FORBIDDEN.value, 'Permission denied')
    @api.response(HTTPStatus.NOT_FOUND.value, 'Not Found')
    @api.response(HTTPStatus.SERVICE_UNAVAILABLE.value, 'Service Unavailable')
    @needs_permission(sec.STATES, sec.UPDATE)
    def put(self, state_code):
        """Partially update a state, preserving its code and omitted fields."""
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            raise wz.BadRequest('Request body must be a JSON object.')
        if 'state_code' in data:
            raise wz.BadRequest('State code cannot be changed.')
        state_exists = sqry.exists(state_code)
        if state_exists is None:
            raise wz.ServiceUnavailable('Database may be down.')
        if not state_exists:
            raise wz.NotFound(f'State {state_code} not found.')
        try:
            state = sqry.update(state_code, **data)
        except ValueError as err:
            raise wz.BadRequest(str(err))
        if state is None:
            raise wz.ServiceUnavailable('Database may be down.')
        return {MESSAGE: 'State updated.', STATE_RESP: state}

    @api.doc(params={USER_EMAIL_HEADER: {
        'in': 'header', 'required': True, 'description': 'Acting user email',
    }})
    @api.response(HTTPStatus.OK.value, 'Deleted')
    @api.response(HTTPStatus.BAD_REQUEST.value, 'Invalid code or has cities')
    @api.response(HTTPStatus.UNAUTHORIZED.value, 'Missing user email')
    @api.response(HTTPStatus.FORBIDDEN.value, 'Permission denied')
    @api.response(HTTPStatus.NOT_FOUND.value, 'Not Found')
    @api.response(HTTPStatus.SERVICE_UNAVAILABLE.value, 'Service Unavailable')
    @needs_permission(sec.STATES, sec.DELETE)
    def delete(self, state_code):
        """Delete a state when permitted and no cities reference it."""
        try:
            deleted = sqry.delete(state_code)
        except ValueError as err:
            raise wz.BadRequest(str(err))
        if deleted is None:
            raise wz.ServiceUnavailable('Database may be down.')
        if not deleted:
            raise wz.NotFound(f'State {state_code} not found.')
        return {MESSAGE: 'State deleted.'}


CITY_CREATE_FLDS = api.model('CreateCity', {
    cqry.NAME: fields.String(required=True, description='City name'),
    cqry.STATE_CODE: fields.String(
        required=True, description='Code of an existing state'),
    cqry.LATITUDE: fields.Float(required=True, description='Latitude'),
    cqry.LONGITUDE: fields.Float(required=True, description='Longitude'),
})


CITY_UPDATE_FLDS = api.model('UpdateCity', {
    cqry.LATITUDE: fields.Float(description='New latitude'),
    cqry.LONGITUDE: fields.Float(description='New longitude'),
})


@cities_ns.route(CITIES_EP)
class Cities(Resource):
    """
    Endpoint for reading all cities and creating a city.
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

    @api.doc(params={USER_EMAIL_HEADER: {
        'in': 'header', 'required': True, 'description': 'Acting user email',
    }})
    @api.expect(CITY_CREATE_FLDS)
    @api.response(HTTPStatus.CREATED.value, 'Created')
    @api.response(HTTPStatus.BAD_REQUEST.value, 'Bad Request')
    @api.response(HTTPStatus.UNAUTHORIZED.value, 'Missing user email')
    @api.response(HTTPStatus.FORBIDDEN.value, 'Permission denied')
    @api.response(HTTPStatus.SERVICE_UNAVAILABLE.value, 'Service Unavailable')
    @needs_permission(sec.CITIES, sec.CREATE)
    def post(self):
        """
        Create a city when the header identifies a permitted user.
        """
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            raise wz.BadRequest('Request body must be a JSON object.')
        try:
            city = cqry.create(
                data.get(cqry.NAME), data.get(cqry.STATE_CODE),
                data.get(cqry.LATITUDE), data.get(cqry.LONGITUDE))
        except ValueError as err:
            raise wz.BadRequest(str(err))
        if city is None:
            raise wz.ServiceUnavailable('Database may be down.')
        return ({MESSAGE: 'City created.', CITY_RESP: city},
                HTTPStatus.CREATED)


@cities_ns.route(CITY_EP)
class City(Resource):
    """
    Read, update or delete a single city by its state code and name.
    """
    @api.response(HTTPStatus.OK.value, 'Success')
    @api.response(HTTPStatus.NOT_FOUND.value, 'Not Found')
    @api.response(HTTPStatus.SERVICE_UNAVAILABLE.value, 'Service Unavailable')
    def get(self, state_code, name):
        """
        Return one city, 404 if missing, or 503 if the DB is down.
        """
        city_exists = cqry.exists(name, state_code)
        if city_exists is None:
            raise wz.ServiceUnavailable('Database may be down.')
        if not city_exists:
            raise wz.NotFound(f'City {name}, {state_code} not found.')
        city = cqry.read_one(name, state_code)
        if city is None:
            raise wz.ServiceUnavailable('Database may be down.')
        return {CITY_RESP: city}

    @api.doc(params={USER_EMAIL_HEADER: {
        'in': 'header', 'required': True, 'description': 'Acting user email',
    }})
    @api.expect(CITY_UPDATE_FLDS)
    @api.response(HTTPStatus.OK.value, 'Updated')
    @api.response(HTTPStatus.BAD_REQUEST.value, 'Bad Request')
    @api.response(HTTPStatus.UNAUTHORIZED.value, 'Missing user email')
    @api.response(HTTPStatus.FORBIDDEN.value, 'Permission denied')
    @api.response(HTTPStatus.NOT_FOUND.value, 'Not Found')
    @api.response(HTTPStatus.SERVICE_UNAVAILABLE.value, 'Service Unavailable')
    @needs_permission(sec.CITIES, sec.UPDATE)
    def put(self, state_code, name):
        """
        Change a city's latitude or longitude; omitted fields stay the same.
        """
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            raise wz.BadRequest('Request body must be a JSON object.')
        city_exists = cqry.exists(name, state_code)
        if city_exists is None:
            raise wz.ServiceUnavailable('Database may be down.')
        if not city_exists:
            raise wz.NotFound(f'City {name}, {state_code} not found.')
        try:
            city = cqry.update(name, state_code, **data)
        except ValueError as err:
            raise wz.BadRequest(str(err))
        if city is None:
            raise wz.ServiceUnavailable('Database may be down.')
        return {MESSAGE: 'City updated.', CITY_RESP: city}

    @api.doc(params={USER_EMAIL_HEADER: {
        'in': 'header', 'required': True, 'description': 'Acting user email',
    }})
    @api.response(HTTPStatus.OK.value, 'Deleted')
    @api.response(HTTPStatus.UNAUTHORIZED.value, 'Missing user email')
    @api.response(HTTPStatus.FORBIDDEN.value, 'Permission denied')
    @api.response(HTTPStatus.NOT_FOUND.value, 'Not Found')
    @api.response(HTTPStatus.SERVICE_UNAVAILABLE.value, 'Service Unavailable')
    @needs_permission(sec.CITIES, sec.DELETE)
    def delete(self, state_code, name):
        """
        Delete a city when the header identifies a permitted user.
        """
        deleted = cqry.delete(name, state_code)
        if deleted is None:
            raise wz.ServiceUnavailable('Database may be down.')
        if not deleted:
            raise wz.NotFound(f'City {name}, {state_code} not found.')
        return {MESSAGE: 'City deleted.'}


LISTING_CREATE_FLDS = api.model('CreateListing', {
    lqry.TITLE: fields.String(required=True, description='Listing title'),
    lqry.PRICE: fields.Float(required=True, description='Asking price'),
    lqry.CITY: fields.String(
        required=True, description='Name of an existing city'),
    lqry.STATE_CODE: fields.String(
        required=True, description='State code of that city'),
    lqry.SELLER_ID: fields.String(
        required=True, description='ID of the seller'),
    lqry.DESCRIPTION: fields.String(description='Longer description'),
})


@listings_ns.route(LISTINGS_EP)
class Listings(Resource):
    """
    Endpoint for reading all listings and creating a listing.
    """
    @api.doc(params={
        LISTING_CITY_ARG: 'Only listings in this city',
        LISTING_STATE_ARG: 'Only listings in this state code',
        LISTING_SEARCH_ARG: 'Text to find in the title or description',
    })
    @api.response(HTTPStatus.OK.value, 'Success')
    @api.response(HTTPStatus.SERVICE_UNAVAILABLE.value, 'Service Unavailable')
    def get(self):
        """
        Return listings, optionally filtered by city, state and search text.
        """
        listings = lqry.read(city=request.args.get(LISTING_CITY_ARG),
                             state_code=request.args.get(LISTING_STATE_ARG),
                             search=request.args.get(LISTING_SEARCH_ARG))
        if listings is None:
            raise wz.ServiceUnavailable('Database may be down.')
        return {LISTINGS_RESP: listings}

    @api.doc(params={USER_EMAIL_HEADER: {
        'in': 'header', 'required': True, 'description': 'Acting user email',
    }})
    @api.expect(LISTING_CREATE_FLDS)
    @api.response(HTTPStatus.CREATED.value, 'Created')
    @api.response(HTTPStatus.BAD_REQUEST.value, 'Bad Request')
    @api.response(HTTPStatus.UNAUTHORIZED.value, 'Missing user email')
    @api.response(HTTPStatus.FORBIDDEN.value, 'Permission denied')
    @api.response(HTTPStatus.SERVICE_UNAVAILABLE.value, 'Service Unavailable')
    def post(self):
        """
        Create a listing when the header identifies a permitted user.
        """
        user_email = request.headers.get(USER_EMAIL_HEADER, '').strip()
        if not user_email:
            raise wz.Unauthorized(f'{USER_EMAIL_HEADER} header is required.')
        if not sec.is_permitted(sec.LISTINGS, sec.CREATE, user_email):
            raise wz.Forbidden('Not permitted to create listings.')
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            raise wz.BadRequest('Request body must be a JSON object.')
        try:
            listing = lqry.create(
                data.get(lqry.TITLE), data.get(lqry.PRICE),
                data.get(lqry.CITY), data.get(lqry.STATE_CODE),
                data.get(lqry.SELLER_ID),
                data.get(lqry.DESCRIPTION, ''))
        except ValueError as err:
            raise wz.BadRequest(str(err))
        if listing is None:
            raise wz.ServiceUnavailable('Database may be down.')
        return ({MESSAGE: 'Listing created.', LISTING_RESP: listing},
                HTTPStatus.CREATED)


LISTING_UPDATE_FLDS = api.model('UpdateListing', {
    lqry.TITLE: fields.String(description='New title'),
    lqry.DESCRIPTION: fields.String(description='New description'),
    lqry.PRICE: fields.Float(description='New asking price'),
    lqry.CITY: fields.String(description='New city name'),
    lqry.STATE_CODE: fields.String(description='New state code'),
    lqry.STATUS: fields.String(enum=list(lqry.STATUSES),
                               description='New listing status'),
})


@listings_ns.route(LISTING_EP)
class Listing(Resource):
    """
    Read a single listing by its ID.
    """
    @api.response(HTTPStatus.OK.value, 'Success')
    @api.response(HTTPStatus.NOT_FOUND.value, 'Not Found')
    @api.response(HTTPStatus.SERVICE_UNAVAILABLE.value, 'Service Unavailable')
    def get(self, listing_id):
        """
        Return one listing, 404 if missing, or 503 if the DB is down.
        """
        listing_exists = lqry.exists(listing_id)
        if listing_exists is None:
            raise wz.ServiceUnavailable('Database may be down.')
        if not listing_exists:
            raise wz.NotFound(f'Listing {listing_id} not found.')
        listing = lqry.read_one(listing_id)
        if listing is None:
            raise wz.ServiceUnavailable('Database may be down.')
        return {LISTING_RESP: listing}

    @api.doc(params={USER_EMAIL_HEADER: {
        'in': 'header', 'required': True, 'description': 'Acting user email',
    }})
    @api.expect(LISTING_UPDATE_FLDS)
    @api.response(HTTPStatus.OK.value, 'Updated')
    @api.response(HTTPStatus.BAD_REQUEST.value, 'Bad Request')
    @api.response(HTTPStatus.UNAUTHORIZED.value, 'Missing user email')
    @api.response(HTTPStatus.FORBIDDEN.value, 'Permission denied')
    @api.response(HTTPStatus.NOT_FOUND.value, 'Not Found')
    @api.response(HTTPStatus.SERVICE_UNAVAILABLE.value, 'Service Unavailable')
    @needs_permission(sec.LISTINGS, sec.UPDATE)
    def patch(self, listing_id):
        """
        Edit a listing's details or change its status.
        """
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            raise wz.BadRequest('Request body must be a JSON object.')
        listing_exists = lqry.exists(listing_id)
        if listing_exists is None:
            raise wz.ServiceUnavailable('Database may be down.')
        if not listing_exists:
            raise wz.NotFound(f'Listing {listing_id} not found.')
        try:
            listing = lqry.update(listing_id, **data)
        except ValueError as err:
            raise wz.BadRequest(str(err))
        if listing is None:
            raise wz.ServiceUnavailable('Database may be down.')
        return {MESSAGE: 'Listing updated.', LISTING_RESP: listing}

    @api.doc(params={USER_EMAIL_HEADER: {
        'in': 'header', 'required': True, 'description': 'Acting user email',
    }})
    @api.response(HTTPStatus.OK.value, 'Deleted')
    @api.response(HTTPStatus.UNAUTHORIZED.value, 'Missing user email')
    @api.response(HTTPStatus.FORBIDDEN.value, 'Permission denied')
    @api.response(HTTPStatus.NOT_FOUND.value, 'Not Found')
    @api.response(HTTPStatus.SERVICE_UNAVAILABLE.value, 'Service Unavailable')
    @needs_permission(sec.LISTINGS, sec.DELETE)
    def delete(self, listing_id):
        """
        Delete a listing when the header identifies a permitted user.
        """
        deleted = lqry.delete(listing_id)
        if deleted is None:
            raise wz.ServiceUnavailable('Database may be down.')
        if not deleted:
            raise wz.NotFound(f'Listing {listing_id} not found.')
        return {MESSAGE: 'Listing deleted.'}


PURCHASE_REQUESTS_EP = '/purchase-requests'
PURCHASE_REQUEST_EP = f'{PURCHASE_REQUESTS_EP}/<request_id>'
PURCHASE_REQUESTS_RESP = 'Purchase requests'
PURCHASE_REQUEST_RESP = 'Purchase request'

PURCHASE_REQUEST_CREATE_FLDS = api.model('CreatePurchaseRequest', {
    prqry.LISTING_ID: fields.String(
        required=True, description='ID of the listing to buy'),
    prqry.BUYER_ID: fields.String(
        required=True, description='ID of the buyer'),
    prqry.SELLER_ID: fields.String(
        required=True, description='ID of the seller (not the buyer)'),
    prqry.MESSAGE: fields.String(description='Optional note to the seller'),
})

PURCHASE_REQUEST_UPDATE_FLDS = api.model('UpdatePurchaseRequest', {
    prqry.STATUS: fields.String(
        required=True, enum=list(prqry.NEW_STATUSES),
        description='New status for a pending request'),
})


@purchase_requests_ns.route(PURCHASE_REQUESTS_EP)
class PurchaseRequests(Resource):
    """
    Send purchase requests, and view them.
    """
    @api.doc(params={prqry.BUYER_ID: 'Outgoing requests of this buyer',
                     prqry.SELLER_ID: 'Incoming requests of this seller',
                     prqry.LISTING_ID: 'Requests for this listing',
                     prqry.STATUS: 'Only requests with this status'})
    @api.response(HTTPStatus.OK.value, 'Success')
    @api.response(HTTPStatus.SERVICE_UNAVAILABLE.value, 'Service Unavailable')
    def get(self):
        """
        Return purchase requests. Use buyer_id for a buyer's outgoing
        requests, seller_id for a seller's incoming ones, and listing_id
        for the requests on one listing.
        """
        requests = prqry.read(buyer_id=request.args.get(prqry.BUYER_ID),
                              seller_id=request.args.get(prqry.SELLER_ID),
                              status=request.args.get(prqry.STATUS),
                              listing_id=request.args.get(prqry.LISTING_ID))
        if requests is None:
            raise wz.ServiceUnavailable('Database may be down.')
        return {PURCHASE_REQUESTS_RESP: requests}

    @api.expect(PURCHASE_REQUEST_CREATE_FLDS)
    @api.response(HTTPStatus.CREATED.value, 'Created')
    @api.response(HTTPStatus.BAD_REQUEST.value, 'Bad Request')
    @api.response(HTTPStatus.NOT_FOUND.value, 'Listing Not Found')
    @api.response(HTTPStatus.SERVICE_UNAVAILABLE.value, 'Service Unavailable')
    def post(self):
        """
        Send a request to buy a listing. The listing must exist.
        """
        data = request.get_json(silent=True) or {}
        listing_id = data.get(prqry.LISTING_ID)
        if listing_id:
            listing_exists = lqry.exists(listing_id)
            if listing_exists is None:
                raise wz.ServiceUnavailable('Database may be down.')
            if not listing_exists:
                raise wz.NotFound(f'Listing {listing_id} not found.')
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


@purchase_requests_ns.route(PURCHASE_REQUEST_EP)
class PurchaseRequest(Resource):
    """
    Operations on a single purchase request.
    """
    @api.response(HTTPStatus.OK.value, 'Success')
    @api.response(HTTPStatus.NOT_FOUND.value, 'Not Found')
    @api.response(HTTPStatus.SERVICE_UNAVAILABLE.value, 'Service Unavailable')
    def get(self, request_id):
        """
        Return one purchase request.
        """
        request_exists = prqry.exists(request_id)
        if request_exists is None:
            raise wz.ServiceUnavailable('Database may be down.')
        if not request_exists:
            raise wz.NotFound(f'Purchase request {request_id} not found.')
        return {PURCHASE_REQUEST_RESP: prqry.read_one(request_id)}

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
        if updated[prqry.STATUS] == prqry.ACCEPTED:
            try:
                lqry.update(updated[prqry.LISTING_ID], status=lqry.SOLD)
            except ValueError:
                pass  # The listing was removed; the request stays accepted.
        return {MESSAGE: 'Purchase request updated.',
                PURCHASE_REQUEST_RESP: updated}
