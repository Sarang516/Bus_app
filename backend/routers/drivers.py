"""
routers/drivers.py  –  ZHRT_DRIVER_MST CRUD
"""
from datetime import date, datetime
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query
from db.database import get_db
from schemas.schemas import DriverCreate, DriverUpdate

from core.security import get_current_user

router = APIRouter(
    prefix="/drivers",
    tags=["Driver Master"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/")
def list_drivers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Any = Depends(get_db),
):
    rows = db.execute(
        "SELECT * FROM ZHRT_DRIVER_MST ORDER BY DRIVER_NAME LIMIT %s OFFSET %s",
        (limit, skip),
    ).fetchall()
    return [dict(r) for r in rows]


@router.get("/{driver_id}")
def get_driver(driver_id: str, db: Any = Depends(get_db)):
    row = db.execute(
        "SELECT * FROM ZHRT_DRIVER_MST WHERE DRIVER_ID = %s", (driver_id,)
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Driver not found")
    return dict(row)


def _next_driver_id(db: Any) -> str:
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


@router.post("/", status_code=201)
def create_driver(
    body: DriverCreate,
    created_by: str = "SYSTEM",
    db: Any = Depends(get_db)
):
    # Duplicate mobile check
    if db.execute(
        "SELECT 1 FROM ZHRT_DRIVER_MST WHERE MOBILE_NO1 = %s", (body.mobile_no1,)
    ).fetchone():
        raise HTTPException(
            status_code=400,
            detail=f"A driver with mobile number {body.mobile_no1} already exists."
        )

    # DOB cannot be future
    if body.dob and body.dob > date.today().isoformat():
        raise HTTPException(status_code=400, detail="Date of Birth cannot be a future date.")

    # Auto-generate Driver ID if not provided
    driver_id = body.driver_id.strip() if body.driver_id and body.driver_id.strip() else _next_driver_id(db)

    # Duplicate driver_id check
    if db.execute(
        "SELECT 1 FROM ZHRT_DRIVER_MST WHERE DRIVER_ID = %s", (driver_id,)
    ).fetchone():
        raise HTTPException(status_code=400, detail=f"Driver ID {driver_id} already exists.")

    now   = datetime.now().isoformat()
    today = date.today().isoformat()

    db.execute(
        """INSERT INTO ZHRT_DRIVER_MST
           (DRIVER_ID, DRIVER_NAME, MOBILE_NO1, MOBILE_NO2, ADDRESS, DOB, DL_NO, VALID_UPTO,
            BEGDA, ENDDA, ZERNAM, ZERDAT, ZERZET)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (driver_id, body.driver_name, body.mobile_no1, body.mobile_no2,
         body.address, body.dob, body.dl_no, body.valid_upto,
         body.begda, body.endda, created_by, today, now)
    )
    db.commit()
    return {"message": "Driver created successfully", "driver_id": driver_id}


@router.put("/{driver_id}")
def update_driver(
    driver_id: str,
    body: DriverUpdate,
    changed_by: str = "SYSTEM",
    db: Any = Depends(get_db)
):
    row = db.execute(
        "SELECT 1 FROM ZHRT_DRIVER_MST WHERE DRIVER_ID = %s", (driver_id,)
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Driver not found")

    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    set_clause = ", ".join(f"{k.upper()} = %s" for k in updates)
    values = list(updates.values()) + [datetime.now().isoformat(), changed_by, driver_id]
    db.execute(
        f"UPDATE ZHRT_DRIVER_MST SET {set_clause}, ZAEDAT = %s, ZAENAM = %s WHERE DRIVER_ID = %s",
        values
    )
    db.commit()
    return {"message": "Driver updated successfully"}


@router.delete("/{driver_id}")
def delete_driver(driver_id: str, db: Any = Depends(get_db)):
    # Check if driver is mapped to any active vehicle
    mapping = db.execute(
        "SELECT 1 FROM ZHRT_DRI_VEH_MAP WHERE DRIVER_ID = %s AND ENDDA >= CURRENT_DATE",
        (driver_id,)
    ).fetchone()
    if mapping:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete driver – active vehicle mapping exists. Remove mapping first."
        )
    db.execute("DELETE FROM ZHRT_DRIVER_MST WHERE DRIVER_ID = %s", (driver_id,))
    db.commit()
    return {"message": "Driver deleted"}
