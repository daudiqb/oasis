# API Endpoints

All endpoints are served by the Flask server in `server/endpoints.py`.
Full Swagger docs are at http://127.0.0.1:8000/ while the server is running.

| Method | Endpoint   | Description |
|--------|------------|-------------|
| GET    | /hello     | Check that the server is running |
| GET    | /endpoints | List all endpoints |
| GET    | /states    | List all states |
| POST   | /states    | Create a state (requires permission) |
| GET    | /cities    | List all cities |

## Planned
- Cities: get one, create, update, delete
- Listings: CRUD, filter by city or state, search near a location
- Purchase requests: create, view, accept/reject/cancel

## Create a state

`POST /states` requires the `X-User-Email` header and permission from
`security.is_permitted('states', 'create', user_email)`. The temporary security
configuration allows `ejc369@nyu.edu`; change the states create user list in
`security/security.py` to configure access. This header is a caller-supplied
identity, not verified authentication; production use requires trusted identity
verification.

The JSON object requires `state_code` and `name`. Optional fields are `population`
(default 0), `capital` (default empty string), and `area_sq_miles` (default 0.0).
Success returns 201 with `Message` and `State`. Errors return 400 for invalid
input or duplicate codes, 401 for a missing/blank email header, 403 for denied
permission, and 503 when the database is unavailable.
