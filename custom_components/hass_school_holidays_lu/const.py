"""Constants for the School holidays Luxembourg calendar integration."""

import datetime

# Integration Domain
DOMAIN = "hass_school_holidays_lu"

# Configuration Keys
CONF_LANGUAGE = "language"

# Static Data URL
DEFAULT_URL = (
    "https://data.public.lu/en/datasets/r/4902766f-1cd3-404c-ab6a-327ec104d564"
)

SUPPORTED_LANGUAGES = ["EN", "FR", "DE", "LB"]

SCAN_INTERVAL = datetime.timedelta(days=1)
