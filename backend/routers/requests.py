"""
routers/requests.py  –  ZHRT_BUS_REQ_MAIN full workflow
"""
import sqlite3
from datetime import datetime, date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from db.database import get_db
from schemas.schemas import BusRequestCreate, BusRequestAction, AdminAllotRequest
import uuid

from core.security import get_current_user

router = APIRouter(
    prefix="/requests",
    tags=["Bus Requests"],
    dependencies=[Depends(get_current_user)],
)

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
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (log_id, reqid, seqnr, action_by, datetime.now().isoformat(),
         curr, new, pending, req_type, app_type, route, pickup,
         station, d1, d2, remarks or "")
    )


# ─────────────────────────────────────────────────────────────────────────────
# CREATE
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/", status_code=201)
def create_request(body: BusRequestCreate, db: sqlite3.Connection = Depends(get_db)):
    # Employee must exist
    emp = db.execute(
        "SELECT * FROM ZEMP_MASTER_TABLE WHERE PERNR = ?", (body.pernr,)
    ).fetchone()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Route must exist
    route_row = db.execute(
        "SELECT 1 FROM ZHRT_ROUTE_MAP WHERE SEQNR = ? AND PICK_UP_POINT = ?",
        (body.route_no, body.pick_up_point)
    ).fetchone()
    if not route_row:
        raise HTTPException(status_code=400, detail="Selected route / pick-up point is invalid.")

    # Determine who created it (on-behalf scenario)
    created_by = body.on_behalf_of if body.on_behalf_of else body.pernr
    now   = datetime.now().isoformat()
    today = date.today().isoformat()

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
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (reqid, body.pernr, body.pass_type, body.application_type, body.reason,
         body.route_no, body.pick_up_point, body.nearest_station,
         body.dist_pickup_residence, body.dist_residence_station,
         body.effective_date, body.attachment,
         "0001", pending_with, created_by, now, now, created_by)
    )

    _log(db, reqid, 1, created_by, "0000", "0001", pending_with,
         "CREATE", body.application_type, body.route_no, body.pick_up_point,
         body.nearest_station, body.dist_pickup_residence, body.dist_residence_station,
         "Request created as draft")
    db.commit()

    return {
        "reqid": reqid,
        "status": "0001",
        "status_text": "Draft",
        "message": "Request saved as Draft."
    }


