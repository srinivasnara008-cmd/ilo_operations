"""
http_client.py
--------------
Low-level HTTP helpers for Redfish API calls.
Wraps GET and PATCH with consistent error handling and iLO error message parsing.
All other modules use these functions instead of calling requests directly.
"""

import json
import requests

from config import REQUEST_TIMEOUT


def pretty_print(data):
    """Pretty-print a dictionary as indented JSON to stdout."""
    print(json.dumps(data, indent=2))


def safe_get(session, url, label):
    """
    Perform a GET request to the given URL.

    Args:
        session : IloSession instance
        url     : Full URL to GET
        label   : Human-readable name shown in error messages

    Returns:
        Response body as dict, or None if the request failed.
    """
    try:
        resp = session.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    except requests.exceptions.ConnectionError as e:
        print("[ERROR] Cannot connect to {} — {}".format(label, e))
        return None

    except requests.exceptions.Timeout:
        print("[ERROR] Request timed out for {}.".format(label))
        return None

    except requests.exceptions.HTTPError:
        print("[ERROR] HTTP {} on {} — {}".format(resp.status_code, label, url))
        return None

    except Exception as e:
        print("[ERROR] Unexpected error on GET {}: {}".format(label, e))
        return None


def safe_patch(session, url, payload, label):
    """
    Perform a PATCH request with the given JSON payload.
    Parses iLO's extended error messages on failure for clear diagnostics.

    Args:
        session : IloSession instance
        url     : Full URL to PATCH
        payload : dict to send as JSON body
        label   : Human-readable name shown in error messages

    Returns:
        Response body as dict on success, or None on failure.
    """
    try:
        resp = session.patch(url, json=payload, timeout=REQUEST_TIMEOUT)

    except requests.exceptions.ConnectionError as e:
        # RemoteDisconnected falls under ConnectionError.
        # This usually means iLO dropped the connection due to DHCP read-only lock.
        print("[ERROR] Connection dropped on {} — {}".format(label, e))
        print("        Likely cause: DHCP is managing NTP (read-only lock active).")
        return None

    except requests.exceptions.Timeout:
        print("[ERROR] Request timed out for {}.".format(label))
        return None

    except Exception as e:
        print("[ERROR] Unexpected error on PATCH {}: {}".format(label, e))
        return None

    if resp.status_code in (200, 202, 204):
        try:
            return resp.json()
        except Exception:
            return {}   # 204 No Content — success with empty body

    # ── Error: parse iLO's extended error info ────────────────────────────────
    print("[ERROR] HTTP {} on {} — {}".format(resp.status_code, label, url))
    try:
        err_body = resp.json()
        ext_info = err_body.get("error", {}).get("@Message.ExtendedInfo", [])
        for msg in ext_info:
            message_id  = msg.get("MessageId", "")
            message_txt = msg.get("Message", "")

            if "SNTPConfigurationManagedByDHCPAndIsReadOnly" in message_id:
                print("        iLO says : NTP/Timezone is DHCP-managed and read-only.")
                print("        Fix      : Script will attempt to disable DHCP NTP control.")
            elif message_txt:
                print("        iLO says : {}".format(message_txt))
            else:
                print("        MessageId: {}".format(message_id))

    except Exception:
        print("        Raw response: {}".format(resp.text[:300]))

    return None
