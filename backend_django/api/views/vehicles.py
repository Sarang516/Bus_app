"""
api/views/vehicles.py  –  ZHRT_VEHICLE_MST CRUD
"""
import logging
from datetime import date, datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from core.db import get_connection

logger = logging.getLogger(__name__)

VALID_TYPES = {"BUS", "SEDAN", "PREMIUM SEDAN", "SUV", "PREMIUM SUV"}


class VehicleListView(APIView):
    """GET /api/vehicles/  –  List vehicles.
       POST /api/vehicles/  –  Create a new vehicle.
    """

    def get(self, request):
        active_only_str = request.GET.get("active_only", "true").lower()
        active_only = active_only_str not in ("false", "0", "no")
        skip  = int(request.GET.get("skip", 0))
        limit = int(request.GET.get("limit", 100))

        where = "WHERE v.ACTIVE_FLAG = 'Y'" if active_only else ""
        sql = f"""
            SELECT v.*,
                   (v.SEATING_CAPACITY - 1)                                          AS EMPLOYEE_CAPACITY,
                   COALESCE(uc.USED_CAPACITY, 0)                                     AS USED_CAPACITY,
                   (v.SEATING_CAPACITY - 1) - COALESCE(uc.USED_CAPACITY, 0)         AS REMAINING_CAPACITY
            FROM ZHRT_VEHICLE_MST v
            LEFT JOIN (
                SELECT ALLOTTED_VEHICLE_NO, COUNT(*) AS USED_CAPACITY
                FROM ZHRT_BUS_REQ_MAIN
                WHERE STATUS = '0005'
                GROUP BY ALLOTTED_VEHICLE_NO
            ) uc ON v.VEHICLE_NO = uc.ALLOTTED_VEHICLE_NO
            {where}
            ORDER BY v.VEHICLE_NO
            LIMIT %s OFFSET %s
        """
        db = get_connection()
        try:
            return Response([dict(r) for r in db.execute(sql, (limit, skip)).fetchall()])
        finally:
            db.close()

    def post(self, request):
        body = request.data
        vehicle_no         = body.get("vehicle_no", "").strip()
        vehicle_type       = body.get("vehicle_type")
        vehicle_category   = body.get("vehicle_category")
        make               = body.get("make")
        model              = body.get("model")
        chassis_no         = body.get("chassis_no")
        engine_no          = body.get("engine_no")
        year_regn          = body.get("year_regn")
        date_purchase      = body.get("date_purchase")
        po_number          = body.get("po_number")
        cost_purchase      = body.get("cost_purchase")
        agency_name        = body.get("agency_name")
        insurance          = body.get("insurance")
        fitness            = body.get("fitness")
        permit             = body.get("permit")
        tax                = body.get("tax")
        tax_valid_upto     = body.get("tax_valid_upto")
        ins_valid_upto     = body.get("ins_valid_upto")
        fitness_valid_upto = body.get("fitness_valid_upto")
        permit_valid_upto  = body.get("permit_valid_upto")
        vehicle_from_date  = body.get("vehicle_from_date", date.today().isoformat())
        vehicle_to_date    = body.get("vehicle_to_date", "9999-12-31")
        seating_capacity   = body.get("seating_capacity", 40)
        created_by         = body.get("created_by", "SYSTEM")

        if not vehicle_no:
            return Response({"detail": "vehicle_no is required."}, status=status.HTTP_400_BAD_REQUEST)

        db = get_connection()
        try:
            if db.execute(
                "SELECT 1 FROM ZHRT_VEHICLE_MST WHERE VEHICLE_NO = %s", (vehicle_no,)
            ).fetchone():
                return Response(
                    {"detail": "Vehicle number already exists."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Date validations
            today = date.today().isoformat()
            for field, label in [
                (tax_valid_upto,     "Tax Valid Upto"),
                (ins_valid_upto,     "Insurance Valid Upto"),
                (fitness_valid_upto, "Fitness Valid Upto"),
                (permit_valid_upto,  "Permit Valid Upto"),
            ]:
                if field and field < today:
                    return Response(
                        {"detail": f"{label} must be today or a future date."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            if vehicle_to_date < vehicle_from_date:
                return Response(
                    {"detail": "Vehicle To Date must be >= Vehicle From Date."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            now = datetime.now().isoformat()
            db.execute(
                """INSERT INTO ZHRT_VEHICLE_MST
                   (VEHICLE_NO, VEHICLE_TYPE, VEHICLE_CATEGORY, MAKE, MODEL, CHASSIS_NO, ENGINE_NO,
                    YEAR_REGN, DATE_PURCHASE, PO_NUMBER, COST_PURCHASE, AGENCY_NAME,
                    INSURANCE, FITNESS, PERMIT, TAX,
                    TAX_VALID_UPTO, INS_VALID_UPTO, FITNESS_VALID_UPTO, PERMIT_VALID_UPTO,
                    VEHICLE_FROM_DATE, VEHICLE_TO_DATE, ACTIVE_FLAG, SEATING_CAPACITY,
                    ZERNAM, ZERDAT, ZERZET)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (vehicle_no, vehicle_type, vehicle_category, make, model,
                 chassis_no, engine_no, year_regn, date_purchase,
                 po_number, cost_purchase, agency_name,
                 insurance, fitness, permit, tax,
                 tax_valid_upto, ins_valid_upto, fitness_valid_upto, permit_valid_upto,
                 vehicle_from_date, vehicle_to_date, "Y", seating_capacity,
                 created_by, today, now)
            )
            db.commit()
            return Response(
                {"message": "Vehicle created successfully", "vehicle_no": vehicle_no},
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            db.rollback()
            logger.exception("Vehicle create error: %s", e)
            return Response({"detail": "An internal error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            db.close()


class VehicleDetailView(APIView):
    """GET/PUT/DELETE /api/vehicles/<vehicle_no>/"""

    def get(self, request, vehicle_no):
        db = get_connection()
        try:
            row = db.execute(
                "SELECT * FROM ZHRT_VEHICLE_MST WHERE VEHICLE_NO = %s", (vehicle_no,)
            ).fetchone()
            if not row:
                return Response({"detail": "Vehicle not found"}, status=status.HTTP_404_NOT_FOUND)
            return Response(dict(row))
        finally:
            db.close()

    def put(self, request, vehicle_no):
        db = get_connection()
        try:
            row = db.execute(
                "SELECT 1 FROM ZHRT_VEHICLE_MST WHERE VEHICLE_NO = %s", (vehicle_no,)
            ).fetchone()
            if not row:
                return Response({"detail": "Vehicle not found"}, status=status.HTTP_404_NOT_FOUND)

            body = request.data
            changed_by = body.get("changed_by", "SYSTEM")

            field_map = {
                "vehicle_type":       "VEHICLE_TYPE",
                "vehicle_category":   "VEHICLE_CATEGORY",
                "make":               "MAKE",
                "model":              "MODEL",
                "chassis_no":         "CHASSIS_NO",
                "engine_no":          "ENGINE_NO",
                "year_regn":          "YEAR_REGN",
                "date_purchase":      "DATE_PURCHASE",
                "po_number":          "PO_NUMBER",
                "cost_purchase":      "COST_PURCHASE",
                "agency_name":        "AGENCY_NAME",
                "insurance":          "INSURANCE",
                "fitness":            "FITNESS",
                "permit":             "PERMIT",
                "tax":                "TAX",
                "tax_valid_upto":     "TAX_VALID_UPTO",
                "ins_valid_upto":     "INS_VALID_UPTO",
                "fitness_valid_upto": "FITNESS_VALID_UPTO",
                "permit_valid_upto":  "PERMIT_VALID_UPTO",
                "vehicle_from_date":  "VEHICLE_FROM_DATE",
                "vehicle_to_date":    "VEHICLE_TO_DATE",
                "seating_capacity":   "SEATING_CAPACITY",
                "active_flag":        "ACTIVE_FLAG",
            }

            updates = {}
            for key, col in field_map.items():
                val = body.get(key)
                if val is not None:
                    updates[col] = val

            if not updates:
                return Response({"detail": "No fields to update"}, status=status.HTTP_400_BAD_REQUEST)

            set_clause = ", ".join(f"{col} = %s" for col in updates)
            values = list(updates.values()) + [datetime.now().isoformat(), changed_by, vehicle_no]
            db.execute(
                f"UPDATE ZHRT_VEHICLE_MST SET {set_clause}, ZAEDAT = %s, ZAENAM = %s WHERE VEHICLE_NO = %s",
                values
            )
            db.commit()
            return Response({"message": "Vehicle updated successfully"})
        except Exception as e:
            db.rollback()
            logger.exception("Vehicle update error for %s: %s", vehicle_no, e)
            return Response({"detail": "An internal error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            db.close()

    def delete(self, request, vehicle_no):
        """Soft-delete: set ACTIVE_FLAG = 'N'."""
        changed_by = request.GET.get("changed_by", "SYSTEM")
        db = get_connection()
        try:
            row = db.execute(
                "SELECT 1 FROM ZHRT_VEHICLE_MST WHERE VEHICLE_NO = %s", (vehicle_no,)
            ).fetchone()
            if not row:
                return Response({"detail": "Vehicle not found"}, status=status.HTTP_404_NOT_FOUND)
            db.execute(
                "UPDATE ZHRT_VEHICLE_MST SET ACTIVE_FLAG = 'N', ZAENAM = %s, ZAEDAT = %s WHERE VEHICLE_NO = %s",
                (changed_by, datetime.now().isoformat(), vehicle_no)
            )
            db.commit()
            return Response({"message": "Vehicle deactivated"})
        except Exception as e:
            db.rollback()
            logger.exception("Vehicle delete error for %s: %s", vehicle_no, e)
            return Response({"detail": "An internal error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            db.close()
