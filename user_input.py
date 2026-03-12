"""
user_input.py
-------------
All interactive user prompts in one place.
Collects iLO connection details and configuration preferences
before any API calls are made.
"""

import getpass

from config import PRIMARY_NTP, SECONDARY_NTP


def get_user_inputs():
    """
    Interactively prompt the user for all required inputs.

    NTP servers are NOT prompted — they use the defaults from config.py:
        Primary   : pool.ntp.org
        Secondary : time.google.com

    Returns:
        Tuple of:
            ilo_ip      (str)  — iLO IP address
            username    (str)  — iLO login username
            password    (str)  — iLO login password (hidden input)
            tz_name     (str)  — partial timezone name, or '' to skip
            ntp_servers (list) — [PRIMARY_NTP, SECONDARY_NTP] from config
            list_tz     (bool) — True if user wants to list timezones first
            do_reset    (bool) — True if user wants iLO reset after changes
    """
    print("=" * 55)
    print("  HPE iLO DateTime Configuration via Redfish API")
    print("=" * 55)

    # ── iLO Connection Details ─────────────────────────────────────────────────
    print("\n── iLO Connection ─────────────────────────────")
    ilo_ip   = input("  iLO IP Address  : ").strip()
    username = input("  Username        : ").strip()
    password = getpass.getpass("  Password        : ")

    # ── Timezone ──────────────────────────────────────────────────────────────
    print("\n── Timezone ───────────────────────────────────")
    print("  iLO uses Windows-style names (NOT IANA names like Asia/Kolkata).")
    print("  Enter a partial word to search. Examples:")
    print("    'India'   →  India Standard Time")
    print("    'UTC'     →  UTC")
    print("    'Eastern' →  Eastern Standard Time")
    print("  Leave blank to skip timezone change.")
    tz_name = input("  Timezone        : ").strip()

    # ── NTP Servers (from config — no prompt needed) ──────────────────────────
    ntp_servers = [PRIMARY_NTP, SECONDARY_NTP]
    print("\n── NTP Servers ────────────────────────────────")
    print("  Primary NTP   : {}".format(ntp_servers[0]))
    print("  Secondary NTP : {}".format(ntp_servers[1]))

    # ── Options ───────────────────────────────────────────────────────────────
    print("\n── Options ────────────────────────────────────")
    list_tz  = input("  List all available timezones first? [y/N] : ").strip().lower() == "y"
    do_reset = input("  Reset iLO after changes?            [y/N] : ").strip().lower() == "y"

    return ilo_ip, username, password, tz_name, ntp_servers, list_tz, do_reset
