"""
api/throttling.py  –  Login rate limiting
"""
from rest_framework.throttling import AnonRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    rate = "5/min"
    scope = "login"
