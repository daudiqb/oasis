"""Permission checks shared by API write handlers."""
from functools import wraps

from flask import request
import werkzeug.exceptions as wz

import security.security as sec

USER_EMAIL_HEADER = 'X-User-Email'


def needs_permission(feature, action):
    """Require an acting user header and permission to run a handler."""
    def decorate(handler):
        @wraps(handler)
        def wrapped(*args, **kwargs):
            user_email = request.headers.get(USER_EMAIL_HEADER, '').strip()
            if not user_email:
                raise wz.Unauthorized(
                    f'{USER_EMAIL_HEADER} header is required.')
            if not sec.is_permitted(feature, action, user_email):
                raise wz.Forbidden(f'Not permitted to {action} {feature}.')
            return handler(*args, **kwargs)
        return wrapped
    return decorate
