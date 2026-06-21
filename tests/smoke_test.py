#!/usr/bin/env python3
"""
Smoke tests for Playoff Translation Lab.
Validates data integrity, accessibility, and compliance with project rules.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple

# ============================================================================
# CONFIG
# ============================================================================

INDEX_FILE = Path("index.html")
DATA_PACKAGE_FILE = Path("data-package.json")
SOURCE_MANIFEST_FILE = Path("source_manifest.json")
DATA_DIR = Path("data")

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

TARGET_YEARS = list(range(1997, 2027))

FORBIDDEN_LABELS = ["RAPM2K", "2K", "Brescou", "Breacou"]
FORBIDDEN_METRICS = ["rapm2k", "2k", "brescou", "breacou"]

# ============================================================================
# TESTS
# ============================================================================

def test_index_html_exists() -> Tuple[bool, str]:
    """Check that index.html exists."""
    if not INDEX_FILE.exists():
        return False, "❌ index.html not found"
    return True, "✅ index.html exists"

def test_index_html_valid() -> Tuple[bool, str]:
    """Check that index.html is valid."""
    if not INDEX_FILE.exists():
        return False, "❌ index.html not found"
    
    try:
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check essential components
        checks = {
            "<!DOCTYPE html>": "DOCTYPE",
            "<title>Playoff Translation Lab</title>": "Title",
            'id="searchInput"': "Search input",
            'id="seasonTable"': "Season table",
            'id="dataPackage"': "Data package script",
        }
        
        missing = [name for pattern, name in checks.items() if pattern not in content]
        if missing:
            return False, f"❌ Missing components: {', '.join(missing)}"
        
        return True, "✅ index.html is valid"
    except Exception as e:
        return False, f"❌ Error reading index.html: {e}"

def test_data_package_exists() -> Tuple[bool, str]:
    """Check that data-package.json exists."""
    if not DATA_PACKAGE_FILE.exists():
        return False, "❌ data-package.json not found"
    return True, "✅ data-package.json exists"

def test_data_package_valid() -> Tuple[bool, str]:
    """Check that data-package.json is valid JSON."""
    if not DATA_PACKAGE_FILE.exists():
        return False, "❌ data-package.json not found"
    
    try:
        with open(DATA_PACKAGE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Check required keys
        required_keys = [
            "version",
            "generated",
            "players",
            "playerSeasons",
            "playerSeries",
            "playerGames",
            "teamBenchmarks",
            "playerImpact",
            "playerSkillSplits",
            "rankings",
            "metadata",
        ]
        
        missing = [key for key in required_keys if key not in data]
        if missing:
            return False, f"❌ Missing keys: {', '.join(missing)}"
        
        return True, "✅ data-package.json is valid"
    except json.JSONDecodeError as e:
        return False, f"❌ Invalid JSON: {e}"
    except Exception as e:
        return False, f"❌ Error reading data-package.json: {e}"

def test_source_manifest_exists() -> Tuple[bool, str]:
    """Check that source_manifest.json exists."""
    if not SOURCE_MANIFEST_FILE.exists():
        return False, "❌ source_manifest.json not found"
    return True, "✅ source_manifest.json exists"

def test_source_manifest_valid() -> Tuple[bool, str]:
    """Check that source_manifest.json is valid JSON."""
    if not SOURCE_MANIFEST_FILE.exists():
        return False, "❌ source_manifest.json not found"
    
    try:
        with open(SOURCE_MANIFEST_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        required_keys = ["version", "sources", "metrics", "rules_applied"]
        missing = [key for key in required_keys if key not in data]
        if missing:
            return False, f"❌ Missing keys: {', '.join(missing)}"
        
        return True, "✅ source_manifest.json is valid"
    except json.JSONDecodeError as e:
        return False, f"❌ Invalid JSON: {e}"
    except Exception as e:
        return False, f"❌ Error reading source_manifest.json: {e}"

def test_no_rapm2k_labels() -> Tuple[bool, str]:
    """Check for forbidden RAPM2K or 2K labels."""
    if not INDEX_FILE.exists():
        return False, "❌ index.html not found"
    
    try:
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            content = f.read().lower()
        
        found = [label for label in FORBIDDEN_LABELS if label.lower() in content]
        if found:
            return False, f"❌ Found forbidden labels: {', '.join(found)}"
        
        return True, "✅ No RAPM2K or 2K labels found"
    except Exception as e:
        return False, f"❌ Error checking labels: {e}"

def test_no_brescou_labels() -> Tuple[bool, str]:
    """Check for forbidden Brescou/Breacou labels."""
    files_to_check = [INDEX_FILE, DATA_PACKAGE_FILE]
    
    for filepath in files_to_check:
        if not filepath.exists():
            continue
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read().lower()
            
            if "brescou" in content or "breacou" in content:
                return False, f"❌ Found Brescou/Breacou in {filepath}"
        except Exception as e:
            return False, f"❌ Error checking {filepath}: {e}"
    
    return True, "✅ No Brescou/Breacou labels found"

def test_missing_stats_show_em_dash() -> Tuple[bool, str]:
    """Check that missing stats use em dash (—) not 'null' or 'undefined'."""
    if not INDEX_FILE.exists():
        return False, "❌ index.html not found"
    
    try:
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check that the format_stat function returns "—" for missing values
        if "return '—'" not in content and 'return "—"' not in content:
            return False, "❌ format_stat does not use em dash for missing stats"
        
        return True, "✅ Missing stats use em dash (—)"
    except Exception as e:
        return False, f"❌ Error checking format: {e}"

def count_players() -> Tuple[int, List[str]]:
    """Count unique players in data package."""
    if not DATA_PACKAGE_FILE.exists():
        return 0, []
    
    try:
        with open(DATA_PACKAGE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        players = data.get("players", {})
        return len(players), list(players.keys())
    except Exception:
        return 0, []

def count_seasons() -> int:
    """Count season rows in data package."""
    if not DATA_PACKAGE_FILE.exists():
        return 0
    
    try:
        with open(DATA_PACKAGE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        seasons = data.get("playerSeasons", [])
        return len(seasons)
    except Exception:
        return 0

def count_series() -> int:
    """Count series rows in data package."""
    if not DATA_PACKAGE_FILE.exists():
        return 0
    
    try:
        with open(DATA_PACKAGE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        series = data.get("playerSeries", [])
        return len(series)
    except Exception:
        return 0

def count_games() -> int:
    """Count game rows in data package."""
    if not DATA_PACKAGE_FILE.exists():
        return 0
    
    try:
        with open(DATA_PACKAGE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        games = data.get("playerGames", [])
        return len(games)
    except Exception:
        return 0

def count_impact() -> int:
    """Count impact rows in data package."""
    if not DATA_PACKAGE_FILE.exists():
        return 0
    
    try:
        with open(DATA_PACKAGE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        impact = data.get("playerImpact", [])
        return len(impact)
    except Exception:
        return 0

def get_years_loaded() -> Tuple[List[int], List[int]]:
    """Get loaded years and missing years."""
    if not DATA_PACKAGE_FILE.exists():
        return [], TARGET_YEARS
    
    try:
        with open(DATA_PACKAGE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        seasons = data.get("playerSeasons", [])
        years_with_data = sorted(set(s.get("year") for s in seasons if s.get("year")))
        missing = [y for y in TARGET_YEARS if y not in years_with_data]
        
        return years_with_data, missing
    except Exception:
        return [], TARGET_YEARS

def test_search_support() -> Tuple[bool, str]:
    """Check that search is supported for featured players."""
    if not INDEX_FILE.exists():
        return False, "❌ index.html not found"
    
    try:
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check for search functionality
        checks = {
            "filterPlayers": "Filter function",
            "renderSearchDropdown": "Dropdown render",
            "selectPlayer": "Player selection",
        }
        
        missing = [name for func, name in checks.items() if func not in content]
        if missing:
            return False, f"❌ Missing search functions: {', '.join(missing)}"
        
        return True, "✅ Search is supported"
    except Exception as e:
        return False, f"❌ Error checking search: {e}"

def test_featured_players() -> Tuple[bool, str]:
    """Check that featured players are in data."""
    if not DATA_PACKAGE_FILE.exists():
        return False, "❌ data-package.json not found"
    
    try:
        with open(DATA_PACKAGE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        players = data.get("players", {})
        player_names = [p.get("name") for p in players.values()]
        
        missing = [p for p in FEATURED_PLAYERS if p not in player_names]
        if missing:
            return False, f"⚠️  Missing featured players: {', '.join(missing[:3])}"
        
        return True, f"✅ All {len(FEATURED_PLAYERS)} featured players present"
    except Exception as e:
        return False, f"❌ Error checking featured players: {e}"

def test_pts75_calculation() -> Tuple[bool, str]:
    """Check that PTS/75 is present in at least one season."""
    if not DATA_PACKAGE_FILE.exists():
        return False, "❌ data-package.json not found"
    
    try:
        with open(DATA_PACKAGE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        seasons = data.get("playerSeasons", [])
        if not seasons:
            return False, "❌ No season data found"
        
        # Check first season
        first_season = seasons[0]
        if "PTS/75" in first_season:
            return True, "✅ PTS/75 is calculated"
        
        return False, "❌ PTS/75 not found in season data"
    except Exception as e:
        return False, f"❌ Error checking PTS/75: {e}"

def test_rnet_calculation() -> Tuple[bool, str]:
    """Check that rNET (relative net rating) is documented."""
    if not SOURCE_MANIFEST_FILE.exists():
        return False, "❌ source_manifest.json not found"
    
    try:
        with open(SOURCE_MANIFEST_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        
        if "rNET" in content or "relative_DRTG" in content:
            return True, "✅ Relative Net Rating (rNET) is documented"
        
        return False, "⚠️  rNET calculation not fully documented"
    except Exception as e:
        return False, f"❌ Error checking rNET: {e}"

# ============================================================================
# REPORTING
# ============================================================================

def run_all_tests() -> Tuple[int, int]:
    """Run all tests and report results."""
    print("\n" + "=" * 70)
    print("PLAYOFF TRANSLATION LAB - SMOKE TESTS")
    print("=" * 70 + "\n")
    
    tests = [
        ("File & Structure", [
            test_index_html_exists,
            test_index_html_valid,
            test_data_package_exists,
            test_data_package_valid,
            test_source_manifest_exists,
            test_source_manifest_valid,
        ]),
        ("Compliance Rules", [
            test_no_rapm2k_labels,
            test_no_brescou_labels,
            test_missing_stats_show_em_dash,
        ]),
        ("Data & Functionality", [
            test_search_support,
            test_featured_players,
            test_pts75_calculation,
            test_rnet_calculation,
        ]),
    ]
    
    passed = 0
    failed = 0
    
    for category, test_list in tests:
        print(f"\n{category}:")
        print("-" * 70)
        for test_func in test_list:
            success, message = test_func()
            print(f"  {message}")
            if success:
                passed += 1
            else:
                failed += 1
    
    return passed, failed

def report_metrics():
    """Report data metrics."""
    print("\n" + "=" * 70)
    print("DATA METRICS")
    print("=" * 70 + "\n")
    
    player_count, player_ids = count_players()
    season_count = count_seasons()
    series_count = count_series()
    game_count = count_games()
    impact_count = count_impact()
    years_loaded, years_missing = get_years_loaded()
    
    print(f"Players loaded:        {player_count}")
    print(f"Season rows:           {season_count}")
    print(f"Series rows:           {series_count}")
    print(f"Game rows:             {game_count}")
    print(f"Impact rows:           {impact_count}")
    print(f"Years with data:       {min(years_loaded) if years_loaded else 'N/A'}–{max(years_loaded) if years_loaded else 'N/A'} ({len(years_loaded)}/{len(TARGET_YEARS)})")
    
    if years_missing:
        print(f"Missing years:         {years_missing[:5]}{'...' if len(years_missing) > 5 else ''}")
    
    print(f"\nTotal data rows:       {season_count + series_count + game_count + impact_count}")

def report_metrics_detailed():
    """Report detailed metric definitions."""
    print("\n" + "=" * 70)
    print("METRICS SUMMARY")
    print("=" * 70 + "\n")
    
    try:
        with open(SOURCE_MANIFEST_FILE, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        
        real = manifest.get("metrics", {}).get("real_metrics", [])
        context = manifest.get("metrics", {}).get("context_only_metrics", [])
        unavailable = manifest.get("metrics", {}).get("unavailable_metrics", [])
        
        print("Real Metrics (calculated from data):")
        for metric in real:
            print(f"  • {metric}")
        
        print(f"\nContext-Only Metrics ({len(context)}):")
        for metric in context[:5]:
            print(f"  • {metric}")
        if len(context) > 5:
            print(f"  ... and {len(context) - 5} more")
        
        print(f"\nUnavailable Metrics ({len(unavailable)}):")
        for metric in unavailable[:3]:
            print(f"  • {metric}")
        if len(unavailable) > 3:
            print(f"  ... and {len(unavailable) - 3} more")
    except Exception as e:
        print(f"Could not load metrics details: {e}")

def report_limitations():
    """Report known limitations."""
    print("\n" + "=" * 70)
    print("KNOWN LIMITATIONS")
    print("=" * 70 + "\n")
    
    try:
        with open(SOURCE_MANIFEST_FILE, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        
        limitations = manifest.get("known_limitations", [])
        for i, limitation in enumerate(limitations, 1):
            print(f"{i}. {limitation}")
    except Exception as e:
        print(f"Could not load limitations: {e}")

def main():
    """Run all tests and report."""
    passed, failed = run_all_tests()
    report_metrics()
    report_metrics_detailed()
    report_limitations()
    
    print("\n" + "=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70 + "\n")
    
    if failed > 0:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
