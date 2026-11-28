# Oasis API reference

Oasis is a geographic database of US states and cities, plus a marketplace
where each listing belongs to a city and buyers send purchase requests.

The API is a Flask app using flask-restx, in `server/endpoints.py`. Data is in
MongoDB, reached only through `data/db_connect.py`. While the server runs
(`./local.sh`), live interactive docs are at http://127.0.0.1:8000/ and the raw
spec is at `/swagger.json`. `tests/test_api_doc.py` fails if this page and the
Swagger spec drift apart, so keep them in step.

## Conventions

- **Format:** requests and responses are JSON. Send `Content-Type:
  application/json` with a body.
- **Success bodies:** a JSON object. Lists and records are wrapped under a key
  (`States:`, `State`, `Cities`, `City`, `Listings`, `Listing`,
  `Purchase requests`, `Purchase request`). Changes also return `Message`.
- **Error bodies:** flask-restx returns `{"message": "..."}` with the status code.
- **IDs:** states use a two-letter code (`NY`), cities are identified by state
  code plus name, listings and purchase requests by a generated `listing_id` /
  `request_id`.

### Status codes used

| Code | Meaning |
|------|---------|
| 200 | Success (read, update, delete) |
| 201 | Created |
| 400 | Invalid input, a duplicate, or a rule was broken (the message says which) |
| 401 | The `X-User-Email` header is missing or blank |
| 403 | That user is not permitted to do this |
| 404 | The record does not exist |
| 503 | The database is unavailable |

### Who may write (`X-User-Email`)

Creating, updating and deleting **states, cities and listings** needs the
`X-User-Email` header. The server checks
`security.is_permitted(feature, action, user_email)`; the allowed users come
from the `security` collection in MongoDB, falling back to the built-in list in
`security/security.py` (see `security/security.md`). The header is a
caller-supplied identity, not verified authentication.

Users and their auth codes live in the `users` collection (`users/query.py`).
A security record that requires the `login` check is satisfied only by a
correct `auth_code`. No endpoint requires that check yet.

Reads never need the header. **Purchase requests do not need it yet.**

## Endpoint summary

| Method | Path | Purpose | Needs header |
|--------|------|---------|--------------|
| GET | /hello | Check that the server is running | No |
| GET | /endpoints | List the endpoint paths | No |
| GET | /states | List all states | No |
| POST | /states | Create a state | Yes |
| GET | /states/fields | Describe the state fields | No |
| GET | /states/{state_code} | Get one state | No |
| PUT | /states/{state_code} | Partially update a state | Yes |
| DELETE | /states/{state_code} | Delete a state with no cities | Yes |
| GET | /cities | List all cities | No |
| POST | /cities | Create a city | Yes |
| GET | /cities/{state_code}/{name} | Get one city | No |
| PUT | /cities/{state_code}/{name} | Change a city's coordinates | Yes |
| DELETE | /cities/{state_code}/{name} | Delete a city | Yes |
| GET | /listings | List listings, with filters | No |
| POST | /listings | Create a listing | Yes |
| GET | /listings/{listing_id} | Get one listing | No |
| PATCH | /listings/{listing_id} | Edit a listing or change its status | Yes |
| DELETE | /listings/{listing_id} | Delete a listing | Yes |
| GET | /purchase-requests | List purchase requests, with filters | No |
| POST | /purchase-requests | Send a request to buy a listing | No |
| GET | /purchase-requests/{request_id} | Get one purchase request | No |
| PATCH | /purchase-requests/{request_id} | Accept, reject or cancel a request | No |

## System

### `GET /hello`

Returns `{"hello": "world"}`. Use it to see that the server is up. Codes: 200.

### `GET /endpoints`

Returns `{"Available endpoints": [...]}`, a sorted list of every route path.
Codes: 200.

## States

A state has `state_code`, `name`, `population` (default 0), `capital` (default
empty) and `area_sq_miles` (default 0.0).

### `GET /states`

Returns `{"States:": [state, ...]}`. Codes: 200, 503.

### `POST /states`

Needs `X-User-Email`. Body: `state_code` (2 letters) and `name` are required;
`population` (non-negative integer), `capital`, `area_sq_miles` are optional.
Returns 201 with `Message` and `State`.

Codes: 201 created; 400 bad body, invalid value or the code already exists;
401 no header; 403 not permitted; 503 database down.

### `GET /states/fields`

The data dictionary for a state: for each field its display name, type,
whether it is required, its default and a description. Works without the
database. Returns `{"Fields": {...}}`. Codes: 200.

### `GET /states/{state_code}`

Returns `{"State": state}`. Codes: 200; 404 no such state; 503 database down.

### `PUT /states/{state_code}`

Needs `X-User-Email`. A partial update: send any of `name`, `population`,
`capital`, `area_sq_miles`. Omitted fields stay as they are, and `{}` changes
nothing. A `state_code` in the body is rejected. Returns 200 with `Message` and
the updated `State`.

Codes: 200 updated; 400 unknown field or invalid value; 401 no header;
403 not permitted; 404 no such state; 503 database down.

