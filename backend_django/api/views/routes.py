"""
api/views/routes.py  –  ZHRT_ROUTE_MAP read endpoints
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from core.db import get_connection

logger = logging.getLogger(__name__)


class RouteListView(APIView):
    """GET /api/routes/  –  Return distinct routes (SEQNR + ROUTE_FROM)."""

    def get(self, request):
        db = get_connection()
        try:
            rows = db.execute(
                """SELECT SEQNR, ROUTE_FROM
                   FROM ZHRT_ROUTE_MAP
                   WHERE ENDDA >= CURRENT_DATE
                   GROUP BY SEQNR, ROUTE_FROM
                   ORDER BY SEQNR"""
            ).fetchall()
            return Response([dict(r) for r in rows])
        finally:
            db.close()


class RoutePickupsView(APIView):
    """GET /api/routes/<seqnr>/pickups/  –  Return all pick-up points for a given route."""

    def get(self, request, seqnr):
        db = get_connection()
        try:
            rows = db.execute(
                """SELECT SUB_SEQNR, PICK_UP_POINT
                   FROM ZHRT_ROUTE_MAP
                   WHERE SEQNR = %s AND ENDDA >= CURRENT_DATE
                   ORDER BY SUB_SEQNR""",
                (seqnr,)
            ).fetchall()
            if not rows:
                return Response({"detail": "Route not found"}, status=status.HTTP_404_NOT_FOUND)
            return Response([dict(r) for r in rows])
        finally:
            db.close()
