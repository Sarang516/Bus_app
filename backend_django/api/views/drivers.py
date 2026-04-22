"""
api/views/drivers.py  –  ZHRT_DRIVER_MST CRUD
"""
import logging
from datetime import date, datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from core.db import get_connection

logger = logging.getLogger(__name__)


def _next_driver_id(db) -> str:
    """Auto-generate next DRIVER_ID as DRV + serial number."""
    row = db.execute(
        "SELECT DRIVER_ID FROM ZHRT_DRIVER_MST ORDER BY DRIVER_ID DESC LIMIT 1"
    ).fetchone()
    if row:
        last = row["DRIVER_ID"]  # e.g. DRV004
        try:
            num = int(last.replace("DRV", "")) + 1
        except ValueError:
            num = 1
    else:
        num = 1
    return f"DRV{num:03d}"


class DriverListView(APIView):
    """GET /api/drivers/  –  List all drivers.
       POST /api/drivers/  –  Create a new driver.
    """

    def get(self, request):
        skip  = int(request.GET.get("skip", 0))
        limit = int(request.GET.get("limit", 100))

        db = get_connection()
        try:
            rows = db.execute(
                "SELECT * FROM ZHRT_DRIVER_MST ORDER BY DRIVER_NAME LIMIT %s OFFSET %s",
                (limit, skip),
            ).fetchall()
            return Response([dict(r) for r in rows])
        finally:
            db.close()

    def post(self, request):
        body       = request.data
        driver_name = body.get("driver_name", "").strip()
        mobile_no1  = body.get("mobile_no1", "").strip()
        mobile_no2  = body.get("mobile_no2")
        address     = body.get("address")
        dob         = body.get("dob")
        dl_no       = body.get("dl_no")
        valid_upto  = body.get("valid_upto")
        begda       = body.get("begda", date.today().isoformat())
        endda       = body.get("endda", "9999-12-31")
        driver_id   = body.get("driver_id", "").strip()
        created_by  = body.get("created_by", "SYSTEM")

        if not driver_name or not mobile_no1:
            return Response(
                {"detail": "driver_name and mobile_no1 are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        db = get_connection()
        try:
            # Duplicate mobile check
            if db.execute(
                "SELECT 1 FROM ZHRT_DRIVER_MST WHERE MOBILE_NO1 = %s", (mobile_no1,)
            ).fetchone():
                return Response(
                    {"detail": f"A driver with mobile number {mobile_no1} already exists."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # DOB cannot be future
            if dob and dob > date.today().isoformat():
                return Response(
                    {"detail": "Date of Birth cannot be a future date."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Auto-generate Driver ID if not provided
            if not driver_id:
                driver_id = _next_driver_id(db)

            # Duplicate driver_id check
            if db.execute(
                "SELECT 1 FROM ZHRT_DRIVER_MST WHERE DRIVER_ID = %s", (driver_id,)
            ).fetchone():
                return Response(
                    {"detail": f"Driver ID {driver_id} already exists."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            now   = datetime.now().isoformat()
            today = date.today().isoformat()

            db.execute(
                """INSERT INTO ZHRT_DRIVER_MST
                   (DRIVER_ID, DRIVER_NAME, MOBILE_NO1, MOBILE_NO2, ADDRESS, DOB, DL_NO, VALID_UPTO,
                    BEGDA, ENDDA, ZERNAM, ZERDAT, ZERZET)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (driver_id, driver_name, mobile_no1, mobile_no2,
                 address, dob, dl_no, valid_upto,
                 begda, endda, created_by, today, now)
            )
            db.commit()
            return Response(
                {"message": "Driver created successfully", "driver_id": driver_id},
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            db.rollback()
            logger.exception("Driver create error: %s", e)
            return Response({"detail": "An internal error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            db.close()


class DriverDetailView(APIView):
    """GET/PUT/DELETE /api/drivers/<driver_id>/"""

    def get(self, request, driver_id):
        db = get_connection()
        try:
            row = db.execute(
                "SELECT * FROM ZHRT_DRIVER_MST WHERE DRIVER_ID = %s", (driver_id,)
            ).fetchone()
            if not row:
                return Response({"detail": "Driver not found"}, status=status.HTTP_404_NOT_FOUND)
            return Response(dict(row))
        finally:
            db.close()

    def put(self, request, driver_id):
        db = get_connection()
        try:
            row = db.execute(
                "SELECT 1 FROM ZHRT_DRIVER_MST WHERE DRIVER_ID = %s", (driver_id,)
            ).fetchone()
            if not row:
                return Response({"detail": "Driver not found"}, status=status.HTTP_404_NOT_FOUND)

            body = request.data
            changed_by = body.get("changed_by", "SYSTEM")

            field_map = {
                "driver_name": "DRIVER_NAME",
                "mobile_no1":  "MOBILE_NO1",
                "mobile_no2":  "MOBILE_NO2",
                "address":     "ADDRESS",
                "dob":         "DOB",
                "dl_no":       "DL_NO",
                "valid_upto":  "VALID_UPTO",
                "begda":       "BEGDA",
                "endda":       "ENDDA",
            }

            updates = {}
            for key, col in field_map.items():
                val = body.get(key)
                if val is not None:
                    updates[col] = val

            if not updates:
                return Response({"detail": "No fields to update"}, status=status.HTTP_400_BAD_REQUEST)

            set_clause = ", ".join(f"{col} = %s" for col in updates)
            values = list(updates.values()) + [datetime.now().isoformat(), changed_by, driver_id]
            db.execute(
                f"UPDATE ZHRT_DRIVER_MST SET {set_clause}, ZAEDAT = %s, ZAENAM = %s WHERE DRIVER_ID = %s",
                values
            )
            db.commit()
            return Response({"message": "Driver updated successfully"})
        except Exception as e:
            db.rollback()
            logger.exception("Driver update error for %s: %s", driver_id, e)
            return Response({"detail": "An internal error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            db.close()

    def delete(self, request, driver_id):
        db = get_connection()
        try:
            # Check if driver is mapped to any active vehicle
            mapping = db.execute(
                "SELECT 1 FROM ZHRT_DRI_VEH_MAP WHERE DRIVER_ID = %s AND ENDDA >= CURRENT_DATE",
                (driver_id,)
            ).fetchone()
            if mapping:
                return Response(
                    {"detail": "Cannot delete driver – active vehicle mapping exists. Remove mapping first."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            db.execute("DELETE FROM ZHRT_DRIVER_MST WHERE DRIVER_ID = %s", (driver_id,))
            db.commit()
            return Response({"message": "Driver deleted"})
        except Exception as e:
            db.rollback()
            logger.exception("Driver delete error for %s: %s", driver_id, e)
            return Response({"detail": "An internal error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            db.close()
