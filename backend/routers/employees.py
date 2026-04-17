"""
routers/employees.py  –  ZEMP_MASTER_TABLE READ + profile update operations
"""
import sqlite3
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from db.database import get_db
from schemas.schemas import EmployeeProfileUpdate
from core.security import hash_password, verify_password

from core.security import get_current_user

router = APIRouter(
    prefix="/employees",
    tags=["Employee Master"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/")
def list_employees(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: sqlite3.Connection = Depends(get_db),
):
    """List employees with optional search and pagination."""
    if search:
        rows = db.execute(
            "SELECT * FROM ZEMP_MASTER_TABLE WHERE ENAME LIKE ? OR PERNR LIKE ? ORDER BY ENAME LIMIT ? OFFSET ?",
            (f"%{search}%", f"%{search}%", limit, skip),
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT * FROM ZEMP_MASTER_TABLE ORDER BY ENAME LIMIT ? OFFSET ?",
            (limit, skip),
        ).fetchall()
    return [dict(r) for r in rows]


@router.get("/with-allotment")
def list_employees_with_allotment(db: sqlite3.Connection = Depends(get_db)):
    """All employees with their latest allotted vehicle & driver (status 0005)."""
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
    return [dict(r) for r in rows]


@router.get("/{pernr}")
def get_employee(pernr: str, db: sqlite3.Connection = Depends(get_db)):
    """Get a single employee by PERNR."""
    row = db.execute(
        "SELECT * FROM ZEMP_MASTER_TABLE WHERE PERNR = ?", (pernr,)
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Employee not found")
    return dict(row)


@router.put("/{pernr}")
def update_employee_profile(
    pernr: str,
    body: EmployeeProfileUpdate,
    db: sqlite3.Connection = Depends(get_db)
):
    """Employee updates their own profile details and optionally changes password."""
    row = db.execute(
        "SELECT * FROM ZEMP_MASTER_TABLE WHERE PERNR = ?", (pernr,)
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Employee not found")

    updates = {}
    if body.ename:         updates["ENAME"]         = body.ename
    if body.designation  is not None: updates["DESIGNATION"]  = body.designation
    if body.department   is not None: updates["DEPARTMENT"]   = body.department
    if body.address      is not None: updates["STRAS"]        = body.address
    if body.email        is not None: updates["EMAIL"]        = body.email
    if body.mobile_no    is not None: updates["MOBILE_NO"]    = body.mobile_no
    if body.profile_photo is not None: updates["PROFILE_PHOTO"] = body.profile_photo

    # Password change — require current password verification
    if body.new_password:
        if not body.current_password:
            raise HTTPException(status_code=400, detail="Current password is required to set a new password.")
        if not verify_password(body.current_password, row["PASSWORD"]):
            raise HTTPException(status_code=400, detail="Current password is incorrect.")
        if len(body.new_password) < 6:
            raise HTTPException(status_code=400, detail="New password must be at least 6 characters.")
        updates["PASSWORD"] = hash_password(body.new_password)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update.")

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [datetime.now().isoformat(), pernr]
    db.execute(
        f"UPDATE ZEMP_MASTER_TABLE SET {set_clause}, ZAEDAT = ? WHERE PERNR = ?",
        values
    )
    db.commit()

    updated = db.execute(
        "SELECT * FROM ZEMP_MASTER_TABLE WHERE PERNR = ?", (pernr,)
    ).fetchone()
    return {
        "message": "Profile updated successfully",
        "pernr":         updated["PERNR"],
        "ename":         updated["ENAME"],
        "role":          updated["ROLE"],
        "designation":   updated["DESIGNATION"],
        "department":    updated["DEPARTMENT"],
        "address":       updated["STRAS"],
        "email":         updated["EMAIL"],
        "mobile_no":     updated["MOBILE_NO"],
        "profile_photo": updated["PROFILE_PHOTO"],
    }
