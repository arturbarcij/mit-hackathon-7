#!/usr/bin/env bash
# Rebuild the cooperative outlier map data. Needs internet for the first two steps.
set -euo pipefail
cd "$(dirname "$0")"
python3 fetch_ndvi.py   # Sentinel-2 dry-season NDVI composites -> cache/
python3 fetch_rain.py   # NASA POWER rainfall -> data/rainfall.json
python3 season.py       # rain onset and season windows from POWER -> data/season_support.json
python3 make_plots.py   # synthetic registry and planted scenarios -> data/
python3 outliers.py     # robust-z model -> ../public/geo/
python3 visit_plan.py   # officer visit plan, seed referrals -> ../public/geo/
python3 validate.py     # check outputs against kb/geo/CONTRACT.md
python3 -m pytest -q test_geo.py   # unit tests for the decision rules and the committed outputs
