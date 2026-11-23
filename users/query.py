"""
Users and their auth codes, stored in MongoDB through data/db_connect.py.
Each user is one document, identified by email. An auth code is a random
secret handed out once; only its SHA-256 hash is stored, never the code.
"""
import hashlib
import hmac
import secrets

import data.db_connect as dbc
from data.db_connect import needs_db

COLLECT = 'users'

EMAIL = 'email'
NAME = 'name'
AUTH_HASH = 'auth_hash'
AUTH_CODE = 'auth_code'

CODE_BYTES = 16


def _norm(email) -> str:
    return email.strip().lower() if isinstance(email, str) else ''


def _hash(code: str) -> str:
    return hashlib.sha256(code.encode('utf-8')).hexdigest()


def _new_code() -> str:
    return secrets.token_hex(CODE_BYTES)


def _public(doc: dict) -> dict:
    """
    Return a copy of a user without Mongo's ID or the stored code hash.
    """
    return {key: val for key, val in doc.items()
            if key not in (dbc.MONGO_ID, AUTH_HASH)}


@needs_db
def create(email: str, name: str) -> dict:
    """
    Add a user and issue their first auth code. The code is returned
    here once and is not stored. Raises ValueError for a missing email
    or name, or an email that is already registered.
    """
    email = _norm(email)
    if not email or '@' not in email:
        raise ValueError('A valid email is required.')
    if not name or not name.strip():
        raise ValueError('name is required.')
    if dbc.read_one(COLLECT, {EMAIL: email}):
        raise ValueError('That email is already registered.')
    code = _new_code()
    dbc.create(COLLECT, {EMAIL: email, NAME: name.strip(),
                         AUTH_HASH: _hash(code)})
    return {EMAIL: email, NAME: name.strip(), AUTH_CODE: code}


@needs_db
def read_one(email: str):
    """
    Return one user (without any auth data), or None if not found.
    """
    doc = dbc.read_one(COLLECT, {EMAIL: _norm(email)})
    return _public(doc) if doc else None


@needs_db
def read() -> list:
    """
    Return all users (without any auth data).
    """
    return [_public(doc) for doc in dbc.read(COLLECT)]


def exists(email: str) -> bool:
    return bool(read_one(email))


@needs_db
def new_auth_code(email: str) -> str:
    """
    Replace a user's auth code with a fresh one and return it once.
    The old code stops working. Raises ValueError for an unknown user.
    """
    email = _norm(email)
    if not dbc.read_one(COLLECT, {EMAIL: email}):
        raise ValueError('No such user.')
    code = _new_code()
    dbc.update(COLLECT, {EMAIL: email}, {AUTH_HASH: _hash(code)})
    return code


@needs_db
def verify_auth_code(email: str, code: str) -> bool:
    """
    True only if the user exists and the code matches their stored hash.
    """
    if not code or not isinstance(code, str):
        return False
    doc = dbc.read_one(COLLECT, {EMAIL: _norm(email)})
    if not doc or not doc.get(AUTH_HASH):
        return False
    return hmac.compare_digest(doc[AUTH_HASH], _hash(code))
