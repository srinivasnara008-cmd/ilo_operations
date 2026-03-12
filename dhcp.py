"""
dhcp.py
-------
Handles detection and disabling of DHCP-managed NTP control on iLO.

When DHCP controls NTP, iLO makes the DateTime fields read-only.
Any attempt to PATCH timezone or NTP will fail with:
    SNTPConfigurationManagedByDHCPAndIsReadOnly

This module checks for that lock and disables it so manual changes are allowed.
"""

import time

from config import RESET_POLL_INTERVAL
from http_client import safe_get, safe_patch


def check_dhcp_ntp_status(session):
    """
    Check whether DHCP is currently controlling NTP settings on this iLO.

    iLO stores DHCP NTP control flags under:
        Oem.Hpe.DHCPv4.UseNTPServers  (IPv4)
        Oem.Hpe.DHCPv6.UseNTPServers  (IPv6)

    Args:
        session: IloSession instance

    Returns:
        True  — DHCP is managing NTP (fields are read-only)
        False — DHCP is NOT managing NTP (fields are writable)
    """
    print("[INFO] Checking if DHCP controls NTP settings...")

    nic_data = safe_get(session, session.nic_url, "EthernetInterface")
    if nic_data is None:
        print("[WARN] Could not read EthernetInterface. Assuming DHCP is not controlling NTP.")
        return False

    hpe        = nic_data.get("Oem", {}).get("Hpe", {})
    dhcpv4     = hpe.get("DHCPv4", {})
    dhcpv6     = hpe.get("DHCPv6", {})
    use_ntp_v4 = dhcpv4.get("UseNTPServers", False)
    use_ntp_v6 = dhcpv6.get("UseNTPServers", False)

    if use_ntp_v4 or use_ntp_v6:
        print("[WARN] DHCP is managing NTP (DHCPv4={}, DHCPv6={}).".format(
            use_ntp_v4, use_ntp_v6))
        return True

    print("[OK]  DHCP is NOT managing NTP. Manual changes are allowed.")
    return False


def disable_dhcp_ntp_control(session):
    """
    Disable DHCP control over NTP by patching DHCPv4/DHCPv6 UseNTPServers to False.
    This unlocks the DateTime fields so timezone and NTP can be set manually.

    Args:
        session: IloSession instance

    Returns:
        True  — DHCP NTP control successfully disabled
        False — Failed to disable (check error output for details)
    """
    print("[INFO] Disabling DHCP NTP control on iLO...")

    nic_data = safe_get(session, session.nic_url, "EthernetInterface")
    if nic_data is None:
        print("[ERROR] Cannot read EthernetInterface. Cannot disable DHCP NTP control.")
        return False

    hpe        = nic_data.get("Oem", {}).get("Hpe", {})
    has_dhcpv4 = "DHCPv4" in hpe
    has_dhcpv6 = "DHCPv6" in hpe

    # Build payload only for DHCP versions that actually exist on this iLO
    oem_payload = {}
    if has_dhcpv4:
        oem_payload["DHCPv4"] = {"UseNTPServers": False}
    if has_dhcpv6:
        oem_payload["DHCPv6"] = {"UseNTPServers": False}

    if not oem_payload:
        print("[WARN] No DHCPv4/DHCPv6 section found. Cannot disable DHCP NTP control.")
        return False

    payload = {"Oem": {"Hpe": oem_payload}}
    result  = safe_patch(session, session.nic_url, payload, "Disable DHCP NTP Control")

    if result is not None:
        print("[OK]  DHCP NTP control disabled.")
        print("[INFO] Waiting {}s for iLO to apply the change...".format(RESET_POLL_INTERVAL))
        time.sleep(RESET_POLL_INTERVAL)
        return True

    print("[ERROR] Failed to disable DHCP NTP control.")
    print("        Manual fix: iLO Web UI → Network → iLO Dedicated Port")
    print("                    → IPv4 → uncheck 'Use DHCPv4 Supplied NTP Servers'")
    return False
