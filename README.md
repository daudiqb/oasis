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

### Running the frontend
```bash
cd frontend
npm install
npm run dev
```
