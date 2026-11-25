#!/bin/bash
# Run on PythonAnywhere, either directly in a Bash console or via deploy.sh.
set -euo pipefail

cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
PA_VENV_PATH=${PA_VENV_PATH:-$HOME/.virtualenvs/oasis}
PA_DOMAIN=${PA_DOMAIN:-${USER:?Set PA_DOMAIN to your web app domain}.pythonanywhere.com}

if [[ ! -x "$PA_VENV_PATH/bin/python" ]]; then
    printf 'Python virtualenv not found at %s\n' "$PA_VENV_PATH" >&2
    exit 1
fi

echo "Rebuilding $PA_DOMAIN from master"
git pull --ff-only origin master
"$PA_VENV_PATH/bin/python" -m pip install -r requirements.txt
pa_reload_webapp.py "$PA_DOMAIN"
echo "Finished rebuilding $PA_DOMAIN."
