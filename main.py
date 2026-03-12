"""
main.py
-------
Entry point for the HPE iLO DateTime Configuration tool.

Orchestrates the full flow:
    1. Collect inputs from user
    2. Build iLO session
    3. Fetch and display current DateTime settings
    4. Optionally list available timezones
    5. Check and disable DHCP NTP lock if active
    6. Set timezone + PropagateTimeToHost
    7. Set static NTP servers
    8. Display updated settings
    9. Reset iLO and wait for it to come back online

Usage:
    python main.py

Requirements:
    pip install requests urllib3
"""

from session       import IloSession
from user_input    import get_user_inputs
from datetime_ops  import get_datetime, display_datetime, list_timezones, find_timezone_index, set_timezone, set_ntp_servers
from dhcp          import check_dhcp_ntp_status, disable_dhcp_ntp_control
from ilo_reset     import reset_ilo


def main():

    # ── Step 1: Collect all inputs from the user ──────────────────────────────
    ilo_ip, username, password, tz_name, ntp_servers, list_tz, do_reset = get_user_inputs()

    print("\n" + "=" * 55)
    print("  Target : https://{}".format(ilo_ip))
    print("  User   : {}".format(username))
    print("=" * 55)

    # ── Step 2: Build Redfish session ─────────────────────────────────────────
    session = IloSession(ilo_ip, username, password)

    # ── Step 3: Fetch and display current DateTime settings ───────────────────
    data = get_datetime(session)
    if data is None:
        print("[FATAL] Could not reach iLO. Check IP address, credentials, and network.")
        return

    display_datetime(data)

    # ── Step 4: List timezones if user requested ──────────────────────────────
    if list_tz:
        list_timezones(data)
        again = input("Continue with changes? [y/N]: ").strip().lower()
        if again != "y":
            print("[EXIT] No changes made.")
            return

    # ── Step 5: Check for DHCP NTP lock and disable if needed ────────────────
    # Only run this check if the user actually wants to make changes.
    if tz_name or ntp_servers:
        dhcp_controlling = check_dhcp_ntp_status(session)

        if dhcp_controlling:
            print("\n[ACTION] DHCP is locking NTP/Timezone — manual changes are blocked.")
            confirm = input("         Disable DHCP NTP control to allow changes? [y/N]: ").strip().lower()

            if confirm == "y":
                success = disable_dhcp_ntp_control(session)
                if not success:
                    print("[WARN] Could not disable DHCP NTP control.")
                    proceed = input("       Continue anyway? [y/N]: ").strip().lower()
                    if proceed != "y":
                        print("[EXIT] No changes made.")
                        return
            else:
                print("[SKIP] DHCP NTP control not disabled.")
                print("       Changes will likely fail with a 400 error.")

    changes_made = False

    # ── Step 6: Set Timezone + PropagateTimeToHost ────────────────────────────
    if tz_name:
        print("\n── Setting Timezone ───────────────────────────")
        tz_index, tz_full_name = find_timezone_index(data, tz_name)

        if tz_index is None:
            print("[WARN] No timezone matching '{}' found.".format(tz_name))
            print("       Showing all available timezones on this iLO:\n")
            list_timezones(data)
        else:
            print("[INFO] Matched: '{}' (Index {})".format(tz_full_name, tz_index))
            result = set_timezone(session, tz_index)
            if result is not None:
                print("[OK]  Timezone and PropagateTimeToHost updated successfully.")
                changes_made = True
            else:
                print("[FAIL] Timezone change failed. See error above.")

    # ── Step 7: Set Static NTP Servers ───────────────────────────────────────
    if ntp_servers:
        print("\n── Setting NTP Servers ────────────────────────")
        result = set_ntp_servers(session, ntp_servers)
        if result is not None:
            print("[OK]  NTP servers updated successfully.")
            changes_made = True
        else:
            print("[FAIL] NTP update failed. See error above.")

    # ── Step 8: Display updated settings ─────────────────────────────────────
    if changes_made:
        print("\n── Updated DateTime Info ──────────────────────")
        updated = get_datetime(session)
        if updated:
            display_datetime(updated)
    else:
        print("\n[INFO] No changes were successfully applied.")

    # ── Step 9: Reset iLO and wait for it to come back ───────────────────────
    if changes_made and do_reset:
        print("\n── Resetting iLO ──────────────────────────────")
        print("[INFO] Reset required for timezone and PropagateTimeToHost to take effect.")
        reset_ilo(session)

    elif changes_made and not do_reset:
        print("\n[REMINDER] You chose not to reset iLO.")
        print("           Timezone changes will only take effect after an iLO reset.")

    print("\n[DONE]")


if __name__ == "__main__":
    main()
