"""
routers/auth.py  –  Login, Self-Register, Admin add employee
"""
import logging
import sqlite3
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Request, status
from db.database import get_db
from schemas.schemas import LoginRequest, LoginOut, RegisterRequest, AdminAddEmployee, UserOut
from core.security import hash_password, verify_password, create_access_token, get_current_user
from core.limiter import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

VALID_ROLES = {"EMPLOYEE", "APPROVER", "TRANSPORT_ADMIN"}


def _next_pernr(db: sqlite3.Connection) -> str:
    row = db.execute(
        "SELECT MAX(CAST(PERNR AS INTEGER)) FROM ZEMP_MASTER_TABLE"
    ).fetchone()
    next_num = (row[0] or 10000000) + 1
    return str(next_num)


def _build_login_response(row: sqlite3.Row, token: str) -> LoginOut:
    return LoginOut(
        access_token=token,
        token_type="bearer",
        pernr=row["PERNR"],
        ename=row["ENAME"],
        role=row["ROLE"],
        designation=row["DESIGNATION"],
        department=row["DEPARTMENT"],
        address=row["STRAS"],
        email=row["EMAIL"],
        mobile_no=row["MOBILE_NO"],
        profile_photo=row["PROFILE_PHOTO"],
    )


# ── Login (rate-limited: 5 attempts / minute per IP) ─────────────────────────
@router.post("/login", response_model=LoginOut)
@limiter.limit("5/minute")
def login(request: Request, payload: LoginRequest, db: sqlite3.Connection = Depends(get_db)):
    row = db.execute(
        "SELECT * FROM ZEMP_MASTER_TABLE WHERE PERNR = ?", (payload.pernr,)
    ).fetchone()

    if not row:
        logger.warning("Login failed – unknown PERNR: %s", payload.pernr)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Employee not found. Check your Employee Number."
        )

    if not verify_password(payload.password, row["PASSWORD"]):
        logger.warning("Login failed – wrong password for PERNR: %s", payload.pernr)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password."
        )

    logger.info("Login success – PERNR: %s role: %s", row["PERNR"], row["ROLE"])
    token = create_access_token({
        "sub":         row["PERNR"],
        "ename":       row["ENAME"],
        "role":        row["ROLE"],
        "designation": row["DESIGNATION"],
    })
    return _build_login_response(row, token)


# ── Self-Register ─────────────────────────────────────────────────────────────
@router.post("/register", status_code=201)
def register(payload: RegisterRequest, db: sqlite3.Connection = Depends(get_db)):
    today = date.today().isoformat()
    pernr = _next_pernr(db)

    db.execute(
        "INSERT INTO ZEMP_MASTER_TABLE "
        "(PERNR, ENAME, DESIGNATION, DEPARTMENT, STRAS, ROLE, PASSWORD, EMAIL, MOBILE_NO, PROFILE_PHOTO, ZERDAT) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (pernr, payload.ename, payload.designation, payload.department,
         payload.address, "EMPLOYEE", hash_password(payload.password),
         payload.email, payload.mobile_no, payload.profile_photo, today)
    )
    db.commit()

    logger.info("New employee registered – PERNR: %s name: %s", pernr, payload.ename)
    token = create_access_token({
        "sub":         pernr,
        "ename":       payload.ename,
        "role":        "EMPLOYEE",
        "designation": payload.designation,
    })
    return {
        "access_token":  token,
        "token_type":    "bearer",
        "pernr":         pernr,
        "ename":         payload.ename,
        "role":          "EMPLOYEE",
        "designation":   payload.designation,
        "department":    payload.department,
        "address":       payload.address,
        "email":         payload.email,
        "mobile_no":     payload.mobile_no,
        "profile_photo": payload.profile_photo,
    }


# ── Admin: manually add employee ─────────────────────────────────────────────
@router.post("/admin/add-employee", status_code=201)
def admin_add_employee(
    payload: AdminAddEmployee,
    db: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("role") != "TRANSPORT_ADMIN":
        raise HTTPException(status_code=403, detail="Only Transport Admin can add employees.")

    if payload.role not in VALID_ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role. Must be one of: {', '.join(VALID_ROLES)}"
        )

    today = date.today().isoformat()
    pernr = _next_pernr(db)

    db.execute(
        "INSERT INTO ZEMP_MASTER_TABLE "
        "(PERNR, ENAME, DESIGNATION, DEPARTMENT, STRAS, ROLE, PASSWORD, EMAIL, MOBILE_NO, ZERDAT) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (pernr, payload.ename, payload.designation, payload.department,
         payload.address, payload.role, hash_password(payload.password),
         payload.email, payload.mobile_no, today)
    )
    db.commit()
    logger.info("Admin %s added employee %s (role=%s)", current_user.get("sub"), pernr, payload.role)
    return {"message": "Employee added successfully", "pernr": pernr}


# ── Employee profile ──────────────────────────────────────────────────────────
@router.get("/employee/{pernr}", response_model=UserOut)
def get_employee_profile(
    pernr: str,
    db: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("role") == "EMPLOYEE" and current_user.get("sub") != pernr:
        raise HTTPException(status_code=403, detail="You can only view your own profile.")

    row = db.execute(
        "SELECT * FROM ZEMP_MASTER_TABLE WHERE PERNR = ?", (pernr,)
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Employee not found")
    return UserOut(
        pernr=row["PERNR"], ename=row["ENAME"], role=row["ROLE"],
        designation=row["DESIGNATION"], department=row["DEPARTMENT"], address=row["STRAS"],
        email=row["EMAIL"], mobile_no=row["MOBILE_NO"], profile_photo=row["PROFILE_PHOTO"],
    )
