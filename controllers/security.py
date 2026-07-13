"""Decoradores de autorização por tipo de usuário."""
from __future__ import annotations

from functools import wraps

from flask import abort
from flask_login import current_user, login_required


def role_required(*allowed_roles: str):
    normalized = {role.upper() for role in allowed_roles}

    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if current_user.tipo not in normalized:
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator
