"""
api/views/requests.py  –  ZHRT_BUS_REQ_MAIN full workflow
"""
import logging
import uuid
from datetime import datetime, date
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from core.db import get_connection

logger = logging.getLogger(__name__)

# ── Status constants ──────────────────────────────────────────────────────────
STATUS = {
    "0001": "Draft",
    "0002": "Submitted",
    "0003": "Approved",
    "0004": "Rejected",
    "0005": "Vehicle Allotted",
    "0006": "Withdrawn",
}

VALID_TRANSITIONS = {
    "SUBMIT":   ("0001", "0002"),
    "APPROVE":  ("0002", "0003"),
    "REJECT":   ("0002", "0004"),
    "ALLOT":    ("0003", "0005"),
    "WITHDRAW": (("0001", "0002", "0003"), "0006"),
}


def _gen_reqid():
    ts  = datetime.now().strftime("%Y%m%d%H%M%S")
    uid = str(uuid.uuid4()).replace("-", "")[:6].upper()
    return f"REQ{ts}{uid}"


def _log(db, reqid, seqnr, action_by, curr, new, pending,
         req_type, app_type, route, pickup, station, d1, d2, remarks):
    log_id = f"LOG{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    db.execute(
        """INSERT INTO ZHRT_BUS_REQ_LOGS
           (LOG_ID, REQID, SEQNR, ACTION_BY, ACTION_ON,
            CURR_REQUEST_STATUS, NEW_REQUEST_STATUS, PENDING_WITH,
            REQUEST_TYPE, APPLICATION_TYPE, ROUTE_NO, PICK_UP_POINT,
            NEAREST_STATION, DIST_PICKUP_RESIDENCE, DIST_RESIDENCE_STATION, REMARKS)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (log_id, reqid, seqnr, action_by, datetime.now().isoformat(),
         curr, new, pending, req_type, app_type, route, pickup,
         station, d1, d2, remarks or "")
    )


class RequestListView(APIView):
    """GET /api/requests/  –  List requests (filtered by role/pernr).
       POST /api/requests/  –  Create a new request.
    """

    def get(self, request):
        pernr         = request.GET.get("pernr")
        role          = request.GET.get("role")
        status_filter = request.GET.get("status_filter")
        skip          = int(request.GET.get("skip", 0))
        limit         = int(request.GET.get("limit", 100))

        base = """
            SELECT r.*,
                   rm.ROUTE_FROM,
                   pw.ENAME AS PENDING_WITH_NAME
            FROM ZHRT_BUS_REQ_MAIN r
            LEFT JOIN (SELECT DISTINCT SEQNR, ROUTE_FROM FROM ZHRT_ROUTE_MAP) rm
                   ON r.ROUTE_NO = rm.SEQNR
            LEFT JOIN ZEMP_MASTER_TABLE pw ON r.PENDING_WITH = pw.PERNR
        """

        if role == "APPROVER":
            where, params = "", []
        elif role == "TRANSPORT_ADMIN":
            where, params = "WHERE r.STATUS IN ('0003','0005','0006')", []
        else:
            where, params = "WHERE (r.PERNR = %s OR r.REQUEST_CREATED_BY = %s)", [pernr, pernr]

        if status_filter:
            connector = "AND" if where else "WHERE"
            where  += f" {connector} r.STATUS = %s"
            params.append(status_filter)

        sql  = base + where + " ORDER BY r.REQUEST_CREATION_DATE DESC LIMIT %s OFFSET %s"

        db = get_connection()
        try:
            rows = db.execute(sql, params + [limit, skip]).fetchall()
            result = []
            for r in rows:
                d = dict(r)
                d["STATUS_TEXT"] = STATUS.get(d["STATUS"], d["STATUS"])
                result.append(d)
            return Response(result)
        finally:
            db.close()

    def post(self, request):
        body = request.data

        pernr                  = body.get("pernr", "").strip()
        pass_type              = body.get("pass_type", "").strip()
        application_type       = body.get("application_type", "").strip()
        reason                 = body.get("reason", "").strip()
        route_no               = body.get("route_no", "").strip()
        pick_up_point          = body.get("pick_up_point", "").strip()
        nearest_station        = body.get("nearest_station", "").strip()
        dist_pickup_residence  = body.get("dist_pickup_residence", 0)
        dist_residence_station = body.get("dist_residence_station", 0)
        effective_date         = body.get("effective_date", "").strip()
        attachment             = body.get("attachment")
        on_behalf_of           = body.get("on_behalf_of")

        if not all([pernr, pass_type, application_type, reason, route_no, pick_up_point, nearest_station, effective_date]):
            return Response(
                {"detail": "pernr, pass_type, application_type, reason, route_no, pick_up_point, nearest_station, effective_date are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        db = get_connection()
        try:
            # Employee must exist
            emp = db.execute(
                "SELECT * FROM ZEMP_MASTER_TABLE WHERE PERNR = %s", (pernr,)
            ).fetchone()
            if not emp:
                return Response({"detail": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)

            # Route must exist
            route_row = db.execute(
                "SELECT 1 FROM ZHRT_ROUTE_MAP WHERE SEQNR = %s AND PICK_UP_POINT = %s",
                (route_no, pick_up_point)
            ).fetchone()
            if not route_row:
                return Response(
                    {"detail": "Selected route / pick-up point is invalid."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Determine who created it (on-behalf scenario)
            created_by = on_behalf_of if on_behalf_of else pernr
            now   = datetime.now().isoformat()

            # Auto-assign to first APPROVER
            approver = db.execute(
                "SELECT PERNR FROM ZEMP_MASTER_TABLE WHERE ROLE = 'APPROVER' LIMIT 1"
            ).fetchone()
            pending_with = approver["PERNR"] if approver else None

            reqid = _gen_reqid()

            db.execute(
                """INSERT INTO ZHRT_BUS_REQ_MAIN
                   (REQID, PERNR, PASS_TYPE, APPLICATION_TYPE, REASON,
                    ROUTE_NO, PICK_UP_POINT, NEAREST_STATION,
                    DIST_PICKUP_RESIDENCE, DIST_RESIDENCE_STATION,
                    EFFECTIVE_DATE, ATTACHMENT, STATUS, PENDING_WITH,
                    REQUEST_CREATED_BY, REQUEST_CREATION_DATE, CHANGED_ON, CHANGED_BY)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (reqid, pernr, pass_type, application_type, reason,
                 route_no, pick_up_point, nearest_station,
                 dist_pickup_residence, dist_residence_station,
                 effective_date, attachment,
                 "0001", pending_with, created_by, now, now, created_by)
            )

            _log(db, reqid, 1, created_by, "0000", "0001", pending_with,
                 "CREATE", application_type, route_no, pick_up_point,
                 nearest_station, dist_pickup_residence, dist_residence_station,
                 "Request created as draft")
            db.commit()

            return Response({
                "reqid":       reqid,
                "status":      "0001",
                "status_text": "Draft",
                "message":     "Request saved as Draft."
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            db.rollback()
            logger.exception("Request create error: %s", e)
            return Response({"detail": "An internal error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            db.close()


class AdminAllotView(APIView):
    """POST /api/requests/admin-allot/  –  Admin direct allotment (bypasses request workflow)."""

    def post(self, request):
        body        = request.data
        pernr       = body.get("pernr", "").strip()
        vehicle_no  = body.get("vehicle_no", "").strip()
        driver_id   = body.get("driver_id", "").strip()
        remarks     = body.get("remarks")
        allotted_by = body.get("allotted_by", "SYSTEM")

        if not all([pernr, vehicle_no, driver_id]):
            return Response(
                {"detail": "pernr, vehicle_no, and driver_id are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        db = get_connection()
        try:
            emp = db.execute(
                "SELECT * FROM ZEMP_MASTER_TABLE WHERE PERNR = %s", (pernr,)
            ).fetchone()
            if not emp:
                return Response({"detail": "Employee not found."}, status=status.HTTP_404_NOT_FOUND)

            vehicle = db.execute(
                "SELECT * FROM ZHRT_VEHICLE_MST WHERE VEHICLE_NO = %s AND ACTIVE_FLAG = 'Y'",
                (vehicle_no,)
            ).fetchone()
            if not vehicle:
                return Response({"detail": "Vehicle not found or inactive."}, status=status.HTTP_400_BAD_REQUEST)

            driver = db.execute(
                "SELECT * FROM ZHRT_DRIVER_MST WHERE DRIVER_ID = %s", (driver_id,)
            ).fetchone()
            if not driver:
                return Response({"detail": "Driver not found."}, status=status.HTTP_400_BAD_REQUEST)

            now   = datetime.now().isoformat()
            today = date.today().isoformat()
            reqid = _gen_reqid()

            db.execute(
                """INSERT INTO ZHRT_BUS_REQ_MAIN
                   (REQID, PERNR, PASS_TYPE, APPLICATION_TYPE, REASON,
                    ROUTE_NO, PICK_UP_POINT, NEAREST_STATION,
                    DIST_PICKUP_RESIDENCE, DIST_RESIDENCE_STATION,
                    EFFECTIVE_DATE, STATUS, PENDING_WITH,
                    REQUEST_CREATED_BY, REQUEST_CREATION_DATE, CHANGED_ON, CHANGED_BY,
                    ALLOTTED_VEHICLE_NO, ALLOTTED_DRIVER_ID, REMARKS)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (reqid, pernr, "STAFF", "DIRECT", "Admin Direct Allotment",
                 "00", "Direct Assignment", "N/A", 0, 0,
                 today, "0005", None,
                 allotted_by, now, now, allotted_by,
                 vehicle_no, driver_id, remarks or "Admin direct allotment")
            )

            _log(db, reqid, 1, allotted_by, None, "0005", None,
                 "ALLOT", "DIRECT", "00", "Direct Assignment",
                 "N/A", 0, 0, remarks or "Admin direct allotment")

            db.commit()
            return Response({
                "message":    "Vehicle and driver allotted to employee successfully.",
                "reqid":      reqid,
                "pernr":      pernr,
                "vehicle_no": vehicle_no,
                "driver_id":  driver_id,
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            db.rollback()
            logger.exception("Admin allot error: %s", e)
            return Response({"detail": "An internal error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            db.close()


class RequestDetailView(APIView):
    """GET/PUT /api/requests/<reqid>/"""

    def get(self, request, reqid):
        db = get_connection()
        try:
            row = db.execute(
                "SELECT * FROM ZHRT_BUS_REQ_MAIN WHERE REQID = %s", (reqid,)
            ).fetchone()
            if not row:
                return Response({"detail": "Request not found"}, status=status.HTTP_404_NOT_FOUND)

            d = dict(row)
            d["STATUS_TEXT"] = STATUS.get(d["STATUS"], d["STATUS"])

            emp = db.execute(
                "SELECT PERNR, ENAME, DESIGNATION, DEPARTMENT, STRAS "
                "FROM ZEMP_MASTER_TABLE WHERE PERNR = %s", (d["PERNR"],)
            ).fetchone()
            d["EMPLOYEE"] = dict(emp) if emp else {}

            # Resolve route description
            route_row = db.execute(
                "SELECT DISTINCT ROUTE_FROM FROM ZHRT_ROUTE_MAP WHERE SEQNR = %s", (d["ROUTE_NO"],)
            ).fetchone()
            d["ROUTE_FROM"] = route_row["ROUTE_FROM"] if route_row else None

            # Resolve PENDING_WITH PERNR → name
            if d.get("PENDING_WITH"):
                pw = db.execute(
                    "SELECT ENAME FROM ZEMP_MASTER_TABLE WHERE PERNR = %s", (d["PENDING_WITH"],)
                ).fetchone()
                d["PENDING_WITH_NAME"] = pw["ENAME"] if pw else d["PENDING_WITH"]

            # Vehicle & Driver info if allotted
            if d.get("ALLOTTED_VEHICLE_NO"):
                veh = db.execute(
                    "SELECT VEHICLE_NO, VEHICLE_TYPE, MAKE, MODEL FROM ZHRT_VEHICLE_MST WHERE VEHICLE_NO = %s",
                    (d["ALLOTTED_VEHICLE_NO"],)
                ).fetchone()
                d["VEHICLE_INFO"] = dict(veh) if veh else {}

            if d.get("ALLOTTED_DRIVER_ID"):
                drv = db.execute(
                    "SELECT DRIVER_ID, DRIVER_NAME, MOBILE_NO1 FROM ZHRT_DRIVER_MST WHERE DRIVER_ID = %s",
                    (d["ALLOTTED_DRIVER_ID"],)
                ).fetchone()
                d["DRIVER_INFO"] = dict(drv) if drv else {}

            logs = db.execute(
                """SELECT l.*, COALESCE(e.ENAME, l.ACTION_BY) AS ACTION_BY_NAME
                   FROM ZHRT_BUS_REQ_LOGS l
                   LEFT JOIN ZEMP_MASTER_TABLE e ON l.ACTION_BY = e.PERNR
                   WHERE l.REQID = %s ORDER BY l.SEQNR""",
                (reqid,)
            ).fetchall()
            d["LOGS"] = [dict(l) for l in logs]

            return Response(d)
        finally:
            db.close()

    def put(self, request, reqid):
        """Update a draft request."""
        body = request.data

        db = get_connection()
        try:
            req = db.execute(
                "SELECT STATUS FROM ZHRT_BUS_REQ_MAIN WHERE REQID = %s", (reqid,)
            ).fetchone()
            if not req:
                return Response({"detail": "Request not found."}, status=status.HTTP_404_NOT_FOUND)
            if req["STATUS"] != "0001":
                return Response({"detail": "Only Draft requests can be edited."}, status=status.HTTP_400_BAD_REQUEST)

            route_no    = body.get("route_no", "")
            pick_up_point = body.get("pick_up_point", "")

            # Validate route/pickup still exist
            if not db.execute(
                "SELECT 1 FROM ZHRT_ROUTE_MAP WHERE SEQNR = %s AND PICK_UP_POINT = %s",
                (route_no, pick_up_point)
            ).fetchone():
                return Response(
                    {"detail": "Selected route / pick-up point is invalid."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            now = datetime.now().isoformat()
            db.execute(
                """UPDATE ZHRT_BUS_REQ_MAIN SET
                       PASS_TYPE=%s, APPLICATION_TYPE=%s, REASON=%s,
                       ROUTE_NO=%s, PICK_UP_POINT=%s, NEAREST_STATION=%s,
                       DIST_PICKUP_RESIDENCE=%s, DIST_RESIDENCE_STATION=%s,
                       EFFECTIVE_DATE=%s, ATTACHMENT=%s, CHANGED_ON=%s, CHANGED_BY=%s
                   WHERE REQID=%s""",
                (body.get("pass_type"), body.get("application_type"), body.get("reason"),
                 route_no, pick_up_point, body.get("nearest_station"),
                 body.get("dist_pickup_residence", 0), body.get("dist_residence_station", 0),
                 body.get("effective_date"), body.get("attachment"), now, body.get("pernr"), reqid)
            )
            db.commit()
            return Response({"message": "Draft updated successfully.", "reqid": reqid})
        except Exception as e:
            db.rollback()
            logger.exception("Request update error for %s: %s", reqid, e)
            return Response({"detail": "An internal error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            db.close()


class RequestActionView(APIView):
    """PUT /api/requests/<reqid>/action/  –  Submit / Approve / Reject / Allot / Withdraw."""

    def put(self, request, reqid):
        body = request.data

        db = get_connection()
        try:
            req = db.execute(
                "SELECT * FROM ZHRT_BUS_REQ_MAIN WHERE REQID = %s", (reqid,)
            ).fetchone()
            if not req:
                return Response({"detail": "Request not found"}, status=status.HTTP_404_NOT_FOUND)

            action = (body.get("action") or "").upper()
            if action not in VALID_TRANSITIONS:
                return Response(
                    {"detail": f"Unknown action '{action}'"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            expected_curr, new_status = VALID_TRANSITIONS[action]
            allowed = (expected_curr,) if isinstance(expected_curr, str) else expected_curr
            if req["STATUS"] not in allowed:
                return Response(
                    {"detail": f"Cannot perform '{action}' on a request with status '{STATUS.get(req['STATUS'])}'."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            now  = datetime.now().isoformat()
            curr = req["STATUS"]

            # Determine next pending_with
            if action == "SUBMIT":
                approver = db.execute(
                    "SELECT PERNR FROM ZEMP_MASTER_TABLE WHERE ROLE = 'APPROVER' LIMIT 1"
                ).fetchone()
                pending_with = approver["PERNR"] if approver else None
            elif action == "APPROVE":
                admin = db.execute(
                    "SELECT PERNR FROM ZEMP_MASTER_TABLE WHERE ROLE = 'TRANSPORT_ADMIN' LIMIT 1"
                ).fetchone()
                pending_with = admin["PERNR"] if admin else None
            elif action in ("REJECT", "WITHDRAW"):
                pending_with = req["PERNR"]
            elif action == "ALLOT":
                vehicle_no = body.get("vehicle_no")
                driver_id  = body.get("driver_id")
                if not vehicle_no or not driver_id:
                    return Response(
                        {"detail": "vehicle_no and driver_id are required for ALLOT action."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                if not db.execute(
                    "SELECT 1 FROM ZHRT_VEHICLE_MST WHERE VEHICLE_NO = %s AND ACTIVE_FLAG = 'Y'",
                    (vehicle_no,)
                ).fetchone():
                    return Response(
                        {"detail": "Vehicle not found or inactive."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                if not db.execute(
                    "SELECT 1 FROM ZHRT_DRIVER_MST WHERE DRIVER_ID = %s", (driver_id,)
                ).fetchone():
                    return Response(
                        {"detail": "Driver not found."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                pending_with = None
            else:
                pending_with = None

            # Persist changes
            vehicle_no = body.get("vehicle_no") if action == "ALLOT" else req["ALLOTTED_VEHICLE_NO"]
            driver_id  = body.get("driver_id")  if action == "ALLOT" else req["ALLOTTED_DRIVER_ID"]
            action_by  = body.get("action_by", "SYSTEM")
            remarks    = body.get("remarks")

            db.execute(
                """UPDATE ZHRT_BUS_REQ_MAIN
                   SET STATUS = %s, PENDING_WITH = %s, CHANGED_ON = %s, CHANGED_BY = %s,
                       ALLOTTED_VEHICLE_NO = %s, ALLOTTED_DRIVER_ID = %s, REMARKS = %s
                   WHERE REQID = %s""",
                (new_status, pending_with, now, action_by,
                 vehicle_no, driver_id, remarks, reqid)
            )

            seqnr = db.execute(
                "SELECT COUNT(*) FROM ZHRT_BUS_REQ_LOGS WHERE REQID = %s", (reqid,)
            ).fetchone()[0] + 1

            _log(db, reqid, seqnr, action_by, curr, new_status, pending_with,
                 action, req["APPLICATION_TYPE"], req["ROUTE_NO"], req["PICK_UP_POINT"],
                 req["NEAREST_STATION"], req["DIST_PICKUP_RESIDENCE"],
                 req["DIST_RESIDENCE_STATION"], remarks)
            db.commit()

            return Response({
                "reqid":       reqid,
                "status":      new_status,
                "status_text": STATUS[new_status],
                "message":     f"Action '{action}' completed successfully."
            })
        except Exception as e:
            db.rollback()
            logger.exception("Request action error for %s: %s", reqid, e)
            return Response({"detail": "An internal error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            db.close()


class RequestLogsView(APIView):
    """GET /api/requests/<reqid>/logs/  –  Get request audit logs."""

    def get(self, request, reqid):
        db = get_connection()
        try:
            rows = db.execute(
                "SELECT * FROM ZHRT_BUS_REQ_LOGS WHERE REQID = %s ORDER BY SEQNR",
                (reqid,)
            ).fetchall()
            result = []
            for r in rows:
                d = dict(r)
                d["CURR_STATUS_TEXT"] = STATUS.get(d.get("CURR_REQUEST_STATUS", ""), d.get("CURR_REQUEST_STATUS", ""))
                d["NEW_STATUS_TEXT"]  = STATUS.get(d.get("NEW_REQUEST_STATUS", ""),  d.get("NEW_REQUEST_STATUS", ""))
                result.append(d)
            return Response(result)
        finally:
            db.close()
