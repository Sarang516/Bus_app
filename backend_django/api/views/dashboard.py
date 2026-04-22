"""
api/views/dashboard.py  –  Summary statistics
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response

from core.db import get_connection

logger = logging.getLogger(__name__)


class DashboardView(APIView):
    """GET /api/dashboard/  –  Overall system statistics."""

    def get(self, request):
        db = get_connection()
        try:
            def count(sql, params=()):
                return db.execute(sql, params).fetchone()[0]

            return Response({
                "total_requests":  count("SELECT COUNT(*) FROM ZHRT_BUS_REQ_MAIN"),
                "draft":           count("SELECT COUNT(*) FROM ZHRT_BUS_REQ_MAIN WHERE STATUS='0001'"),
                "submitted":       count("SELECT COUNT(*) FROM ZHRT_BUS_REQ_MAIN WHERE STATUS='0002'"),
                "approved":        count("SELECT COUNT(*) FROM ZHRT_BUS_REQ_MAIN WHERE STATUS='0003'"),
                "rejected":        count("SELECT COUNT(*) FROM ZHRT_BUS_REQ_MAIN WHERE STATUS='0004'"),
                "allotted":        count("SELECT COUNT(*) FROM ZHRT_BUS_REQ_MAIN WHERE STATUS='0005'"),
                "active_vehicles": count("SELECT COUNT(*) FROM ZHRT_VEHICLE_MST WHERE ACTIVE_FLAG='Y'"),
                "active_drivers":  count("SELECT COUNT(*) FROM ZHRT_DRIVER_MST"),
                "active_mappings": count("SELECT COUNT(*) FROM ZHRT_DRI_VEH_MAP WHERE ENDDA >= CURRENT_DATE"),
            })
        finally:
            db.close()


class MyDashboardView(APIView):
    """GET /api/dashboard/my/<pernr>/  –  Employee's own request statistics."""

    def get(self, request, pernr):
        db = get_connection()
        try:
            def count(sql, params=()):
                return db.execute(sql, params).fetchone()[0]

            return Response({
                "my_total":    count("SELECT COUNT(*) FROM ZHRT_BUS_REQ_MAIN WHERE PERNR=%s", (pernr,)),
                "my_draft":    count("SELECT COUNT(*) FROM ZHRT_BUS_REQ_MAIN WHERE PERNR=%s AND STATUS='0001'", (pernr,)),
                "my_pending":  count("SELECT COUNT(*) FROM ZHRT_BUS_REQ_MAIN WHERE PERNR=%s AND STATUS='0002'", (pernr,)),
                "my_approved": count("SELECT COUNT(*) FROM ZHRT_BUS_REQ_MAIN WHERE PERNR=%s AND STATUS IN ('0003','0005')", (pernr,)),
                "my_rejected": count("SELECT COUNT(*) FROM ZHRT_BUS_REQ_MAIN WHERE PERNR=%s AND STATUS='0004'", (pernr,)),
            })
        finally:
            db.close()
