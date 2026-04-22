"""
api/views/auth.py  –  Login (SAP-backed) + Admin utilities
"""
import logging
from datetime import date
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from api.throttling import LoginRateThrottle
from core.db import get_connection
from core.security import hash_password, verify_password, create_access_token
from core.sap_client import get_employee_from_sap

logger = logging.getLogger(__name__)

VALID_ROLES = {"EMPLOYEE", "APPROVER", "TRANSPORT_ADMIN"}


def _validate_password(password: str):
    errors = []
    if len(password) < 8:
        errors.append("at least 8 characters")
    if not any(c.isupper() for c in password):
        errors.append("one uppercase letter")
    if not any(c.isdigit() for c in password):
        errors.append("one number")
    return errors


class LoginView(APIView):
    """POST /api/auth/login/  –  SAP-backed login with rate limiting."""
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        pernr    = request.data.get("pernr", "").strip()
        password = request.data.get("password", "")

        if not pernr or not password:
            return Response(
                {"detail": "pernr and password are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Step 1 — Verify employee exists in SAP and is active
        sap = get_employee_from_sap(pernr)
        if not sap:
            logger.warning("Login failed – PERNR not found in SAP or inactive: %s", pernr)
            return Response(
                {"detail": "Employee not found or inactive. Contact HR or Transport Admin."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        today = date.today().isoformat()
        db = get_connection()
        try:
            # Step 2 — Check local DB for existing account
            row = db.execute(
                "SELECT * FROM ZEMP_MASTER_TABLE WHERE PERNR = %s", (pernr,)
            ).fetchone()

            if not row:
                # First login — auto-create local account using SAP data
                errors = _validate_password(password)
                if errors:
                    return Response(
                        {"detail": f"Password must contain: {', '.join(errors)}."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                db.execute(
                    "INSERT INTO ZEMP_MASTER_TABLE "
                    "(PERNR, ENAME, DESIGNATION, DEPARTMENT, WERKS, PERSG, PERSK, "
                    " ROLE, PASSWORD, EMAIL, MOBILE_NO, ZERDAT) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (sap["pernr"], sap["ename"], sap["designation"], sap["department"],
                     sap["werks"], sap["persg"], sap["persk"],
                     "EMPLOYEE", hash_password(password),
                     sap["email"], sap["mobile_no"], today)
                )
                db.commit()
                logger.info("Auto-created local account for PERNR: %s", pernr)
                row = db.execute(
                    "SELECT * FROM ZEMP_MASTER_TABLE WHERE PERNR = %s", (pernr,)
                ).fetchone()
            else:
                # Existing account — verify password
                if not verify_password(password, row["PASSWORD"]):
                    logger.warning("Login failed – wrong password for PERNR: %s", pernr)
                    return Response(
                        {"detail": "Incorrect password."},
                        status=status.HTTP_401_UNAUTHORIZED
                    )
                # Refresh SAP data in local DB
                db.execute(
                    "UPDATE ZEMP_MASTER_TABLE SET ENAME=%s, DESIGNATION=%s, DEPARTMENT=%s, "
                    "EMAIL=%s, MOBILE_NO=%s, WERKS=%s, PERSG=%s, PERSK=%s WHERE PERNR=%s",
                    (sap["ename"], sap["designation"], sap["department"],
                     sap["email"], sap["mobile_no"],
                     sap["werks"], sap["persg"], sap["persk"], pernr)
                )
                db.commit()

            logger.info("Login success – PERNR: %s role: %s", row["PERNR"], row["ROLE"])
            token = create_access_token({
                "sub":         row["PERNR"],
                "ename":       sap.get("ename") or row["ENAME"],
                "role":        row["ROLE"],
                "designation": sap.get("designation") or row["DESIGNATION"],
            })

            return Response({
                "access_token":  token,
                "token_type":    "bearer",
                "pernr":         row["PERNR"],
                "ename":         sap.get("ename") or row["ENAME"],
                "role":          row["ROLE"],
                "designation":   sap.get("designation") or row["DESIGNATION"],
                "department":    sap.get("department") or row["DEPARTMENT"],
                "address":       row["STRAS"],
                "email":         sap.get("email") or row["EMAIL"],
                "mobile_no":     sap.get("mobile_no") or row["MOBILE_NO"],
                "profile_photo": row["PROFILE_PHOTO"],
            })
        except Exception as e:
            db.rollback()
            logger.exception("Login error for PERNR %s: %s", pernr, e)
            return Response({"detail": "An internal error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            db.close()


class EmployeeProfileView(APIView):
    """GET /api/auth/employee/<pernr>/  –  Get employee profile."""

    def get(self, request, pernr):
        current_user = request.user
        if current_user.get("role") == "EMPLOYEE" and current_user.get("sub") != pernr:
            return Response(
                {"detail": "You can only view your own profile."},
                status=status.HTTP_403_FORBIDDEN
            )

        db = get_connection()
        try:
            row = db.execute(
                "SELECT * FROM ZEMP_MASTER_TABLE WHERE PERNR = %s", (pernr,)
            ).fetchone()
            if not row:
                return Response({"detail": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)

            return Response({
                "pernr":         row["PERNR"],
                "ename":         row["ENAME"],
                "role":          row["ROLE"],
                "designation":   row["DESIGNATION"],
                "department":    row["DEPARTMENT"],
                "address":       row["STRAS"],
                "email":         row["EMAIL"],
                "mobile_no":     row["MOBILE_NO"],
                "profile_photo": row["PROFILE_PHOTO"],
            })
        finally:
            db.close()


class SetRoleView(APIView):
    """PUT /api/auth/admin/set-role/<pernr>/  –  TRANSPORT_ADMIN only role change."""

    def put(self, request, pernr):
        current_user = request.user
        if current_user.get("role") != "TRANSPORT_ADMIN":
            return Response(
                {"detail": "Only Transport Admin can change roles."},
                status=status.HTTP_403_FORBIDDEN
            )

        role = request.data.get("role") or request.GET.get("role", "")
        if role not in VALID_ROLES:
            return Response(
                {"detail": f"Invalid role. Must be one of: {', '.join(VALID_ROLES)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        db = get_connection()
        try:
            row = db.execute("SELECT 1 FROM ZEMP_MASTER_TABLE WHERE PERNR = %s", (pernr,)).fetchone()
            if not row:
                return Response(
                    {"detail": "Employee not found. They must log in once first."},
                    status=status.HTTP_404_NOT_FOUND
                )

            db.execute(
                "UPDATE ZEMP_MASTER_TABLE SET ROLE = %s, ZAEDAT = %s WHERE PERNR = %s",
                (role, date.today().isoformat(), pernr)
            )
            db.commit()
            logger.info("Admin %s set role of %s to %s", current_user.get("sub"), pernr, role)
            return Response({"message": f"Role updated to {role}", "pernr": pernr})
        except Exception as e:
            db.rollback()
            logger.exception("Set role error: %s", e)
            return Response({"detail": "An internal error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            db.close()
