from functools import wraps

import data.db_connect as dbc
import users.query as uqry

"""
Our record format to meet our requirements (see security.md) will be:

{
    feature_name1: {
        create: {
            user_list: [],
            checks: {
                login: True,
                ip_address: False,
                dual_factor: False,
                # etc.
            },
        },
        read: {
            user_list: [],
            checks: {
                login: True,
                ip_address: False,
                dual_factor: False,
                # etc.
            },
        },
        update: {
            user_list: [],
            checks: {
                login: True,
                ip_address: False,
                dual_factor: False,
                # etc.
            },
        },
        delete: {
            user_list: [],
            checks: {
                login: True,
                ip_address: False,
                dual_factor: False,
                # etc.
            },
        },
    },
    feature_name2: # etc.
}
"""

COLLECT_NAME = 'security'
CREATE = 'create'
READ = 'read'
UPDATE = 'update'
DELETE = 'delete'
USER_LIST = 'user_list'
CHECKS = 'checks'
LOGIN = 'login'
AUTH_CODE = 'auth_code'
FEATURE = 'feature'

# Features:
PEOPLE = 'people'
STATES = 'states'
CITIES = 'cities'
LISTINGS = 'listings'

security_recs = None
# These will come from the DB soon:
temp_recs = {
    STATES: {
        CREATE: {USER_LIST: ['ejc369@nyu.edu']},
        UPDATE: {USER_LIST: ['ejc369@nyu.edu']},
        DELETE: {USER_LIST: ['ejc369@nyu.edu']},
    },
    CITIES: {
        CREATE: {USER_LIST: ['ejc369@nyu.edu']},
        UPDATE: {USER_LIST: ['ejc369@nyu.edu']},
        DELETE: {USER_LIST: ['ejc369@nyu.edu']},
    },
    LISTINGS: {
        CREATE: {USER_LIST: ['ejc369@nyu.edu']},
        UPDATE: {USER_LIST: ['ejc369@nyu.edu']},
        DELETE: {USER_LIST: ['ejc369@nyu.edu']},
    },
    PEOPLE: {
        CREATE: {
            USER_LIST: ['ejc369@nyu.edu'],
            CHECKS: {
                LOGIN: True,
            },
        },
    },
}


def read_from_db():
    """
    Load the security records from MongoDB. Each document holds one
    feature: {'feature': <name>, 'create': {...}, 'read': {...}, ...}.
    Returns a dict keyed by feature name, or None if there is nothing
    usable (DB down, unreachable, or collection empty).
    """
    try:
        docs = dbc.read(COLLECT_NAME)
    except Exception as err:
        print(f'Could not read security records: {err}')
        return None
    if not docs:
        return None
    return {doc[FEATURE]: {key: val for key, val in doc.items()
                           if key != FEATURE}
            for doc in docs if doc.get(FEATURE)}


def read() -> dict:
    """
    Use the records in the DB; fall back to temp_recs if there are none.
    """
    global security_recs
    security_recs = read_from_db() or temp_recs
    return security_recs


def needs_recs(fn):
    """
    Should be used to decorate any function that directly accesses sec recs.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        global security_recs
        if not security_recs:
            security_recs = read()
        return fn(*args, **kwargs)
    return wrapper


@needs_recs
def read_feature(feature_name: str) -> dict:
    if feature_name in security_recs:
        return security_recs[feature_name]
    else:
        return None


def check_passed(check: str, user_email: str, kwargs: dict) -> bool:
    """
    Run one required security check. Login is real: the caller must
    supply the user's auth code, which is verified against the users DB.
    Any other check still needs its flag passed in as True.
    """
    if check == LOGIN:
        return uqry.verify_auth_code(user_email,
                                     kwargs.get(AUTH_CODE)) is True
    return kwargs.get(check) is True


@needs_recs
def is_permitted(feature_name: str, action: str, user_email: str,
                 **kwargs) -> bool:
    """
    True if user_email may do action on the feature. Pass auth_code=...
    for any feature whose record requires the login check.
    """
    feature = read_feature(feature_name)
    if feature is None:
        return True
    permission = feature.get(action)
    if permission is None:
        return False
    if user_email not in permission.get(USER_LIST, []):
        return False
    return all(check_passed(check, user_email, kwargs)
               for check, required in permission.get(CHECKS, {}).items()
               if required)
