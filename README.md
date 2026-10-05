# oasis

Campus marketplace where students can list items, browse listings, and request to buy them.

## Stack
React frontend, Node.js/Express backend, PostgreSQL database. The repo also still contains the Flask template server (`server/`).

## Startup

### Flask server (template)
```bash
python3 -m venv venv
source venv/bin/activate
export PYTHONPATH="$PWD"
make dev_env
make all_tests
./local.sh
```
Open http://127.0.0.1:8000/ for the API documentation. Stop the server with Ctrl+C.

### Node backend
```bash
cd backend
npm install
npm run dev
```

### React frontend
```bash
cd frontend
npm install
npm run dev
```
