"""
main.py  –  FastAPI application entry point (Enterprise Edition)
Run:  python main.py
Docs: http://localhost:8080/docs
"""
import sys
import os
import uuid
import logging
import logging.handlers
from pathlib import Path

# ── Path setup ────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

# ── Load .env before anything else ────────────────────────────────────────────
from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env")

# ── Logging setup (file + console) ────────────────────────────────────────────
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
LOG_DIR   = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

def setup_logging():
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    root = logging.getLogger()
    root.setLevel(LOG_LEVEL)

    # Console
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    root.addHandler(ch)

    # Rotating file – 10 MB max, keep 5 backups
    fh = logging.handlers.RotatingFileHandler(
        LOG_DIR / "app.log", maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    fh.setFormatter(fmt)
    root.addHandler(fh)

setup_logging()
logger = logging.getLogger("main")

# ── JWT secret enforcement ────────────────────────────────────────────────────
_DEFAULT_SECRET = "bus-app-dev-secret-change-in-production"
_jwt_secret = os.environ.get("JWT_SECRET_KEY", _DEFAULT_SECRET)
# Only warn in the main process (not in uvicorn reloader child processes)
if _jwt_secret == _DEFAULT_SECRET and os.environ.get("_JWT_WARNED") != "1":
    os.environ["_JWT_WARNED"] = "1"
    logger.warning(
        "⚠️  JWT_SECRET_KEY is using the default dev value! "
        "Set JWT_SECRET_KEY in your .env file before deploying to production."
    )

# ── FastAPI + middleware ───────────────────────────────────────────────────────
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from core.limiter import limiter
from db.database import init_db, get_connection
from routers import auth, employees, drivers, vehicles, mappings, routes, requests, dashboard, uploads

app = FastAPI(
    title="Bus Transportation Booking System",
    description="Employee official commutation bus booking – REST API",
    version="2.0.0",
)

# Rate limiter state + error handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ──────────────────────────────────────────────────────────────────────
_raw_origins = os.environ.get(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:5173",
)
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# ── Global exception handler (never expose stack traces in prod) ──────────────
APP_ENV = os.environ.get("APP_ENV", "development")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    detail = str(exc) if APP_ENV == "development" else "An internal error occurred."
    return JSONResponse(status_code=500, content={"detail": detail})

# ── Request logging middleware (with request ID for traceability) ─────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    req_id = str(uuid.uuid4())[:8]
    logger.info("[%s] → %s %s", req_id, request.method, request.url.path)
    response = await call_next(request)
    response.headers["X-Request-ID"] = req_id
    logger.info("[%s] ← %s %s %d", req_id, request.method, request.url.path, response.status_code)
    return response

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router,       prefix="/api")
app.include_router(employees.router,  prefix="/api")
app.include_router(drivers.router,    prefix="/api")
app.include_router(vehicles.router,   prefix="/api")
app.include_router(mappings.router,   prefix="/api")
app.include_router(routes.router,     prefix="/api")
app.include_router(requests.router,   prefix="/api")
app.include_router(dashboard.router,  prefix="/api")
app.include_router(uploads.router,    prefix="/api")

# ── Health check ─────────────────────────────────────────────────────────────
@app.get("/api/health", tags=["Health"])
def health_check():
    """Liveness + DB connectivity probe."""
    try:
        conn = get_connection()
        conn.execute("SELECT 1")
        conn.close()
        db_status = "ok"
    except Exception as e:
        logger.error("DB health check failed: %s", e)
        db_status = "error"

    status = "ok" if db_status == "ok" else "degraded"
    return {
        "status":  status,
        "version": "2.0.0",
        "db":      db_status,
        "env":     APP_ENV,
    }


@app.get("/", tags=["Health"])
def root():
    return {
        "app":     "Bus Transportation Booking System",
        "version": "2.0.0",
        "docs":    "/docs",
        "health":  "/api/health",
        "status":  "running",
    }


# ── Bootstrap ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logger.info("Initialising database …")
    init_db()
    logger.info("Database ready.")

    PORT = int(os.environ.get("PORT", 8080))
    logger.info("Starting server on port %d (env=%s)", PORT, APP_ENV)

    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=PORT,
        reload=(APP_ENV == "development"),
        # Only watch source directories — exclude env/ to prevent false reloads
        reload_dirs=[
            str(BASE_DIR / "routers"),
            str(BASE_DIR / "core"),
            str(BASE_DIR / "db"),
            str(BASE_DIR / "schemas"),
            str(BASE_DIR),
        ] if APP_ENV == "development" else None,
        reload_excludes=["env/*", "logs/*", "uploads/*", "*.db"] if APP_ENV == "development" else None,
    )
