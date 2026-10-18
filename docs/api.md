# API Endpoints

All endpoints are served by the Flask server in `server/endpoints.py`.
Full Swagger docs are at http://127.0.0.1:8000/ while the server is running.

| Method | Endpoint   | Description |
|--------|------------|-------------|
| GET    | /hello     | Check that the server is running |
| GET    | /endpoints | List all endpoints |
| GET    | /states    | List all states |
| GET    | /cities    | List all cities |

## Planned
- Cities: get one, create, update, delete
- Listings: CRUD, filter by city or state, search near a location
- Purchase requests: create, view, accept/reject/cancel