### `DELETE /states/{state_code}`

Needs `X-User-Email`. A state that still has cities cannot be deleted.
Returns 200 with `Message`.

Codes: 200 deleted; 400 invalid code or the state still has cities; 401 no
header; 403 not permitted; 404 no such state; 503 database down.

## Cities

A city has `name`, `state_code`, `latitude` and `longitude`. A city is
identified by its state code plus name, and its state must exist.

### `GET /cities`

Returns `{"Cities": [city, ...]}`. Codes: 200, 503.

### `POST /cities`

Needs `X-User-Email`. Body: `name`, `state_code`, `latitude` (-90 to 90) and
`longitude` (-180 to 180), all required. Returns 201 with `Message` and `City`.

Codes: 201 created; 400 bad body, invalid value, unknown state or the city
already exists; 401 no header; 403 not permitted; 503 database down.

### `GET /cities/{state_code}/{name}`

Returns `{"City": city}`. Codes: 200; 404 no such city; 503 database down.

### `PUT /cities/{state_code}/{name}`

Needs `X-User-Email`. Send `latitude` and/or `longitude`; only those can be
changed. Omitted fields stay as they are. Returns 200 with `Message` and `City`.

Codes: 200 updated; 400 not a JSON object, other fields, or out-of-range
values; 401 no header; 403 not permitted; 404 no such city; 503 database down.

### `DELETE /cities/{state_code}/{name}`

Needs `X-User-Email`. Returns 200 with `Message`.

Codes: 200 deleted; 401 no header; 403 not permitted; 404 no such city;
503 database down.

## Listings

A listing has `listing_id`, `title`, `description`, `price`, `city`,
`state_code`, `seller_id` and `status`, which is `available`, `pending` or
`sold`. The city must exist.

### `GET /listings`

Returns `{"Listings": [listing, ...]}`. Optional query filters: `city` (only
that city), `state` (only that state code) and `search` (text found in the
title or description). Codes: 200, 503.

### `POST /listings`

Needs `X-User-Email`. Body: `title`, `price` (not negative), `city`,
`state_code` and `seller_id` are required; `description` is optional. The new
listing starts as `available`. Returns 201 with `Message` and `Listing`.

Codes: 201 created; 400 bad body, invalid value or the city does not exist;
401 no header; 403 not permitted; 503 database down.

### `GET /listings/{listing_id}`

Returns `{"Listing": listing}`. Codes: 200; 404 no such listing; 503 database
down.

### `PATCH /listings/{listing_id}`

Needs `X-User-Email`. Partial update of `title`, `description`, `price`,
`city`, `state_code` and `status`. The ID and seller cannot be changed.
Returns 200 with `Message` and `Listing`.

Codes: 200 updated; 400 unknown field or invalid value; 401 no header;
403 not permitted; 404 no such listing; 503 database down.

### `DELETE /listings/{listing_id}`

Needs `X-User-Email`. Returns 200 with `Message`.

Codes: 200 deleted; 401 no header; 403 not permitted; 404 no such listing;
503 database down.

## Purchase requests

A purchase request has `request_id`, `listing_id`, `buyer_id`, `seller_id`,
`message` and `status`: `pending` when sent, later `accepted`, `rejected` or
`cancelled`.

### `GET /purchase-requests`

Returns `{"Purchase requests": [request, ...]}`. Optional query filters:
`buyer_id` (a buyer's outgoing requests), `seller_id` (a seller's incoming
requests), `listing_id` and `status`. Codes: 200, 503.

### `POST /purchase-requests`

Body: `listing_id`, `buyer_id` and `seller_id` are required; `message` is
optional. The listing must exist, the buyer cannot be the seller, and a buyer
may have only one pending request per listing. Returns 201 with `Message` and
`Purchase request`.

Codes: 201 sent; 400 missing ID, own listing or a duplicate pending request;
404 the listing does not exist; 503 database down.

### `GET /purchase-requests/{request_id}`

Returns `{"Purchase request": request}`. Codes: 200; 404 no such request;
503 database down.

### `PATCH /purchase-requests/{request_id}`

Body: `status`, one of `accepted`, `rejected` or `cancelled`. Only a pending
request can be changed. Accepting a request also marks its listing `sold`.
Returns 200 with `Message` and `Purchase request`.

Codes: 200 updated; 400 invalid status or the request is no longer pending;
404 no such request; 503 database down.

## Examples

```bash
curl http://127.0.0.1:8000/hello

curl -X POST http://127.0.0.1:8000/listings \
  -H 'Content-Type: application/json' -H 'X-User-Email: ejc369@nyu.edu' \
  -d '{"title": "Desk lamp", "price": 12.5, "city": "Brooklyn",
       "state_code": "NY", "seller_id": "seller1"}'

curl 'http://127.0.0.1:8000/listings?state=NY&search=lamp'

curl -X PATCH http://127.0.0.1:8000/purchase-requests/<request_id> \
  -H 'Content-Type: application/json' -d '{"status": "accepted"}'
```
