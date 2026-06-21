#!/usr/bin/env python3
"""
Build data pipeline for Playoff Translation Lab.
Clones Gabriel1200's public repos and processes playoff stats into embedded JSON.
"""

import os
import sys
import json
import csv
import subprocess
import shutil
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any, Optional, Tuple

# ============================================================================
# CONFIG
# ============================================================================

DATA_DIR = Path("data")
EXTERNAL_DIR = Path("external_data")
OUTPUT_FILE = Path("data-package.json")

GABRIEL_REPOS = {
    "site_Data": "https://github.com/gabriel1200/site_Data",
    "player_sheets": "https://github.com/gabriel1200/player_sheets",
    "merged_playbyplay": "https://github.com/gabriel1200/merged_playbyplay",
    "pbpbacklog": "https://github.com/gabriel1200/pbpbacklog",
    "legacy_pbp": "https://github.com/gabriel1200/legacy_pbp",
}

PLAYER_SHEETS_PRIORITY_FOLDERS = [
    "game_report",
    "teamgame_report",
    "series",
    "series/team",
    "year_totals",
    "totals",
    "team_totals",
]

TARGET_YEARS = list(range(1997, 2027))
FEATURED_PLAYERS = [
    "LeBron James",
    "Stephen Curry",
    "Nikola Jokic",
    "Kobe Bryant",
    "Kevin Durant",
    "Giannis Antetokounmpo",
    "Tim Duncan",
    "Shaquille O'Neal",
    "Michael Jordan",
    "Dwyane Wade",
    "James Harden",
    "Luka Doncic",
]

# ============================================================================
# UTILITIES
# ============================================================================

def clone_or_update_repo(url: str, dest: Path) -> Path:
    """Clone or update a GitHub repo using sparse checkout for large ones."""
    dest_path = EXTERNAL_DIR / dest
    
    if dest_path.exists():
        print(f"  Updating {dest}...")
        os.chdir(dest_path)
        subprocess.run(["git", "pull"], check=False, capture_output=True)
        os.chdir(Path.cwd())
    else:
        print(f"  Cloning {url}...")
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "clone", "--depth", "1", url, str(dest_path)],
            check=False,
            capture_output=True,
        )
    return dest_path

def sparse_checkout(repo_path: Path, folders: List[str]):
    """Enable sparse checkout for specific folders in a repo."""
    os.chdir(repo_path)
    for folder in folders:
        subprocess.run(
            ["git", "sparse-checkout", "add", folder],
            check=False,
            capture_output=True,
        )
    os.chdir(Path.cwd())

def find_csv_files(directory: Path, pattern: Optional[str] = None) -> List[Path]:
    """Find all CSV files in directory, optionally filtered by name pattern."""
    if not directory.exists():
        return []
    files = list(directory.glob("**/*.csv"))
    if pattern:
        files = [f for f in files if pattern in f.name]
    return sorted(files)