# ─────────────────────────────────────────────────────────────────────────────
# LIST
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/")
def list_requests(
    pernr: Optional[str]  = Query(None),
    role:  Optional[str]  = Query(None),
    status_filter: Optional[str] = Query(None),
    skip:  int = Query(0,   ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: sqlite3.Connection = Depends(get_db),
):
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
        where, params = "WHERE (r.PERNR = ? OR r.REQUEST_CREATED_BY = ?)", [pernr, pernr]

    if status_filter:
        connector = "AND" if where else "WHERE"
        where  += f" {connector} r.STATUS = ?"
        params.append(status_filter)

    sql  = base + where + " ORDER BY r.REQUEST_CREATION_DATE DESC LIMIT ? OFFSET ?"
    rows = db.execute(sql, params + [limit, skip]).fetchall()

    result = []
    for r in rows:
        d = dict(r)
        d["STATUS_TEXT"] = STATUS.get(d["STATUS"], d["STATUS"])
        result.append(d)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# UPDATE DRAFT
# ─────────────────────────────────────────────────────────────────────────────
@router.put("/{reqid}")
def update_draft(reqid: str, body: BusRequestCreate, db: sqlite3.Connection = Depends(get_db)):
    req = db.execute(
        "SELECT STATUS FROM ZHRT_BUS_REQ_MAIN WHERE REQID = ?", (reqid,)
    ).fetchone()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found.")
    if req["STATUS"] != "0001":
        raise HTTPException(status_code=400, detail="Only Draft requests can be edited.")

    # Validate route/pickup still exist
    if not db.execute(
        "SELECT 1 FROM ZHRT_ROUTE_MAP WHERE SEQNR = ? AND PICK_UP_POINT = ?",
        (body.route_no, body.pick_up_point)
    ).fetchone():
        raise HTTPException(status_code=400, detail="Selected route / pick-up point is invalid.")

    now = datetime.now().isoformat()
    db.execute(
        """UPDATE ZHRT_BUS_REQ_MAIN SET
               PASS_TYPE=?, APPLICATION_TYPE=?, REASON=?,
               ROUTE_NO=?, PICK_UP_POINT=?, NEAREST_STATION=?,
               DIST_PICKUP_RESIDENCE=?, DIST_RESIDENCE_STATION=?,
               EFFECTIVE_DATE=?, ATTACHMENT=?, CHANGED_ON=?, CHANGED_BY=?
           WHERE REQID=?""",
        (body.pass_type, body.application_type, body.reason,
         body.route_no, body.pick_up_point, body.nearest_station,
         body.dist_pickup_residence, body.dist_residence_station,
         body.effective_date, body.attachment, now, body.pernr, reqid)
    )
    db.commit()
    return {"message": "Draft updated successfully.", "reqid": reqid}


# ─────────────────────────────────────────────────────────────────────────────
# GET SINGLE
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/{reqid}")
def get_request(reqid: str, db: sqlite3.Connection = Depends(get_db)):
    row = db.execute(
        "SELECT * FROM ZHRT_BUS_REQ_MAIN WHERE REQID = ?", (reqid,)
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Request not found")

    d = dict(row)
    d["STATUS_TEXT"] = STATUS.get(d["STATUS"], d["STATUS"])

    emp = db.execute(
        "SELECT PERNR, ENAME, DESIGNATION, DEPARTMENT, STRAS "
        "FROM ZEMP_MASTER_TABLE WHERE PERNR = ?", (d["PERNR"],)
    ).fetchone()
    d["EMPLOYEE"] = dict(emp) if emp else {}

    # Resolve route description
    route_row = db.execute(
        "SELECT DISTINCT ROUTE_FROM FROM ZHRT_ROUTE_MAP WHERE SEQNR = ?", (d["ROUTE_NO"],)
    ).fetchone()
    d["ROUTE_FROM"] = route_row["ROUTE_FROM"] if route_row else None

    # Resolve PENDING_WITH PERNR → name
    if d.get("PENDING_WITH"):
        pw = db.execute(
            "SELECT ENAME FROM ZEMP_MASTER_TABLE WHERE PERNR = ?", (d["PENDING_WITH"],)
        ).fetchone()
        d["PENDING_WITH_NAME"] = pw["ENAME"] if pw else d["PENDING_WITH"]

    # Vehicle & Driver info if allotted
    if d.get("ALLOTTED_VEHICLE_NO"):
        veh = db.execute(
            "SELECT VEHICLE_NO, VEHICLE_TYPE, MAKE, MODEL FROM ZHRT_VEHICLE_MST WHERE VEHICLE_NO = ?",
            (d["ALLOTTED_VEHICLE_NO"],)
        ).fetchone()
        d["VEHICLE_INFO"] = dict(veh) if veh else {}

    if d.get("ALLOTTED_DRIVER_ID"):
        drv = db.execute(
            "SELECT DRIVER_ID, DRIVER_NAME, MOBILE_NO1 FROM ZHRT_DRIVER_MST WHERE DRIVER_ID = ?",
            (d["ALLOTTED_DRIVER_ID"],)
        ).fetchone()
        d["DRIVER_INFO"] = dict(drv) if drv else {}

    logs = db.execute(
        """SELECT l.*, COALESCE(e.ENAME, l.ACTION_BY) AS ACTION_BY_NAME
           FROM ZHRT_BUS_REQ_LOGS l
           LEFT JOIN ZEMP_MASTER_TABLE e ON l.ACTION_BY = e.PERNR
           WHERE l.REQID = ? ORDER BY l.SEQNR""",
        (reqid,)
    ).fetchall()
    d["LOGS"] = [dict(l) for l in logs]

    return d


# ─────────────────────────────────────────────────────────────────────────────
# ACTION (Submit / Approve / Reject / Allot / Withdraw)
# ─────────────────────────────────────────────────────────────────────────────
@router.put("/{reqid}/action")
def take_action(
    reqid: str,
    body: BusRequestAction,
    db: sqlite3.Connection = Depends(get_db)
):
    req = db.execute(
        "SELECT * FROM ZHRT_BUS_REQ_MAIN WHERE REQID = ?", (reqid,)
    ).fetchone()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    action = body.action.upper()
    if action not in VALID_TRANSITIONS:
        raise HTTPException(status_code=400, detail=f"Unknown action '{action}'")

    expected_curr, new_status = VALID_TRANSITIONS[action]
    allowed = (expected_curr,) if isinstance(expected_curr, str) else expected_curr
    if req["STATUS"] not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot perform '{action}' on a request with status '{STATUS.get(req['STATUS'])}'."
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
        if not body.vehicle_no or not body.driver_id:
            raise HTTPException(
                status_code=400, detail="vehicle_no and driver_id are required for ALLOT action."
            )
        # Validate vehicle & driver exist
        if not db.execute(
            "SELECT 1 FROM ZHRT_VEHICLE_MST WHERE VEHICLE_NO = ? AND ACTIVE_FLAG = 'Y'",
            (body.vehicle_no,)
        ).fetchone():
            raise HTTPException(status_code=400, detail="Vehicle not found or inactive.")
        if not db.execute(
            "SELECT 1 FROM ZHRT_DRIVER_MST WHERE DRIVER_ID = ?", (body.driver_id,)
        ).fetchone():
            raise HTTPException(status_code=400, detail="Driver not found.")
        pending_with = None
    else:
        pending_with = None

    # Persist changes
    vehicle_no = body.vehicle_no if action == "ALLOT" else req["ALLOTTED_VEHICLE_NO"]
    driver_id  = body.driver_id  if action == "ALLOT" else req["ALLOTTED_DRIVER_ID"]

    db.execute(
        """UPDATE ZHRT_BUS_REQ_MAIN
           SET STATUS = ?, PENDING_WITH = ?, CHANGED_ON = ?, CHANGED_BY = ?,
               ALLOTTED_VEHICLE_NO = ?, ALLOTTED_DRIVER_ID = ?, REMARKS = ?
           WHERE REQID = ?""",
        (new_status, pending_with, now, body.action_by,
         vehicle_no, driver_id, body.remarks, reqid)
    )

    seqnr = db.execute(
        "SELECT COUNT(*) FROM ZHRT_BUS_REQ_LOGS WHERE REQID = ?", (reqid,)
    ).fetchone()[0] + 1

    _log(db, reqid, seqnr, body.action_by, curr, new_status, pending_with,
         action, req["APPLICATION_TYPE"], req["ROUTE_NO"], req["PICK_UP_POINT"],
         req["NEAREST_STATION"], req["DIST_PICKUP_RESIDENCE"],
         req["DIST_RESIDENCE_STATION"], body.remarks)
    db.commit()

    return {
        "reqid":       reqid,
        "status":      new_status,
        "status_text": STATUS[new_status],
        "message":     f"Action '{action}' completed successfully."
    }


# ─────────────────────────────────────────────────────────────────────────────
# ADMIN DIRECT ALLOTMENT (bypasses request workflow)
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/admin-allot", status_code=201)
def admin_direct_allot(
    body: AdminAllotRequest,
    allotted_by: str = "SYSTEM",
    db: sqlite3.Connection = Depends(get_db)
):
    emp = db.execute(
        "SELECT * FROM ZEMP_MASTER_TABLE WHERE PERNR = ?", (body.pernr,)
    ).fetchone()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found.")

    vehicle = db.execute(
        "SELECT * FROM ZHRT_VEHICLE_MST WHERE VEHICLE_NO = ? AND ACTIVE_FLAG = 'Y'",
        (body.vehicle_no,)
    ).fetchone()
    if not vehicle:
        raise HTTPException(status_code=400, detail="Vehicle not found or inactive.")

    driver = db.execute(
        "SELECT * FROM ZHRT_DRIVER_MST WHERE DRIVER_ID = ?", (body.driver_id,)
    ).fetchone()
    if not driver:
        raise HTTPException(status_code=400, detail="Driver not found.")

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
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (reqid, body.pernr, "STAFF", "DIRECT", "Admin Direct Allotment",
         "00", "Direct Assignment", "N/A", 0, 0,
         today, "0005", None,
         allotted_by, now, now, allotted_by,
         body.vehicle_no, body.driver_id, body.remarks or "Admin direct allotment")
    )

    _log(db, reqid, 1, allotted_by, None, "0005", None,
         "ALLOT", "DIRECT", "00", "Direct Assignment",
         "N/A", 0, 0, body.remarks or "Admin direct allotment")

    db.commit()
    return {
        "message": "Vehicle and driver allotted to employee successfully.",
        "reqid":   reqid,
        "pernr":   body.pernr,
        "vehicle_no": body.vehicle_no,
        "driver_id":  body.driver_id,
    }


# ─────────────────────────────────────────────────────────────────────────────
# GET LOGS
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/{reqid}/logs")
def get_logs(reqid: str, db: sqlite3.Connection = Depends(get_db)):
    rows = db.execute(
        "SELECT * FROM ZHRT_BUS_REQ_LOGS WHERE REQID = ? ORDER BY SEQNR",
        (reqid,)
    ).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        d["CURR_STATUS_TEXT"] = STATUS.get(d.get("CURR_REQUEST_STATUS",""), d.get("CURR_REQUEST_STATUS",""))
        d["NEW_STATUS_TEXT"]  = STATUS.get(d.get("NEW_REQUEST_STATUS",""),  d.get("NEW_REQUEST_STATUS",""))
        result.append(d)
    return result
