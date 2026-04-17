"""
schemas.py  –  Pydantic request / response models
"""
from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import date


# ─── Auth ────────────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    pernr: str
    password: str


class RegisterRequest(BaseModel):
    ename: str
    designation: Optional[str] = None
    department: Optional[str] = None
    address: Optional[str] = None
    email: Optional[str] = None
    mobile_no: Optional[str] = None
    profile_photo: Optional[str] = None
    password: str


class AdminAddEmployee(BaseModel):
    ename: str
    designation: Optional[str] = None
    department: Optional[str] = None
    address: Optional[str] = None
    email: Optional[str] = None
    mobile_no: Optional[str] = None
    role: str = "EMPLOYEE"          # EMPLOYEE | APPROVER | TRANSPORT_ADMIN
    password: str


class UserOut(BaseModel):
    pernr: str
    ename: str
    role: str
    designation: Optional[str] = None
    department: Optional[str] = None
    address: Optional[str] = None
    email: Optional[str] = None
    mobile_no: Optional[str] = None
    profile_photo: Optional[str] = None


class LoginOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    pernr: str
    ename: str
    role: str
    designation: Optional[str] = None
    department: Optional[str] = None
    address: Optional[str] = None
    email: Optional[str] = None
    mobile_no: Optional[str] = None
    profile_photo: Optional[str] = None


class EmployeeProfileUpdate(BaseModel):
    ename: Optional[str] = None
    designation: Optional[str] = None
    department: Optional[str] = None
    address: Optional[str] = None
    email: Optional[str] = None
    mobile_no: Optional[str] = None
    profile_photo: Optional[str] = None
    current_password: Optional[str] = None   # required only when changing password
    new_password: Optional[str] = None


# ─── Employee ────────────────────────────────────────────────────────────────
class EmployeeOut(BaseModel):
    PERNR: str
    ENAME: str
    DESIGNATION: Optional[str]
    DEPARTMENT: Optional[str]
    STRAS: Optional[str]
    ROLE: str


# ─── Driver ──────────────────────────────────────────────────────────────────
class DriverCreate(BaseModel):
    driver_id: Optional[str] = None   # auto-generated if not provided
    driver_name: str
    mobile_no1: str
    mobile_no2: Optional[str] = None
    address: Optional[str] = None
    dob: Optional[str] = None
    dl_no: Optional[str] = None
    valid_upto: Optional[str] = None
    begda: str
    endda: str = "9999-12-31"

    @field_validator("mobile_no1")
    @classmethod
    def validate_mobile(cls, v):
        if not v.isdigit() or len(v) < 10:
            raise ValueError("Mobile number must be at least 10 digits")
        return v


class DriverUpdate(BaseModel):
    driver_name: Optional[str] = None
    mobile_no2: Optional[str] = None
    address: Optional[str] = None
    dl_no: Optional[str] = None
    valid_upto: Optional[str] = None
    endda: Optional[str] = None


# ─── Vehicle ─────────────────────────────────────────────────────────────────
class VehicleCreate(BaseModel):
    vehicle_no: str
    vehicle_type: str
    vehicle_category: Optional[str] = None
    make: str
    model: str
    seating_capacity: int = 40
    chassis_no: Optional[str] = None
    engine_no: Optional[str] = None
    year_regn: Optional[str] = None
    date_purchase: Optional[str] = None
    po_number: Optional[str] = None
    cost_purchase: Optional[float] = None
    agency_name: Optional[str] = None
    insurance: Optional[str] = None
    fitness: Optional[str] = None
    permit: Optional[str] = None
    tax: Optional[str] = None
    tax_valid_upto: Optional[str] = None
    ins_valid_upto: Optional[str] = None
    fitness_valid_upto: Optional[str] = None
    permit_valid_upto: Optional[str] = None
    vehicle_from_date: str
    vehicle_to_date: str = "9999-12-31"


class VehicleUpdate(BaseModel):
    vehicle_type: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    seating_capacity: Optional[int] = None
    tax_valid_upto: Optional[str] = None
    ins_valid_upto: Optional[str] = None
    fitness_valid_upto: Optional[str] = None
    permit_valid_upto: Optional[str] = None
    active_flag: Optional[str] = None
    vehicle_to_date: Optional[str] = None


# ─── Admin Direct Allotment ──────────────────────────────────────────────────
class AdminAllotRequest(BaseModel):
    pernr: str
    vehicle_no: str
    driver_id: str
    remarks: Optional[str] = None


# ─── Driver-Vehicle Mapping ───────────────────────────────────────────────────
class MappingCreate(BaseModel):
    vehicle_type: str
    vehicle_no: str
    driver_id: str
    begda: str
    endda: str = "9999-12-31"


# ─── Route ───────────────────────────────────────────────────────────────────
class RouteOut(BaseModel):
    SEQNR: str
    ROUTE_FROM: str


class PickupOut(BaseModel):
    SUB_SEQNR: str
    PICK_UP_POINT: str


# ─── Bus Request ─────────────────────────────────────────────────────────────
class BusRequestCreate(BaseModel):
    pernr: str
    pass_type: str
    application_type: str
    reason: str
    route_no: str
    pick_up_point: str
    nearest_station: str
    dist_pickup_residence: float
    dist_residence_station: float
    effective_date: str
    attachment: Optional[str] = None
    on_behalf_of: Optional[str] = None   # PERNR of actual employee if raised by someone else

    @field_validator("dist_pickup_residence", "dist_residence_station")
    @classmethod
    def positive_dist(cls, v):
        if v < 0:
            raise ValueError("Distance cannot be negative")
        return v


class BusRequestAction(BaseModel):
    action: str           # SUBMIT | APPROVE | REJECT | ALLOT | WITHDRAW
    action_by: str        # PERNR of person taking action
    remarks: Optional[str] = None
    vehicle_no: Optional[str] = None   # required for ALLOT
    driver_id: Optional[str] = None    # required for ALLOT


# ─── Dashboard ────────────────────────────────────────────────────────────────
class DashboardOut(BaseModel):
    total_requests: int
    draft: int
    submitted: int
    approved: int
    rejected: int
    allotted: int
    active_vehicles: int
    active_drivers: int
    active_mappings: int