def load_csv(filepath: Path) -> List[Dict[str, Any]]:
    """Load CSV file into list of dicts."""
    if not filepath.exists():
        return []
    rows = []
    try:
        with open(filepath, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    except Exception as e:
        print(f"  Warning: Could not load {filepath}: {e}")
    return rows

def safe_float(val: Any) -> Optional[float]:
    """Safely convert value to float, return None if invalid."""
    if val is None or val == "" or val == "—":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None

def safe_int(val: Any) -> Optional[int]:
    """Safely convert value to int, return None if invalid."""
    if val is None or val == "" or val == "—":
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None

def format_stat(val: Optional[float], decimals: int = 1) -> str:
    """Format stat for display. Use '—' for missing."""
    if val is None:
        return "—"
    return f"{val:.{decimals}f}"

# ============================================================================
# DATA LOADING
# ============================================================================

def fetch_external_data() -> Dict[str, Any]:
    """Fetch all external data from Gabriel's repos."""
    print("Fetching external data...")
    data = {}
    
    # Clone site_Data
    site_data_path = clone_or_update_repo(GABRIEL_REPOS["site_Data"], Path("site_Data"))
    data["site_data_path"] = site_data_path
    
    # Clone player_sheets with sparse checkout
    player_sheets_path = clone_or_update_repo(GABRIEL_REPOS["player_sheets"], Path("player_sheets"))
    # sparse_checkout(player_sheets_path, PLAYER_SHEETS_PRIORITY_FOLDERS)
    data["player_sheets_path"] = player_sheets_path
    
    # Clone other repos
    for name, url in GABRIEL_REPOS.items():
        if name not in ["site_Data", "player_sheets"]:
            repo_path = clone_or_update_repo(url, Path(name))
            data[f"{name}_path"] = repo_path
    
    return data

def load_player_stats(external_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Load all player stats from CSV files."""
    print("Loading player stats...")
    players = {}
    
    player_sheets_path = external_data.get("player_sheets_path")
    if not player_sheets_path:
        return players
    
    # Find all player files
    csv_files = find_csv_files(player_sheets_path)
    
    for csv_file in csv_files:
        rows = load_csv(csv_file)
        for row in rows:
            player_name = row.get("Player") or row.get("player") or row.get("NAME")
            if not player_name:
                continue
            
            if player_name not in players:
                players[player_name] = {
                    "name": player_name,
                    "seasons": defaultdict(lambda: defaultdict(dict)),
                    "series": defaultdict(list),
                    "games": defaultdict(list),
                    "impact": defaultdict(dict),
                }
            
            # Extract year from row
            year_col = next((col for col in row.keys() if "year" in col.lower() or "season" in col.lower()), None)
            year = safe_int(row.get(year_col)) if year_col else None
            
            # Store raw row for later processing
            if year:
                players[player_name]["_raw_rows"] = players[player_name].get("_raw_rows", [])
                players[player_name]["_raw_rows"].append((row, csv_file.name))
    
    return players

def build_season_translations(players: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Build season-level translations with PTS/75 and relative stats."""
    print("Building season translations...")
    
    for player_name, player_data in players.items():
        for row, filename in player_data.get("_raw_rows", []):
            year = safe_int(row.get("Year")) or safe_int(row.get("year"))
            if not year or year not in TARGET_YEARS:
                continue
            
            # Extract key stats
            stats = {
                "MIN": safe_float(row.get("MIN")),
                "PTS": safe_float(row.get("PTS")),
                "REB": safe_float(row.get("REB")),
                "AST": safe_float(row.get("AST")),
                "TOV": safe_float(row.get("TOV")),
                "TS%": safe_float(row.get("TS%")),
                "eFG%": safe_float(row.get("eFG%")),
                "ORTG": safe_float(row.get("ORTG")),
                "DRTG": safe_float(row.get("DRTG")),
            }
            
            # Calculate PTS/75 if needed
            if stats["PTS"]:
                possessions = safe_float(row.get("Possessions")) or safe_float(row.get("OffPoss"))
                if possessions and possessions > 0:
                    stats["PTS/75"] = (stats["PTS"] / possessions) * 75
                else:
                    # Assume per-100 and scale
                    stats["PTS/75"] = stats["PTS"] * 0.75
            
            # Store season data
            player_data["seasons"][year]["stats"] = {k: v for k, v in stats.items() if v is not None}
            player_data["seasons"][year]["source"] = filename
    
    return players

def build_season_series(players: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Build series-level aggregations."""
    print("Building series aggregations...")
    # This requires series-level CSV data from Gabriel's repos
    # For now, we'll use placeholder structure
    return players

def build_game_logs(players: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Build game-level data."""
    print("Building game logs...")
    # This requires game-level CSV data
    # For now, we'll use placeholder structure
    return players

def build_impact_metrics(players: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Build on-court impact and skill split data."""
    print("Building impact metrics...")
    # This requires detailed CSV files like pbp_totals_ps.csv, windex_ps.csv, etc.
    return players

# ============================================================================
# DATA EXPORT
# ============================================================================

def export_data_package(players: Dict[str, Dict[str, Any]], output_file: Path):
    """Export final data package as JSON."""
    print(f"Exporting data package to {output_file}...")
    
    # Build compact export format
    data_package = {
        "version": "1.0",
        "generated": "2026-06-21",
        "players": {},
        "playerSeasons": [],
        "playerSeries": [],
        "playerGames": [],
        "teamBenchmarks": [],
        "playerImpact": [],
        "playerSkillSplits": [],
        "rankings": [],
        "metadata": {
            "targetYears": TARGET_YEARS,
            "featuredPlayers": FEATURED_PLAYERS,
            "sourceRepos": list(GABRIEL_REPOS.keys()),
        }
    }
    
    # Flatten players into arrays
    for player_name, player_data in players.items():
        player_id = player_name.lower().replace(" ", "_")
        
        data_package["players"][player_id] = {
            "id": player_id,
            "name": player_name,
            "featured": player_name in FEATURED_PLAYERS,
        }
        
        # Add season rows
        for year, season_data in player_data["seasons"].items():
            if season_data.get("stats"):
                data_package["playerSeasons"].append({
                    "playerId": player_id,
                    "year": year,
                    **season_data["stats"]
                })
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data_package, f, indent=2)
    
    print(f"  Exported {len(data_package['players'])} players")
    print(f"  Exported {len(data_package['playerSeasons'])} season rows")

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main build pipeline."""
    print("=== Playoff Translation Lab Build ===\n")
    
    # Setup directories
    EXTERNAL_DIR.mkdir(exist_ok=True)
    DATA_DIR.mkdir(exist_ok=True)
    
    # Fetch external data
    external_data = fetch_external_data()
    
    # Load and process data
    players = load_player_stats(external_data)
    players = build_season_translations(players)
    players = build_season_series(players)
    players = build_game_logs(players)
    players = build_impact_metrics(players)
    
    # Export
    export_data_package(players, OUTPUT_FILE)
    
    print("\n=== Build Complete ===")
    print(f"Data package: {OUTPUT_FILE}")
    print(f"Players loaded: {len(players)}")

if __name__ == "__main__":
    main()
