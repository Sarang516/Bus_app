"""
api/exceptions.py  –  Custom exception handler for DRF
"""
import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that ensures all errors return
    a consistent JSON format with a 'detail' key.
    """
    response = exception_handler(exc, context)

    if response is not None:
        return response

    # For unhandled exceptions, return 500
    logger.exception("Unhandled error: %s", exc)
    return Response({"detail": "An internal error occurred."}, status=500)
