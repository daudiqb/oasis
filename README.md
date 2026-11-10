# oasis

A geographic database API for US states and cities, with a marketplace where each listing belongs to a city.

## Tech stack
- Python 3.9+
- API: Flask and flask-restx (Swagger docs)
- Database: MongoDB
- Testing: pytest
- Lint: flake8
- Build: make
- CI/CD: GitHub Actions
- Deployment: PythonAnywhere
- Frontend: React (in `frontend/`)

## Project layout
- `server/` Flask app and endpoints
- `states/` state data and queries
- `cities/` city data and queries
- `data/` MongoDB connection
- `frontend/` React app

### Running the API (Flask)
```bash
python3 -m venv venv
source venv/bin/activate
export PYTHONPATH="$PWD"
make dev_env
make all_tests
./local.sh
```
Open http://127.0.0.1:8000/ for the API documentation. Stop the server with Ctrl+C.

### Loading local MongoDB
Start MongoDB locally on `localhost:27017`, activate your virtual environment,
and install the dependencies with `make dev_env`. From the repository root:

```bash
make load_db
```

This loads the bundled CSVs into the `states` and `cities` collections in
`seDB`. The target forces local MongoDB (`CLOUD_MONGO=0`). It inserts missing
records without changing existing records, so you can run it again safely.
Both CSVs are validated before insertion. Database failures can leave a partial
import; rerun the command after restoring the connection.

The states CSV contains 50 states (DC and PR are excluded); population, capital,
and area use zero/empty defaults. The cities CSV contains three starter cities:
Brooklyn, Manhattan, and Jersey City. To load a larger dataset:

```bash
make load_db CITIES_CSV=/path/to/cities.csv
```

Cities CSV columns are `name,state_code,latitude,longitude`; each city must
reference a state in the states CSV. Existing city identity is name plus state
code. You can also override `STATES_CSV` (columns `Abbrev,State`) and `PYTHON`.

### Running the frontend
```bash
cd frontend
npm install
npm run dev
```
