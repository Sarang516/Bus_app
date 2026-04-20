"""
database.py  –  SQLite connection + table creation + seed data
"""
import sqlite3
from datetime import date, datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "bus_app.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_db():
    """FastAPI dependency – yields a connection and closes it after the request."""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# DDL
# ─────────────────────────────────────────────────────────────────────────────
DDL = """
-- ── Employee Master ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ZEMP_MASTER_TABLE (
    PERNR       TEXT PRIMARY KEY,
    ENAME       TEXT NOT NULL,
    DESIGNATION TEXT,
    DEPARTMENT  TEXT,
    WERKS       TEXT,
    PERSG       TEXT,
    PERSK       TEXT,
    ORGEH       TEXT,
    STRAS       TEXT,
    ROLE        TEXT NOT NULL DEFAULT 'EMPLOYEE',  -- EMPLOYEE | APPROVER | TRANSPORT_ADMIN
    PASSWORD    TEXT NOT NULL DEFAULT 'pass123',
    EMAIL       TEXT,
    MOBILE_NO   TEXT,
    PROFILE_PHOTO TEXT,
    ZERNAM      TEXT,
    ZERDAT      TEXT,
    ZAENAM      TEXT,
    ZAEDAT      TEXT
);

-- ── Driver Master (ZHRT_DRIVER_MST) ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ZHRT_DRIVER_MST (
    DRIVER_ID   TEXT PRIMARY KEY,
    DRIVER_NAME TEXT NOT NULL,
    MOBILE_NO1  TEXT NOT NULL UNIQUE,
    MOBILE_NO2  TEXT,
    ADDRESS     TEXT,
    DOB         TEXT,
    DL_NO       TEXT,
    VALID_UPTO  TEXT,
    BEGDA       TEXT NOT NULL,
    ENDDA       TEXT NOT NULL DEFAULT '9999-12-31',
    ZERNAM      TEXT,
    ZERDAT      TEXT,
    ZERZET      TEXT,
    ZAENAM      TEXT,
    ZAEDAT      TEXT,
    ZTIME       TEXT
);

-- ── Vehicle Master (ZHRT_VEHICLE_MST) ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ZHRT_VEHICLE_MST (
    VEHICLE_NO          TEXT PRIMARY KEY,
    VEHICLE_TYPE        TEXT,
    VEHICLE_CATEGORY    TEXT,
    MAKE                TEXT,
    MODEL               TEXT,
    CHASSIS_NO          TEXT,
    ENGINE_NO           TEXT,
    YEAR_REGN           TEXT,
    DATE_PURCHASE       TEXT,
    PO_NUMBER           TEXT,
    COST_PURCHASE       REAL,
    AGENCY_NAME         TEXT,
    TAX                 TEXT,
    INSURANCE           TEXT,
    FITNESS             TEXT,
    PERMIT              TEXT,
    TAX_VALID_UPTO      TEXT,
    INS_VALID_UPTO      TEXT,
    FITNESS_VALID_UPTO  TEXT,
    PERMIT_VALID_UPTO   TEXT,
    SEATING_CAPACITY    INTEGER NOT NULL DEFAULT 40,
    VEHICLE_FROM_DATE   TEXT NOT NULL,
    VEHICLE_TO_DATE     TEXT NOT NULL DEFAULT '9999-12-31',
    ACTIVE_FLAG         TEXT NOT NULL DEFAULT 'Y',
    ZERNAM              TEXT,
    ZERDAT              TEXT,
    ZERZET              TEXT,
    ZAENAM              TEXT,
    ZAEDAT              TEXT,
    ZTIME               TEXT
);

-- ── Driver-Vehicle Mapping (ZHRT_DRI_VEH_MAP) ────────────────────────────────
CREATE TABLE IF NOT EXISTS ZHRT_DRI_VEH_MAP (
    MAP_ID      TEXT PRIMARY KEY,
    VEHICLE_TYPE TEXT NOT NULL,
    VEHICLE_NO  TEXT NOT NULL,
    DRIVER_ID   TEXT NOT NULL,
    DRIVER_NAME TEXT,
    MOBILE_NO1  TEXT,
    BEGDA       TEXT NOT NULL,
    ENDDA       TEXT NOT NULL DEFAULT '9999-12-31',
    DATE_MAP    TEXT,
    ZERNAM      TEXT,
    ZERDAT      TEXT,
    ZERZET      TEXT,
    ZAENAM      TEXT,
    ZAEDAT      TEXT,
    ZTIME       TEXT,
    UNIQUE (VEHICLE_NO, DRIVER_ID, BEGDA)
);

-- ── Bus Route Map (ZHRT_ROUTE_MAP) ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ZHRT_ROUTE_MAP (
    SEQNR       TEXT NOT NULL,
    SUB_SEQNR   TEXT NOT NULL,
    ROUTE_FROM  TEXT NOT NULL,
    PICK_UP_POINT TEXT NOT NULL,
    BEGDA       TEXT NOT NULL DEFAULT '2024-01-01',
    ENDDA       TEXT NOT NULL DEFAULT '9999-12-31',
    ZERNAM      TEXT,
    ZERDAT      TEXT,
    PRIMARY KEY (SEQNR, SUB_SEQNR)
);

-- ── Bus Request Main (ZHRT_BUS_REQ_MAIN) ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS ZHRT_BUS_REQ_MAIN (
    REQID                       TEXT PRIMARY KEY,
    PERNR                       TEXT NOT NULL,
    PASS_TYPE                   TEXT NOT NULL,
    APPLICATION_TYPE            TEXT NOT NULL,
    REASON                      TEXT NOT NULL,
    ROUTE_NO                    TEXT NOT NULL,
    PICK_UP_POINT               TEXT NOT NULL,
    NEAREST_STATION             TEXT NOT NULL,
    DIST_PICKUP_RESIDENCE       REAL NOT NULL DEFAULT 0,
    DIST_RESIDENCE_STATION      REAL NOT NULL DEFAULT 0,
    EFFECTIVE_DATE              TEXT NOT NULL,
    ATTACHMENT                  TEXT,
    STATUS                      TEXT NOT NULL DEFAULT '0001',
    PENDING_WITH                TEXT,
    REQUEST_CREATED_BY          TEXT NOT NULL,
    REQUEST_CREATION_DATE       TEXT NOT NULL,
    CHANGED_ON                  TEXT,
    CHANGED_BY                  TEXT,
    ALLOTTED_VEHICLE_NO         TEXT,
    ALLOTTED_DRIVER_ID          TEXT,
    REMARKS                     TEXT
);

-- ── Bus Request Log (ZHRT_BUS_REQ_LOGS) ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS ZHRT_BUS_REQ_LOGS (
    LOG_ID                      TEXT PRIMARY KEY,
    REQID                       TEXT NOT NULL,
    SEQNR                       INTEGER NOT NULL,
    ACTION_BY                   TEXT NOT NULL,
    ACTION_ON                   TEXT NOT NULL,
    CURR_REQUEST_STATUS         TEXT,
    NEW_REQUEST_STATUS          TEXT NOT NULL,
    PENDING_WITH                TEXT,
    REQUEST_TYPE                TEXT,
    APPLICATION_TYPE            TEXT,
    ROUTE_NO                    TEXT,
    PICK_UP_POINT               TEXT,
    NEAREST_STATION             TEXT,
    DIST_PICKUP_RESIDENCE       REAL,
    DIST_RESIDENCE_STATION      REAL,
    REMARKS                     TEXT
);
"""


