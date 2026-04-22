"""
api/views/mappings.py  –  ZHRT_DRI_VEH_MAP CRUD
"""
import logging
from datetime import date, datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from core.db import get_connection

logger = logging.getLogger(__name__)


class MappingListView(APIView):
    """GET /api/mappings/  –  List all driver-vehicle mappings.
       POST /api/mappings/  –  Create a new mapping.
    """

    def get(self, request):
        active_only_str = request.GET.get("active_only", "false").lower()
        active_only = active_only_str in ("true", "1", "yes")

        db = get_connection()
        try:
            if active_only:
                sql = "SELECT * FROM ZHRT_DRI_VEH_MAP WHERE ENDDA >= CURRENT_DATE ORDER BY DATE_MAP DESC"
            else:
                sql = "SELECT * FROM ZHRT_DRI_VEH_MAP ORDER BY DATE_MAP DESC"
            return Response([dict(r) for r in db.execute(sql).fetchall()])
        finally:
            db.close()

    def post(self, request):
        body        = request.data
        vehicle_no  = body.get("vehicle_no", "").strip()
        driver_id   = body.get("driver_id", "").strip()
        vehicle_type = body.get("vehicle_type", "").strip()
        begda       = body.get("begda", date.today().isoformat())
        endda       = body.get("endda", "9999-12-31")
        created_by  = body.get("created_by", "SYSTEM")

        if not vehicle_no or not driver_id:
            return Response(
                {"detail": "vehicle_no and driver_id are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        db = get_connection()
        try:
            # Duplicate check
            if db.execute(
                """SELECT 1 FROM ZHRT_DRI_VEH_MAP
                   WHERE VEHICLE_NO = %s AND DRIVER_ID = %s AND ENDDA >= CURRENT_DATE""",
                (vehicle_no, driver_id)
            ).fetchone():
                return Response(
                    {"detail": "An active mapping for this vehicle and driver already exists."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            driver = db.execute(
                "SELECT * FROM ZHRT_DRIVER_MST WHERE DRIVER_ID = %s", (driver_id,)
            ).fetchone()
            if not driver:
                return Response({"detail": "Driver not found"}, status=status.HTTP_404_NOT_FOUND)

            vehicle = db.execute(
                "SELECT 1 FROM ZHRT_VEHICLE_MST WHERE VEHICLE_NO = %s AND ACTIVE_FLAG = 'Y'",
                (vehicle_no,)
            ).fetchone()
            if not vehicle:
                return Response({"detail": "Vehicle not found or inactive"}, status=status.HTTP_404_NOT_FOUND)

            now    = datetime.now().isoformat()
            today  = date.today().isoformat()
            map_id = f"MAP{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

            db.execute(
                """INSERT INTO ZHRT_DRI_VEH_MAP
                   (MAP_ID, VEHICLE_TYPE, VEHICLE_NO, DRIVER_ID, DRIVER_NAME, MOBILE_NO1,
                    BEGDA, ENDDA, DATE_MAP, ZERNAM, ZERDAT, ZERZET)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (map_id, vehicle_type, vehicle_no, driver_id,
                 driver["DRIVER_NAME"], driver["MOBILE_NO1"],
                 begda, endda, today, created_by, today, now)
            )
            db.commit()
            return Response(
                {"message": "Mapping created", "map_id": map_id},
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            db.rollback()
            logger.exception("Mapping create error: %s", e)
            return Response({"detail": "An internal error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            db.close()


class MappingDetailView(APIView):
    """DELETE /api/mappings/<map_id>/  –  End a mapping."""

    def delete(self, request, map_id):
        ended_by = request.GET.get("ended_by", "SYSTEM")
        db = get_connection()
        try:
            row = db.execute(
                "SELECT 1 FROM ZHRT_DRI_VEH_MAP WHERE MAP_ID = %s", (map_id,)
            ).fetchone()
            if not row:
                return Response({"detail": "Mapping not found"}, status=status.HTTP_404_NOT_FOUND)
            db.execute(
                "UPDATE ZHRT_DRI_VEH_MAP SET ENDDA = CURRENT_DATE, ZAENAM = %s, ZAEDAT = %s WHERE MAP_ID = %s",
                (ended_by, datetime.now().isoformat(), map_id)
            )
            db.commit()
            return Response({"message": "Mapping ended"})
        except Exception as e:
            db.rollback()
            logger.exception("Mapping delete error for %s: %s", map_id, e)
            return Response({"detail": "An internal error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            db.close()
