"""Constants for the Phoenix Contact CHARX integration."""

DOMAIN = "phoenixcontact_charx"

CONF_NUM_CHARGING_POINTS = "num_charging_points"
CONF_MAC = "mac"

DEFAULT_PORT = 502
DEFAULT_SCAN_INTERVAL = 30  # seconds
DEFAULT_POLL_TIMEOUT = 10  # seconds
DEFAULT_NUM_CHARGING_POINTS = 1

MAX_CHARGING_POINTS = 12
MIN_CURRENT_A = 6
MAX_CURRENT_A = 80