INDEXES = """
CREATE INDEX IF NOT EXISTS idx_req_pernr        ON ZHRT_BUS_REQ_MAIN (PERNR);
CREATE INDEX IF NOT EXISTS idx_req_status       ON ZHRT_BUS_REQ_MAIN (STATUS);
CREATE INDEX IF NOT EXISTS idx_req_created_by   ON ZHRT_BUS_REQ_MAIN (REQUEST_CREATED_BY);
CREATE INDEX IF NOT EXISTS idx_req_vehicle      ON ZHRT_BUS_REQ_MAIN (ALLOTTED_VEHICLE_NO);
CREATE INDEX IF NOT EXISTS idx_emp_role         ON ZEMP_MASTER_TABLE  (ROLE);
CREATE INDEX IF NOT EXISTS idx_emp_name         ON ZEMP_MASTER_TABLE  (ENAME);
CREATE INDEX IF NOT EXISTS idx_veh_active       ON ZHRT_VEHICLE_MST   (ACTIVE_FLAG);
CREATE INDEX IF NOT EXISTS idx_map_vehicle      ON ZHRT_DRI_VEH_MAP   (VEHICLE_NO);
CREATE INDEX IF NOT EXISTS idx_map_driver       ON ZHRT_DRI_VEH_MAP   (DRIVER_ID);
CREATE INDEX IF NOT EXISTS idx_logs_reqid       ON ZHRT_BUS_REQ_LOGS  (REQID);
"""


