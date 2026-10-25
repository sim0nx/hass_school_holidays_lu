# School Holidays Luxembourg

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/docs/faq/custom_repositories)
[![Validate](https://github.com/sim0nx/hass_school_holidays_lu/actions/workflows/validate.yml/badge.svg)](https://github.com/sim0nx/hass_school_holidays_lu/actions/workflows/validate.yml)

<img src="custom_components/hass_school_holidays_lu/brand/icon.png" alt="School Holidays Luxembourg logo" width="128">

Home Assistant integration that adds a calendar with the school holidays in
Luxembourg, based on the [official dataset on data.public.lu](https://data.public.lu/en/datasets/school-holidays-in-luxembourg/).

## Installation

Add this repository as a custom repository in HACS, or copy
`custom_components/hass_school_holidays_lu` into your Home Assistant
`config/custom_components` folder. Requires Home Assistant 2025.3 or newer;
the integration logo is shown from Home Assistant 2026.3 onwards.

## Configuration

Add the integration from **Settings → Devices & services**. Pick the language
for the holiday names (English, Français, Deutsch or Lëtzebuergesch). The form
defaults to your Home Assistant language, or English if it isn't supported.

The calendar is `on` while a school holiday is in progress, and its attributes
show the current or next holiday. The data is refreshed once a day.

## Development

```bash
pip install -r requirements_test.txt
pytest
```

## License

Licensed under the Apache License 2.0. See [LICENSE](LICENSE).
