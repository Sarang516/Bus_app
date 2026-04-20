"""
routers/mappings.py  –  ZHRT_DRI_VEH_MAP CRUD
"""
from datetime import date, datetime
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from db.database import get_db
from schemas.schemas import MappingCreate

from core.security import get_current_user

router = APIRouter(
    prefix="/mappings",
    tags=["Driver-Vehicle Mapping"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/")
def list_mappings(active_only: bool = False, db: Any = Depends(get_db)):
    if active_only:
        sql = "SELECT * FROM ZHRT_DRI_VEH_MAP WHERE ENDDA >= CURRENT_DATE ORDER BY DATE_MAP DESC"
    else:
        sql = "SELECT * FROM ZHRT_DRI_VEH_MAP ORDER BY DATE_MAP DESC"
    return [dict(r) for r in db.execute(sql).fetchall()]


@router.post("/", status_code=201)
def create_mapping(
    body: MappingCreate,
    created_by: str = "SYSTEM",
    db: Any = Depends(get_db)
):
    # Duplicate check
    if db.execute(
        """SELECT 1 FROM ZHRT_DRI_VEH_MAP
           WHERE VEHICLE_NO = %s AND DRIVER_ID = %s AND ENDDA >= CURRENT_DATE""",
        (body.vehicle_no, body.driver_id)
    ).fetchone():
        raise HTTPException(
            status_code=400,
            detail="An active mapping for this vehicle and driver already exists."
        )

    driver = db.execute(
        "SELECT * FROM ZHRT_DRIVER_MST WHERE DRIVER_ID = %s", (body.driver_id,)
    ).fetchone()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    vehicle = db.execute(
        "SELECT 1 FROM ZHRT_VEHICLE_MST WHERE VEHICLE_NO = %s AND ACTIVE_FLAG = 'Y'", (body.vehicle_no,)
    ).fetchone()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found or inactive")

    now   = datetime.now().isoformat()
    today = date.today().isoformat()
    map_id = f"MAP{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

    db.execute(
        """INSERT INTO ZHRT_DRI_VEH_MAP
           (MAP_ID, VEHICLE_TYPE, VEHICLE_NO, DRIVER_ID, DRIVER_NAME, MOBILE_NO1,
            BEGDA, ENDDA, DATE_MAP, ZERNAM, ZERDAT, ZERZET)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (map_id, body.vehicle_type, body.vehicle_no, body.driver_id,
         driver["DRIVER_NAME"], driver["MOBILE_NO1"],
         body.begda, body.endda, today, created_by, today, now)
    )
    db.commit()
    return {"message": "Mapping created", "map_id": map_id}


@router.delete("/{map_id}")
def end_mapping(map_id: str, ended_by: str = "SYSTEM", db: Any = Depends(get_db)):
    row = db.execute("SELECT 1 FROM ZHRT_DRI_VEH_MAP WHERE MAP_ID = %s", (map_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Mapping not found")
    db.execute(
        "UPDATE ZHRT_DRI_VEH_MAP SET ENDDA = CURRENT_DATE, ZAENAM = %s, ZAEDAT = %s WHERE MAP_ID = %s",
        (ended_by, datetime.now().isoformat(), map_id)
    )
    db.commit()
    return {"message": "Mapping ended"}
