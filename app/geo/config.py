"""Shared settings for the Jani geo pipeline (cooperative outlier map).

Every number here is either a cited source or labelled as an assumption.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "cache"            # raw downloads and rasters, git-ignored
DATA = ROOT / "data"              # small derived files, committed
OUT = ROOT.parent / "public" / "geo"

# Area of interest: Mathira West, Nyeri County, Kenya, inside the coffee belt
# (about 1,700 to 1,850 m). The plots are synthetic; the land under them is real.
AREA_NAME = "Mathira West, Nyeri County, Kenya (reference area)"
BBOX = (37.050, -0.480, 37.090, -0.440)   # lon_min, lat_min, lon_max, lat_max (WGS84)
UTM_EPSG = 32737                           # WGS 84 / UTM zone 37S, Sentinel-2 tile 37MBV
S2_TILE = "37MBV"

# Sentinel-2 L2A via Element 84 Earth Search (AWS open data).
STAC_URL = "https://earth-search.aws.element84.com/v1"
S2_COLLECTION = "sentinel-2-l2a"
SCENE_CLOUD_MAX = 70          # scene-level filter only; pixels are masked with SCL
# SCL classes kept as clear land: 4 vegetation, 5 not vegetated. Everything else
# (no data, saturated, dark/shadow, cloud shadow, water, unclassified, cloud
# medium/high, cirrus, snow) is masked.
SCL_CLEAR = (4, 5)

# Dry-season composites. January to mid March is the main dry season in the
# central highlands; coffee is evergreen, so canopy stays visible while annual
# crops are bare. One composite per coffee year, same calendar window each year
# so phenology does not drive the change.
DRY_SEASONS = {
    "2022/23": ("2023-01-01", "2023-03-15"),
    "2023/24": ("2024-01-01", "2024-03-15"),
    "2024/25": ("2025-01-01", "2025-03-15"),
    "2025/26": ("2026-01-01", "2026-03-15"),
}
CURRENT_SEASON = "2025/26"
COFFEE_YEARS = list(DRY_SEASONS.keys())   # coffee year runs 1 Oct to 30 Sep

# NASA POWER daily rainfall (PRECTOTCORR, mm/day) at the AOI centre.
POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
POWER_START = "19910101"
POWER_END = "20260930"
CLIMATOLOGY = (1991, 2020)

# Yield baseline for synthetic deliveries.
# Nyeri County average about 3.0 kg cherry per tree (MOALF 2014, cited in
# Mugendi, Orero and Mwiti, Asian Journal of Business and Management 3(6), 2015,
# data for the 2013/14 coffee year).
BASE_KG_PER_TREE = 3.0
# Planting density for traditional types (SL28, SL34): 1,300 trees per ha
# (Coffee Directorate, Coffee Year Book 2022/23).
TREES_PER_HA = 1300

# Outlier model thresholds (assumptions, tuned on nothing real: there is no
# real delivery data in this build).
Z_FLAG = 3.0            # |robust z| at or above this is an outlier
Z_CORROBORATED = 2.0   # delivery drop threshold when canopy loss (z <= -3) backs it up
Z_CANOPY_NORMAL = -1.5  # NDVI change z above this counts as "canopy looks normal"
LOCAL_K = 12            # nearest plots used as the local canopy baseline
MIN_PRIOR_SEASONS = 2   # fewer prior deliveries than this: abstain
MIN_CLEAR_PIXELS = 15   # fewer clear 10 m pixels in the current composite: abstain
MIN_CLEAR_FRACTION = 0.5
MIN_AREA_HA = 0.10      # below about 10 Sentinel-2 pixels: abstain on NDVI
MAX_KG_PER_TREE = 10.0  # above this is beyond reported good-practice yields in
                        # Nyeri (6 to 10 kg, Nyeri County Government): check records
SEED = 20261004
