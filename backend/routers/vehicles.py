"""
routers/vehicles.py  –  ZHRT_VEHICLE_MST CRUD
"""
import sqlite3
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from db.database import get_db
from schemas.schemas import VehicleCreate, VehicleUpdate

from core.security import get_current_user

router = APIRouter(
    prefix="/vehicles",
    tags=["Vehicle Master"],
    dependencies=[Depends(get_current_user)],
)

VALID_TYPES = {"BUS", "SEDAN", "PREMIUM SEDAN", "SUV", "PREMIUM SUV"}


@router.get("/")
def list_vehicles(
    active_only: bool = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: sqlite3.Connection = Depends(get_db),
):
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
        LIMIT ? OFFSET ?
    """
    return [dict(r) for r in db.execute(sql, (limit, skip)).fetchall()]


@router.get("/{vehicle_no}")
def get_vehicle(vehicle_no: str, db: sqlite3.Connection = Depends(get_db)):
    row = db.execute(
        "SELECT * FROM ZHRT_VEHICLE_MST WHERE VEHICLE_NO = ?", (vehicle_no,)
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return dict(row)


@router.post("/", status_code=201)
def create_vehicle(
    body: VehicleCreate,
    created_by: str = "SYSTEM",
    db: sqlite3.Connection = Depends(get_db)
):
    if db.execute(
        "SELECT 1 FROM ZHRT_VEHICLE_MST WHERE VEHICLE_NO = ?", (body.vehicle_no,)
    ).fetchone():
        raise HTTPException(status_code=400, detail="Vehicle number already exists.")

    # Date validations
    today = date.today().isoformat()
    for field, label in [
        (body.tax_valid_upto, "Tax Valid Upto"),
        (body.ins_valid_upto, "Insurance Valid Upto"),
        (body.fitness_valid_upto, "Fitness Valid Upto"),
        (body.permit_valid_upto, "Permit Valid Upto"),
    ]:
        if field and field < today:
            raise HTTPException(status_code=400, detail=f"{label} must be today or a future date.")

    if body.vehicle_to_date < body.vehicle_from_date:
        raise HTTPException(status_code=400, detail="Vehicle To Date must be >= Vehicle From Date.")

    now = datetime.now().isoformat()
    db.execute(
        """INSERT INTO ZHRT_VEHICLE_MST
           (VEHICLE_NO, VEHICLE_TYPE, VEHICLE_CATEGORY, MAKE, MODEL, CHASSIS_NO, ENGINE_NO,
            YEAR_REGN, DATE_PURCHASE, PO_NUMBER, COST_PURCHASE, AGENCY_NAME,
            INSURANCE, FITNESS, PERMIT, TAX,
            TAX_VALID_UPTO, INS_VALID_UPTO, FITNESS_VALID_UPTO, PERMIT_VALID_UPTO,
            VEHICLE_FROM_DATE, VEHICLE_TO_DATE, ACTIVE_FLAG, SEATING_CAPACITY,
            ZERNAM, ZERDAT, ZERZET)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (body.vehicle_no, body.vehicle_type, body.vehicle_category, body.make, body.model,
         body.chassis_no, body.engine_no, body.year_regn, body.date_purchase,
         body.po_number, body.cost_purchase, body.agency_name,
         body.insurance, body.fitness, body.permit, body.tax,
         body.tax_valid_upto, body.ins_valid_upto, body.fitness_valid_upto, body.permit_valid_upto,
         body.vehicle_from_date, body.vehicle_to_date, "Y", body.seating_capacity,
         created_by, today, now)
    )
    db.commit()
    return {"message": "Vehicle created successfully", "vehicle_no": body.vehicle_no}


@router.put("/{vehicle_no}")
def update_vehicle(
    vehicle_no: str,
    body: VehicleUpdate,
    changed_by: str = "SYSTEM",
    db: sqlite3.Connection = Depends(get_db)
):
    row = db.execute(
        "SELECT 1 FROM ZHRT_VEHICLE_MST WHERE VEHICLE_NO = ?", (vehicle_no,)
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    set_clause = ", ".join(f"{k.upper()} = ?" for k in updates)
    values = list(updates.values()) + [datetime.now().isoformat(), changed_by, vehicle_no]
    db.execute(
        f"UPDATE ZHRT_VEHICLE_MST SET {set_clause}, ZAEDAT = ?, ZAENAM = ? WHERE VEHICLE_NO = ?",
        values
    )
    db.commit()
    return {"message": "Vehicle updated successfully"}


@router.delete("/{vehicle_no}")
def deactivate_vehicle(vehicle_no: str, changed_by: str = "SYSTEM", db: sqlite3.Connection = Depends(get_db)):
    """Soft-delete: set ACTIVE_FLAG = 'N'."""
    row = db.execute(
        "SELECT 1 FROM ZHRT_VEHICLE_MST WHERE VEHICLE_NO = ?", (vehicle_no,)
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    db.execute(
        "UPDATE ZHRT_VEHICLE_MST SET ACTIVE_FLAG = 'N', ZAENAM = ?, ZAEDAT = ? WHERE VEHICLE_NO = ?",
        (changed_by, datetime.now().isoformat(), vehicle_no)
    )
    db.commit()
    return {"message": "Vehicle deactivated"}
