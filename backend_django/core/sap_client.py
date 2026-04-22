"""
core/sap_client.py  –  SAP Employee API client (Basic Auth)
"""
import os
import logging
import urllib.request
import urllib.error
import base64
import json

logger = logging.getLogger(__name__)


def get_employee_from_sap(pernr: str):
    """
    Fetch employee data from SAP API by PERNR.
    Returns mapped dict on success, None if not found or API unreachable.
    """
    # Read at call time so load_dotenv() in settings.py is guaranteed to have run
    sap_url      = os.environ.get("SAP_API_URL",      "http://192.168.2.21:5050")
    sap_user     = os.environ.get("SAP_API_USER",     "")
    sap_password = os.environ.get("SAP_API_PASSWORD", "")

    url = f"{sap_url}/api/employees/{pernr}"   # no trailing slash — matches SAP server

    token = base64.b64encode(f"{sap_user}:{sap_password}".encode()).decode()
    req = urllib.request.Request(url, headers={
        "Authorization": f"Basic {token}",
        "Accept":        "application/json",
    })

    logger.debug("SAP lookup → %s (user=%s)", url, sap_user)

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode())

        logger.debug("SAP response for %s: status=%s count=%s",
                     pernr, body.get("status"), body.get("count"))

        if not body.get("status") or not body.get("data"):
            logger.warning("SAP returned no data for PERNR %s", pernr)
            return None

        emp = body["data"][0]

        status_text = emp.get("employment_status_text", "")
        if status_text.strip().lower() != "active":
            logger.warning("SAP employee %s is not active: '%s'", pernr, status_text)
            return None

        return {
            "pernr":       str(emp.get("personnel_number", pernr)),
            "ename":       emp.get("employee_full_name",      ""),
            "designation": emp.get("employee_sub_group_text", ""),
            "department":  emp.get("personnel_area_text",     ""),
            "email":       emp.get("email_address",           ""),
            "mobile_no":   emp.get("mobile_number",           ""),
            "werks":       emp.get("personnel_area_code",     ""),
            "persg":       emp.get("employee_group_code",     ""),
            "persk":       emp.get("employee_sub_group_code", ""),
        }

    except urllib.error.HTTPError as e:
        logger.error("SAP API HTTP %s for PERNR %s: %s", e.code, pernr, e)
        if e.code == 404:
            return None
        return None
    except urllib.error.URLError as e:
        logger.error("SAP API unreachable for PERNR %s: %s", pernr, e.reason)
        return None
    except Exception as e:
        logger.exception("SAP API unexpected error for PERNR %s: %s", pernr, e)
        return None
