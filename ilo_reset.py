"""
ilo_reset.py
------------
Handles iLO graceful reset and waits until iLO is fully back online.

A reset is required after changing timezone or PropagateTimeToHost
for the changes to actually take effect.
"""

import time
import requests

from config import (
    RESET_INITIAL_WAIT,
    RESET_POLL_INTERVAL,
    RESET_MAX_WAIT,
    PING_TIMEOUT
)
from http_client import pretty_print


def wait_for_ilo_up(session):
    """
    Poll iLO every RESET_POLL_INTERVAL seconds until it responds or times out.
    Prints live status so the user knows the script is still running.

    iLO is considered back online when it returns any of:
        200 — fully up and authenticated
        401 — up but credentials needed (still counts as online)
        403 — up but access denied (still counts as online)

    Any connection error means iLO is still restarting — we keep polling.

    Args:
        session: IloSession instance

    Returns:
        True  — iLO responded within RESET_MAX_WAIT seconds
        False — iLO did not respond in time (may still be coming up)
    """
    print("[INFO] Polling iLO every {}s (max wait: {}s)...".format(
        RESET_POLL_INTERVAL, RESET_MAX_WAIT))

    elapsed = 0
    attempt = 1

    while elapsed < RESET_MAX_WAIT:
        time.sleep(RESET_POLL_INTERVAL)
        elapsed += RESET_POLL_INTERVAL
        print("[...] Attempt {:>2} — {:>3}s elapsed — pinging iLO...".format(attempt, elapsed))

        try:
            resp = session.get(session.datetime_url, timeout=PING_TIMEOUT)
            if resp.status_code in (200, 401, 403):
                print("[OK]  iLO is back online after {}s.".format(elapsed))
                return True
        except Exception:
            print("       iLO not responding yet — still restarting...")

        attempt += 1

    print("[WARN] iLO did not respond within {}s.".format(RESET_MAX_WAIT))
    print("       It may still be coming up. Check manually in a minute.")
    return False


def reset_ilo(session):
    """
    Send a GracefulRestart to iLO and then wait for it to come back online.

    Flow:
        1. POST GracefulRestart → iLO acknowledges and begins shutdown
        2. Wait RESET_INITIAL_WAIT seconds (iLO shutdown phase)
        3. Poll iLO until it responds (iLO restart phase)
        4. Confirm online status to the user

    Args:
        session: IloSession instance
    """
    print("\n[INFO] Sending GracefulRestart to iLO...")

    try:
        resp = session.post(
            session.reset_url,
            json={"Action": "Manager.Reset", "ResetType": "GracefulRestart"},
            timeout=30
        )
    except requests.exceptions.RequestException as e:
        print("[ERROR] Reset request failed: {}".format(e))
        return

    if resp.status_code not in (200, 202, 204):
        print("[WARN] Reset returned unexpected HTTP {}.".format(resp.status_code))
        try:
            pretty_print(resp.json())
        except Exception:
            pass
        return

    print("[OK]  iLO reset initiated.")
    print("[INFO] iLO will be unreachable for ~60 seconds while restarting.")
    print("[INFO] Giving iLO {}s to begin shutdown...".format(RESET_INITIAL_WAIT))
    time.sleep(RESET_INITIAL_WAIT)

    came_up = wait_for_ilo_up(session)

    if came_up:
        print("[OK]  iLO is fully back online. All changes have been applied.")
    else:
        print("[WARN] Could not confirm iLO is back online.")
        print("       Please check iLO manually to verify changes were applied.")