def init_db():
    """Create all tables, indexes and insert seed data if the DB is brand-new."""
    conn = get_connection()
    conn.executescript(DDL)
    conn.executescript(INDEXES)
    conn.commit()

    # Migrations for columns added after initial release
    for sql in [
        "ALTER TABLE ZHRT_VEHICLE_MST ADD COLUMN SEATING_CAPACITY INTEGER NOT NULL DEFAULT 40",
        "ALTER TABLE ZEMP_MASTER_TABLE ADD COLUMN EMAIL TEXT",
        "ALTER TABLE ZEMP_MASTER_TABLE ADD COLUMN MOBILE_NO TEXT",
        "ALTER TABLE ZEMP_MASTER_TABLE ADD COLUMN PROFILE_PHOTO TEXT",
    ]:
        try:
            conn.execute(sql)
            conn.commit()
        except Exception:
            pass  # Column already exists

    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM ZEMP_MASTER_TABLE")
    if cur.fetchone()[0] == 0:
        _seed(conn)

    conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Seed
# ─────────────────────────────────────────────────────────────────────────────
def _seed(conn: sqlite3.Connection):
    today = date.today().isoformat()
    now   = datetime.now().isoformat()

    # Import here to avoid circular imports at module load time
    from core.security import hash_password
    hashed = hash_password("pass123")

    # Employees (passwords stored as bcrypt hashes)
    conn.executemany(
        "INSERT INTO ZEMP_MASTER_TABLE "
        "(PERNR,ENAME,DESIGNATION,DEPARTMENT,WERKS,PERSG,PERSK,ORGEH,STRAS,ROLE,PASSWORD,ZERDAT) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        [
            ("10000001","Rahul Sharma","Senior Engineer","IT Department","1001","1","01","50000001","12 MG Road, Pune","EMPLOYEE",hashed,today),
            ("10000002","Priya Verma","HR Manager","HR Department","1001","2","02","50000002","45 FC Road, Pune","APPROVER",hashed,today),
            ("10000003","Amit Patel","Transport Admin","Administration","1001","3","03","50000003","7 SB Road, Pune","TRANSPORT_ADMIN",hashed,today),
            ("10000004","Sneha Joshi","Software Developer","IT Department","1001","1","01","50000001","22 Aundh Road, Pune","EMPLOYEE",hashed,today),
            ("10000005","Vikram Nair","Business Analyst","Finance Department","1001","1","02","50000004","88 Baner Road, Pune","EMPLOYEE",hashed,today),
        ]
    )

    # Drivers
    conn.executemany(
        "INSERT INTO ZHRT_DRIVER_MST "
        "(DRIVER_ID,DRIVER_NAME,MOBILE_NO1,MOBILE_NO2,ADDRESS,DOB,DL_NO,VALID_UPTO,BEGDA,ENDDA,ZERNAM,ZERDAT) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        [
            ("DRV001","Suresh Kumar","9876543210","9876543211","14 Kharadi, Pune","1985-06-15","MH12AB1234","2026-12-31","2024-01-01","9999-12-31","SYSTEM",today),
            ("DRV002","Ramesh Singh","9988776655","9988776656","3 Viman Nagar, Pune","1980-03-22","MH14CD5678","2025-09-30","2024-01-01","9999-12-31","SYSTEM",today),
            ("DRV003","Ganesh Yadav","9011223344",None,"55 Magarpatta, Pune","1990-11-08","MH15EF9012","2027-03-31","2024-01-01","9999-12-31","SYSTEM",today),
            ("DRV004","Manoj Tiwari","9922334455",None,"8 Wakad, Pune","1978-07-30","MH12GH3456","2026-06-30","2024-01-01","9999-12-31","SYSTEM",today),
        ]
    )

    # Vehicles
    conn.executemany(
        "INSERT INTO ZHRT_VEHICLE_MST "
        "(VEHICLE_NO,VEHICLE_TYPE,MAKE,MODEL,CHASSIS_NO,ENGINE_NO,YEAR_REGN,DATE_PURCHASE,"
        "COST_PURCHASE,AGENCY_NAME,INSURANCE,FITNESS,PERMIT,TAX,"
        "TAX_VALID_UPTO,INS_VALID_UPTO,FITNESS_VALID_UPTO,PERMIT_VALID_UPTO,"
        "VEHICLE_FROM_DATE,VEHICLE_TO_DATE,ACTIVE_FLAG,SEATING_CAPACITY,ZERDAT) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [
            ("MH12AB1001","BUS","TATA","Starbus Ultra 32","CHN001A","ENG001A","2022","2022-03-15",3500000.0,"Tata Motors Pune","INS-TT-001","FIT-001","PER-001","TAX-001","2026-03-14","2026-03-14","2026-03-14","2026-03-14","2022-04-01","9999-12-31","Y",32,today),
            ("MH12CD2002","BUS","ASHOK LEYLAND","Viking 40 Seater","CHN002B","ENG002B","2023","2023-01-10",4200000.0,"Leyland Dealers Pune","INS-AL-002","FIT-002","PER-002","TAX-002","2026-01-09","2026-01-09","2026-01-09","2026-01-09","2023-02-01","9999-12-31","Y",40,today),
            ("MH14EF3003","SEDAN","TOYOTA","Innova Crysta","CHN003C","ENG003C","2023","2023-05-20",1800000.0,"Toyota Dealer Pune","INS-TY-003","FIT-003","PER-003","TAX-003","2026-05-19","2026-05-19","2026-05-19","2026-05-19","2023-06-01","9999-12-31","Y",6,today),
            ("MH15GH4004","BUS","VOLVO","9400 AC Coach","CHN004D","ENG004D","2021","2021-08-12",8500000.0,"Volvo Bus India","INS-VL-004","FIT-004","PER-004","TAX-004","2025-08-11","2025-08-11","2025-08-11","2025-08-11","2021-09-01","9999-12-31","Y",45,today),
        ]
    )

    # Routes
    conn.executemany(
        "INSERT INTO ZHRT_ROUTE_MAP (SEQNR,SUB_SEQNR,ROUTE_FROM,PICK_UP_POINT,BEGDA,ENDDA) VALUES (?,?,?,?,?,?)",
        [
            ("01","001","Shivajinagar","Shivajinagar Bus Stand","2024-01-01","9999-12-31"),
            ("01","002","Shivajinagar","Deccan Gymkhana Corner","2024-01-01","9999-12-31"),
            ("01","003","Shivajinagar","FC Road Junction","2024-01-01","9999-12-31"),
            ("01","004","Shivajinagar","Law College Road","2024-01-01","9999-12-31"),
            ("02","001","Hinjewadi","Hinjewadi Phase 1 Gate","2024-01-01","9999-12-31"),
            ("02","002","Hinjewadi","Hinjewadi Phase 2 Chowk","2024-01-01","9999-12-31"),
            ("02","003","Hinjewadi","Wakad Bridge","2024-01-01","9999-12-31"),
            ("02","004","Hinjewadi","Balewadi High Street","2024-01-01","9999-12-31"),
            ("03","001","Kothrud","Kothrud Bus Depot","2024-01-01","9999-12-31"),
            ("03","002","Kothrud","Dahanukar Colony Stop","2024-01-01","9999-12-31"),
            ("03","003","Kothrud","Karve Road Crossing","2024-01-01","9999-12-31"),
            ("04","001","Hadapsar","Hadapsar Gadital","2024-01-01","9999-12-31"),
            ("04","002","Hadapsar","Magarpatta City Gate","2024-01-01","9999-12-31"),
            ("04","003","Hadapsar","Manjri Phata","2024-01-01","9999-12-31"),
        ]
    )

    conn.commit()
    print("[DB] Seed data inserted successfully.")
