import json

import requests
import pandas as pd
import os
from dotenv import load_dotenv
from pathlib import Path

# Global Variables
load_dotenv()
api_key = os.getenv('college_api_key')
H = {"Authorization": f"Bearer {api_key}"}
Host = "https://api.collegefootballdata.com"

# Config File Save 
PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "data" / "college_data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Pull 2025-2026 draft picks and 2024-2025 college stats
college_data = {}

# Draft Data
college_data['2025_draft'] = requests.get(f"{Host}/draft/picks", headers=H, params={"year": 2025}).json()
college_data['2026_draft'] = requests.get(f"{Host}/draft/picks", headers=H, params={"year": 2026}).json()

# College Stats
college_data['2024_stats'] = requests.get(f"{Host}/stats/player/season", headers=H,
                     params={"year": 2024, "seasonType": "both"}).json()
college_data['2025_stats'] = requests.get(f"{Host}/stats/player/season", headers=H,
                     params={"year": 2025, "seasonType": "both"}).json()

for setname, dataset in college_data.items():
    path = OUTPUT_DIR / setname
    with open(path, "w") as f:
        json.dump(dataset, f, indent=2)
    print(f"Saved {path} ({len(dataset)} records)")
