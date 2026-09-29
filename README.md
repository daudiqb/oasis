# flask-api
An example flask rest API server.

Run these commands from the project directory to set up and start the Flask API:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
export PYTHONPATH="$PWD"
python -m flask --app server.endpoints run --debug --host=127.0.0.1 --port=8000
```

Open http://127.0.0.1:8000/ for the API documentation.

Check the endpoints in a second terminal:

```bash
curl http://127.0.0.1:8000/hello
curl http://127.0.0.1:8000/endpoints
curl http://127.0.0.1:8000/states
```

Run tests from the project directory:

```bash
source .venv/bin/activate
export PYTHONPATH="$PWD"
python -m pytest
```

To start the server again after setup, run from the project directory:

```bash
source .venv/bin/activate
export PYTHONPATH="$PWD"
bash local.sh
```

Stop the server with Ctrl+C.

Exit the virtual environment:

```bash
deactivate
```

