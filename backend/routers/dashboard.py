"""
routers/dashboard.py  –  Summary statistics
"""
import sqlite3
from fastapi import APIRouter, Depends
from db.database import get_connection
from core.security import get_current_user

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/")
def get_dashboard():
    db = get_connection()
    try:
        def count(sql, params=()):
            return db.execute(sql, params).fetchone()[0]

        return {
            "total_requests":   count("SELECT COUNT(*) FROM ZHRT_BUS_REQ_MAIN"),
            "draft":            count("SELECT COUNT(*) FROM ZHRT_BUS_REQ_MAIN WHERE STATUS='0001'"),
            "submitted":        count("SELECT COUNT(*) FROM ZHRT_BUS_REQ_MAIN WHERE STATUS='0002'"),
            "approved":         count("SELECT COUNT(*) FROM ZHRT_BUS_REQ_MAIN WHERE STATUS='0003'"),
            "rejected":         count("SELECT COUNT(*) FROM ZHRT_BUS_REQ_MAIN WHERE STATUS='0004'"),
            "allotted":         count("SELECT COUNT(*) FROM ZHRT_BUS_REQ_MAIN WHERE STATUS='0005'"),
            "active_vehicles":  count("SELECT COUNT(*) FROM ZHRT_VEHICLE_MST WHERE ACTIVE_FLAG='Y'"),
            "active_drivers":   count("SELECT COUNT(*) FROM ZHRT_DRIVER_MST"),
            "active_mappings":  count("SELECT COUNT(*) FROM ZHRT_DRI_VEH_MAP WHERE ENDDA >= date('now')"),
        }
    finally:
        db.close()


@router.get("/my/{pernr}")
def my_dashboard(pernr: str):
    db = get_connection()
    try:
        def count(sql, params=()):
            return db.execute(sql, params).fetchone()[0]

        return {
            "my_total":    count("SELECT COUNT(*) FROM ZHRT_BUS_REQ_MAIN WHERE PERNR=?", (pernr,)),
            "my_draft":    count("SELECT COUNT(*) FROM ZHRT_BUS_REQ_MAIN WHERE PERNR=? AND STATUS='0001'", (pernr,)),
            "my_pending":  count("SELECT COUNT(*) FROM ZHRT_BUS_REQ_MAIN WHERE PERNR=? AND STATUS='0002'", (pernr,)),
            "my_approved": count("SELECT COUNT(*) FROM ZHRT_BUS_REQ_MAIN WHERE PERNR=? AND STATUS IN ('0003','0005')", (pernr,)),
            "my_rejected": count("SELECT COUNT(*) FROM ZHRT_BUS_REQ_MAIN WHERE PERNR=? AND STATUS='0004'", (pernr,)),
        }
    finally:
        db.close()
