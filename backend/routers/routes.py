"""
routers/routes.py  –  ZHRT_ROUTE_MAP read endpoints
"""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from db.database import get_db

from core.security import get_current_user

router = APIRouter(
    prefix="/routes",
    tags=["Bus Routes"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/")
def list_routes(db: Any = Depends(get_db)):
    """Return distinct routes (SEQNR + ROUTE_FROM)."""
    rows = db.execute(
        """SELECT SEQNR, ROUTE_FROM
           FROM ZHRT_ROUTE_MAP
           WHERE ENDDA >= CURRENT_DATE
           GROUP BY SEQNR, ROUTE_FROM
           ORDER BY SEQNR"""
    ).fetchall()
    return [dict(r) for r in rows]


@router.get("/{seqnr}/pickups")
def list_pickups(seqnr: str, db: Any = Depends(get_db)):
    """Return all pick-up points for a given route."""
    rows = db.execute(
        """SELECT SUB_SEQNR, PICK_UP_POINT
           FROM ZHRT_ROUTE_MAP
           WHERE SEQNR = %s AND ENDDA >= CURRENT_DATE
           ORDER BY SUB_SEQNR""",
        (seqnr,)
    ).fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail="Route not found")
    return [dict(r) for r in rows]
