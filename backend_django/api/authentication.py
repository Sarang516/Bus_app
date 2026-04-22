"""
api/authentication.py  –  Custom JWT DRF authentication class
"""
import logging
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from core.security import decode_token

logger = logging.getLogger(__name__)


class JWTUser:
    """
    Thin wrapper around the JWT payload dict.
    Exposes is_authenticated=True so DRF's IsAuthenticated permission works,
    while still supporting .get() / [] access for all view code.
    """
    is_authenticated = True

    def __init__(self, payload: dict):
        self._payload = payload

    def get(self, key, default=None):
        return self._payload.get(key, default)

    def __getitem__(self, key):
        return self._payload[key]

    def __contains__(self, key):
        return key in self._payload

    def __repr__(self):
        return f"JWTUser(sub={self._payload.get('sub')}, role={self._payload.get('role')})"


class JWTAuthentication(BaseAuthentication):
    """
    Reads JWT from the Authorization: Bearer <token> header.
    Returns (JWTUser, token) on success so request.user works with DRF permissions.
    """

    def authenticate(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None

        token = parts[1]
        try:
            payload = decode_token(token)
        except ValueError:
            raise AuthenticationFailed("Invalid or expired token. Please log in again.")

        return (JWTUser(payload), token)

    def authenticate_header(self, request):
        return "Bearer"
