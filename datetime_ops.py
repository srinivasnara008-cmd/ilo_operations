"""
datetime_ops.py
---------------
All iLO DateTime operations:
  - Fetch current DateTime settings
  - List available timezones
  - Find timezone index by partial name
  - Set timezone + PropagateTimeToHost
  - Set static NTP servers
"""

from http_client import safe_get, safe_patch, pretty_print


def get_datetime(session):
    """
    Fetch the current DateTime resource from iLO.

    Args:
        session: IloSession instance

    Returns:
        DateTime resource as dict, or None on failure.
    """
    print("[INFO] Fetching current DateTime settings of iLO...")
    return safe_get(session, session.datetime_url, "DateTime")


def display_datetime(data):
    """
    Print a clean summary of the key DateTime fields.

    Args:
        data: DateTime resource dict returned by get_datetime()
    """
    print("\n── Current DateTime Info ──────────────────────")
    pretty_print({
        "DateTime"           : data.get("DateTime"),
        "TimeZone"           : data.get("TimeZone", {}).get("Name"),
        "NTPServers"         : data.get("NTPServers"),
        "StaticNTPServers"   : data.get("StaticNTPServers"),
        "PropagateTimeToHost": data.get("PropagateTimeToHost"),
    })


def list_timezones(data):
    """
    Print all timezones available on this iLO with their index numbers.
    The index is what iLO requires when setting a timezone via PATCH.

    Args:
        data: DateTime resource dict returned by get_datetime()
    """
    tz_list = data.get("TimeZoneList", [])
    if not tz_list:
        print("[WARN] No TimeZoneList found in iLO response.")
        return

    print("\n{:<8} {}".format("Index", "Timezone Name"))
    print("-" * 65)
    for tz in tz_list:
        print("{:<8} {}".format(tz.get("Index", "?"), tz.get("Name", "?")))

    print("\nTip: Enter any partial word from the Name column as your timezone.")
    print("     e.g. 'India'  →  'India Standard Time'")
    print("     e.g. 'UTC'    →  'UTC'")
    print("     e.g. 'Eastern'→  'Eastern Standard Time'\n")


def find_timezone_index(data, tz_name):
    """
    Search iLO's TimeZoneList for a timezone whose name contains tz_name.
    Case-insensitive partial match — so 'India' matches 'India Standard Time'.

    Args:
        data   : DateTime resource dict
        tz_name: Partial timezone name entered by the user

    Returns:
        (index, full_name) if found, or (None, None) if no match.
    """
    tz_list = data.get("TimeZoneList", [])
    for tz in tz_list:
        if tz_name.lower() in tz.get("Name", "").lower():
            return tz.get("Index"), tz.get("Name")
    return None, None


def set_timezone(session, index):
    """
    Set the iLO timezone and enable PropagateTimeToHost in a single PATCH call.

    PropagateTimeToHost=True ensures iLO pushes its corrected time to the
    Host OS on the next server boot — so both clocks stay in sync.

    Args:
        session: IloSession instance
        index  : Timezone index from iLO's TimeZoneList

    Returns:
        Response dict on success, None on failure.
    """
    print("[INFO] Setting timezone (Index {}) and enabling PropagateTimeToHost...".format(index))
    payload = {
        "TimeZone"           : {"Index": index},
        "PropagateTimeToHost": True
    }
    return safe_patch(session, session.datetime_url, payload, "Set Timezone + PropagateTimeToHost")


def set_ntp_servers(session, servers):
    """
    Set static NTP servers on iLO.

    Only patches StaticNTPServers — the NTPServers field is read-only
    (managed by DHCP) and patching it causes a 400 Bad Request error.

    Empty strings and '0.0.0.0' placeholders are filtered out before sending,
    as iLO rejects them with a 400 error.

    Args:
        session: IloSession instance
        servers: List of NTP server hostnames or IPs

    Returns:
        Response dict on success, None on failure.
    """
    # Remove empty strings and 0.0.0.0 placeholders
    clean = [s for s in servers if s.strip() and s.strip() != "0.0.0.0"]

    if not clean:
        print("[WARN] No valid NTP servers to set after filtering empty/placeholder values.")
        return None

    print("[INFO] Setting NTP servers: {}".format(clean))
    payload = {"StaticNTPServers": clean}
    return safe_patch(session, session.datetime_url, payload, "Set NTP Servers")
