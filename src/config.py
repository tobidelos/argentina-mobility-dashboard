import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'
SRC_DIR = BASE_DIR / 'src'

# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

# File paths
TRANSPORT_CSV_PATH = DATA_DIR / 'dat-ab-usos-2025.csv'
DB_PATH = DATA_DIR / 'movilidad_urbana.db'

# ETL Settings
API_LAT = -34.6037
API_LON = -58.3816
START_DATE = "2025-01-01"
END_DATE = "2025-12-31"
