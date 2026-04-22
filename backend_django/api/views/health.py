"""
api/views/health.py  –  Health check and root endpoints
"""
import os
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from core.db import get_connection

logger = logging.getLogger(__name__)

APP_ENV = os.environ.get("APP_ENV", "production")


class HealthView(APIView):
    """GET /api/health/  –  Returns {status, version, db, env}."""
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            conn = get_connection()
            conn.execute("SELECT 1")
            conn.close()
            db_status = "ok"
        except Exception as e:
            logger.error("DB health check failed: %s", e)
            db_status = "error"

        return Response({
            "status":  "ok" if db_status == "ok" else "degraded",
            "version": "2.0.0",
            "db":      db_status,
            "env":     APP_ENV,
        })


class RootView(APIView):
    """GET /  –  App info."""
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
            "app":     "Bus Transportation Booking System",
            "version": "2.0.0",
            "docs":    "/api/health/",
            "health":  "/api/health/",
            "status":  "running",
        })
