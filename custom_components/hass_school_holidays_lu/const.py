"""Constants for the School holidays Luxembourg calendar integration."""

import datetime

# Integration Domain
DOMAIN = "hass_school_holidays_lu"

# Configuration Keys
CONF_LANGUAGE = "language"

# Static Data URL
DATA_URL = "https://data.public.lu/en/datasets/r/4902766f-1cd3-404c-ab6a-327ec104d564"

# Language codes as used by the dataset keys, mapped to their native names.
SUPPORTED_LANGUAGES = {
    "en": "English",
    "fr": "Français",
    "de": "Deutsch",
    "lb": "Lëtzebuergesch",
}
DEFAULT_LANGUAGE = "en"

FALLBACK_SUMMARY = "Unknown Event"

REQUEST_TIMEOUT = 20
UPDATE_INTERVAL = datetime.timedelta(days=1)
