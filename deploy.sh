#!/bin/bash
# Run from a workstation with SSH access to the PythonAnywhere account.
set -euo pipefail

: "${PA_USER:?Set PA_USER to your PythonAnywhere username}"
PA_PROJECT_DIR=${PA_PROJECT_DIR:-/home/$PA_USER/oasis}
PA_VENV_PATH=${PA_VENV_PATH:-/home/$PA_USER/.virtualenvs/oasis}
PA_DOMAIN=${PA_DOMAIN:-$PA_USER.pythonanywhere.com}
PA_SSH_HOST=${PA_SSH_HOST:-ssh.pythonanywhere.com}

printf -v rebuild_command 'cd %q && PA_VENV_PATH=%q PA_DOMAIN=%q bash ./rebuild.sh' \
    "$PA_PROJECT_DIR" "$PA_VENV_PATH" "$PA_DOMAIN"
ssh "$PA_USER@$PA_SSH_HOST" "$rebuild_command"
