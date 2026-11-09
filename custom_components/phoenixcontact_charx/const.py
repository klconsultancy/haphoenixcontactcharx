"""Constants for the Phoenix Contact CHARX integration."""

from typing import Final

DOMAIN: Final = "phoenixcontact_charx"

# Kept in the entry's data; 1.x read the Charging Points it set up from it. Since 2.0 the
# library places them from the controller's own count, so this only records what the
# config flow found.
CONF_NUM_CHARGING_POINTS: Final = "num_charging_points"
CONF_MAC: Final = "mac"

DEFAULT_PORT: Final = 502
DEFAULT_SCAN_INTERVAL: Final = 30  # seconds

# CHARX answers on Modbus server address 1 only (manual, table B-6, and §2.5.8).
UNIT_ID: Final = 1

# One SEC-3xxx hosts up to 11 SEC-1000s: 12 Charging Points (manual §2.3.3).
MAX_CHARGING_POINTS: Final = 12
MIN_CURRENT_A: Final = 6
MAX_CURRENT_A: Final = 80

MANUFACTURER: Final = "Phoenix Contact"
# Register 100 holds the name set for the controller (ev3000), not its model.
MODEL: Final = "CHARX SEC"
