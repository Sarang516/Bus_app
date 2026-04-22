"""
api/views/employees.py  –  ZEMP_MASTER_TABLE READ + profile update operations
"""
import logging
from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from core.db import get_connection
from core.security import hash_password, verify_password

logger = logging.getLogger(__name__)


class EmployeeListView(APIView):
    """GET /api/employees/  –  List employees with optional search and pagination."""

    def get(self, request):
        skip   = int(request.GET.get("skip", 0))
        limit  = int(request.GET.get("limit", 100))
        search = request.GET.get("search", "").strip()

        db = get_connection()
        try:
            if search:
                rows = db.execute(
                    "SELECT * FROM ZEMP_MASTER_TABLE WHERE ENAME LIKE %s OR PERNR LIKE %s ORDER BY ENAME LIMIT %s OFFSET %s",
                    (f"%{search}%", f"%{search}%", limit, skip),
                ).fetchall()
            else:
                rows = db.execute(
                    "SELECT * FROM ZEMP_MASTER_TABLE ORDER BY ENAME LIMIT %s OFFSET %s",
                    (limit, skip),
                ).fetchall()
            return Response([dict(r) for r in rows])
        finally:
            db.close()


class EmployeeWithAllotmentView(APIView):
    """GET /api/employees/with-allotment/  –  All employees with latest allotted vehicle & driver."""

    def get(self, request):
        db = get_connection()
        try:
            rows = db.execute("""
                SELECT
                    e.PERNR, e.ENAME, e.DESIGNATION, e.DEPARTMENT,
                    r.REQID, r.ROUTE_NO, r.PICK_UP_POINT, r.STATUS,
                    r.ALLOTTED_VEHICLE_NO, r.ALLOTTED_DRIVER_ID,
                    v.VEHICLE_TYPE, v.MAKE, v.MODEL,
                    d.DRIVER_NAME, d.MOBILE_NO1 AS DRIVER_MOBILE
                FROM ZEMP_MASTER_TABLE e
                LEFT JOIN ZHRT_BUS_REQ_MAIN r
                    ON e.PERNR = r.PERNR AND r.STATUS = '0005'
                    AND r.REQID = (
                        SELECT REQID FROM ZHRT_BUS_REQ_MAIN
                        WHERE PERNR = e.PERNR AND STATUS = '0005'
                        ORDER BY REQUEST_CREATION_DATE DESC LIMIT 1
                    )
                LEFT JOIN ZHRT_VEHICLE_MST v ON r.ALLOTTED_VEHICLE_NO = v.VEHICLE_NO
                LEFT JOIN ZHRT_DRIVER_MST  d ON r.ALLOTTED_DRIVER_ID  = d.DRIVER_ID
                ORDER BY e.ENAME
            """).fetchall()
            return Response([dict(r) for r in rows])
        finally:
            db.close()


class EmployeeDetailView(APIView):
    """GET/PUT /api/employees/<pernr>/"""

    def get(self, request, pernr):
        db = get_connection()
        try:
            row = db.execute(
                "SELECT * FROM ZEMP_MASTER_TABLE WHERE PERNR = %s", (pernr,)
            ).fetchone()
            if not row:
                return Response({"detail": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)
            return Response(dict(row))
        finally:
            db.close()

    def put(self, request, pernr):
        """Employee updates their own profile details and optionally changes password."""
        db = get_connection()
        try:
            row = db.execute(
                "SELECT * FROM ZEMP_MASTER_TABLE WHERE PERNR = %s", (pernr,)
            ).fetchone()
            if not row:
                return Response({"detail": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)

            body = request.data
            updates = {}

            if body.get("ename"):
                updates["ENAME"] = body["ename"]
            if body.get("designation") is not None:
                updates["DESIGNATION"] = body["designation"]
            if body.get("department") is not None:
                updates["DEPARTMENT"] = body["department"]
            if body.get("address") is not None:
                updates["STRAS"] = body["address"]
            if body.get("email") is not None:
                updates["EMAIL"] = body["email"]
            if body.get("mobile_no") is not None:
                updates["MOBILE_NO"] = body["mobile_no"]
            if body.get("profile_photo") is not None:
                updates["PROFILE_PHOTO"] = body["profile_photo"]

            # Password change — require current password verification
            new_password = body.get("new_password")
            if new_password:
                current_password = body.get("current_password")
                if not current_password:
                    return Response(
                        {"detail": "Current password is required to set a new password."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                if not verify_password(current_password, row["PASSWORD"]):
                    return Response(
                        {"detail": "Current password is incorrect."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                errors = []
                if len(new_password) < 8:
                    errors.append("at least 8 characters")
                if not any(c.isupper() for c in new_password):
                    errors.append("one uppercase letter")
                if not any(c.isdigit() for c in new_password):
                    errors.append("one number")
                if errors:
                    return Response(
                        {"detail": f"Password must contain: {', '.join(errors)}."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                updates["PASSWORD"] = hash_password(new_password)

            if not updates:
                return Response({"detail": "No fields to update."}, status=status.HTTP_400_BAD_REQUEST)

            set_clause = ", ".join(f"{k} = %s" for k in updates)
            values = list(updates.values()) + [datetime.now().isoformat(), pernr]
            db.execute(
                f"UPDATE ZEMP_MASTER_TABLE SET {set_clause}, ZAEDAT = %s WHERE PERNR = %s",
                values
            )
            db.commit()

            updated = db.execute(
                "SELECT * FROM ZEMP_MASTER_TABLE WHERE PERNR = %s", (pernr,)
            ).fetchone()
            return Response({
                "message":       "Profile updated successfully",
                "pernr":         updated["PERNR"],
                "ename":         updated["ENAME"],
                "role":          updated["ROLE"],
                "designation":   updated["DESIGNATION"],
                "department":    updated["DEPARTMENT"],
                "address":       updated["STRAS"],
                "email":         updated["EMAIL"],
                "mobile_no":     updated["MOBILE_NO"],
                "profile_photo": updated["PROFILE_PHOTO"],
            })
        except Exception as e:
            db.rollback()
            logger.exception("Employee update error for %s: %s", pernr, e)
            return Response({"detail": "An internal error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            db.close()
