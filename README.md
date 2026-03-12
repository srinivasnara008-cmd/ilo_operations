# HPE iLO DateTime Configuration Tool

Configures timezone, NTP servers, and PropagateTimeToHost on HPE iLO
via the Redfish API. Automatically handles DHCP NTP locks and waits
for iLO to come back online after reset.

## Project Structure

```
ilo_datetime/
├── main.py          # Entry point — orchestrates the full flow
├── config.py        # Constants: NTP defaults, URLs, timeouts
├── session.py       # Redfish HTTP session management
├── http_client.py   # safe_get / safe_patch with error handling
├── dhcp.py          # DHCP NTP lock detection and disable
├── datetime_ops.py  # Get/set timezone, NTP, PropagateTimeToHost
├── ilo_reset.py     # iLO graceful reset + wait for online
└── user_input.py    # All interactive user prompts
```

## Requirements

```bash
pip install requests urllib3
```

## Usage

```bash
cd ilo_datetime
python main.py
```

## What It Does

1. Prompts for iLO IP, username, password, timezone
2. Fetches and displays current DateTime settings
3. Detects and disables DHCP NTP lock if active
4. Sets timezone + enables `PropagateTimeToHost`
5. Sets NTP servers (`pool.ntp.org`, `time.google.com`)
6. Displays updated settings
7. Resets iLO and waits until it is fully back online

## Changing Default NTP Servers

Edit `config.py`:

```python
PRIMARY_NTP   = "10.1.1.50"    # your internal NTP
SECONDARY_NTP = "10.1.1.51"
```

## Notes

- iLO uses **Windows-style timezone names** (not IANA).
  Enter a partial word e.g. `India`, `UTC`, `Eastern`, `Tokyo`.
- `NTPServers` is read-only (DHCP-managed). Only `StaticNTPServers` is patched.
- Timezone changes require an iLO reset to take effect.
- `PropagateTimeToHost` syncs iLO time to the Host OS on next server boot.
