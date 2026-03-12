"""
config.py
---------
Central place for all constants and default configuration values.
To change NTP servers, edit PRIMARY_NTP and SECONDARY_NTP here.
"""

# ── Default NTP Servers ───────────────────────────────────────────────────────
# These are applied to every iLO automatically — no user input needed.
PRIMARY_NTP   = "pool.ntp.org"
SECONDARY_NTP = "time.google.com"

# ── Redfish API URL Templates ─────────────────────────────────────────────────
# {base} will be replaced at runtime with https://<ilo_ip>
DATETIME_PATH = "/redfish/v1/Managers/1/DateTime"
RESET_PATH    = "/redfish/v1/Managers/1/Actions/Manager.Reset"
NIC_PATH      = "/redfish/v1/Managers/1/EthernetInterfaces/1"

# ── HTTP Request Settings ─────────────────────────────────────────────────────
REQUEST_TIMEOUT   = 30      # seconds — for all normal API calls
PING_TIMEOUT      = 10      # seconds — used when polling iLO after reset

# ── iLO Reset / Wait Settings ────────────────────────────────────────────────
RESET_INITIAL_WAIT = 20     # seconds — wait after reset before polling starts
RESET_POLL_INTERVAL = 10    # seconds — how often to ping iLO while waiting
RESET_MAX_WAIT     = 300    # seconds — give up after this long (5 minutes)

# ── Redfish Request Headers ───────────────────────────────────────────────────
DEFAULT_HEADERS = {
    "Content-Type": "application/json",
    "OData-Version": "4.0"
}
