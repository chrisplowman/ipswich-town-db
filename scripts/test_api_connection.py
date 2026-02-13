"""
Test API connections and database setup
Run this to verify everything is configured correctly
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from api.thesportsdb_client import TheSportsDBClient
from api.football_data_client import FootballDataClient
from config.config import API_KEYS


def test_database():
    """Test database connection"""
    print("\n" + "=" * 60)
    print("Testing Database Connection")
    print("=" * 60)
    
    try:
        db = DatabaseManager()
        print("✓ Database connection successful")
        
        # Try a simple query
        seasons = db.execute_query("SELECT COUNT(*) as count FROM seasons;")
        print(f"✓ Found {seasons[0]['count']} season(s) in database")
        
        teams = db.execute_query("SELECT COUNT(*) as count FROM teams;")
        print(f"✓ Found {teams[0]['count']} team(s) in database")
        
        matches = db.execute_query("SELECT COUNT(*) as count FROM matches;")
        print(f"✓ Found {matches[0]['count']} match(es) in database")
        
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False


def test_thesportsdb():
    """Test TheSportsDB API"""
    print("\n" + "=" * 60)
    print("Testing TheSportsDB API")
    print("=" * 60)
    
    try:
        client = TheSportsDBClient()
        
        # Test team info
        print("Fetching team information...")
        team_info = client.get_team_info()
        
        if team_info:
            print(f"✓ Team: {team_info.get('strTeam')}")
            print(f"✓ Stadium: {team_info.get('strStadium')}")
            print(f"✓ Founded: {team_info.get('intFormedYear')}")
        else:
            print("✗ Failed to fetch team information")
            return False
        
        # Test recent matches
        print("\nFetching recent matches...")
        matches = client.get_last_matches(3)
        
        if matches:
            print(f"✓ Found {len(matches)} recent matches")
            for match in matches[:2]:
                print(f"  - {match['match_date']}: {match['home_team']} vs {match['away_team']}")
        else:
            print("✗ No recent matches found")
        
        return True
    except Exception as e:
        print(f"✗ TheSportsDB API test failed: {e}")
        return False


def test_football_data():
    """Test Football-Data.org API"""
    print("\n" + "=" * 60)
    print("Testing Football-Data.org API")
    print("=" * 60)
    
    if not API_KEYS['football_data']:
        print("⚠ No API key configured")
        print("  Register at: https://www.football-data.org/")
        print("  Then add key to config/config.py")
        return None
    
    try:
        client = FootballDataClient()
        
        # Test team info
        print("Fetching team information...")
        team_info = client.get_team_info()
        
        if team_info:
            print(f"✓ Team: {team_info.get('team_name')}")
            print(f"✓ Stadium: {team_info.get('stadium')}")
            print(f"✓ Founded: {team_info.get('founded')}")
        else:
            print("✗ Failed to fetch team information")
            return False
        
        # Test recent matches
        print("\nFetching recent matches...")
        matches = client.get_team_matches('FINISHED', limit=3)
        
        if matches:
            print(f"✓ Found {len(matches)} recent matches")
            for match in matches[:2]:
                score = f"{match['home_score']}-{match['away_score']}" if match['home_score'] is not None else "vs"
                print(f"  - {match['match_date']}: {match['home_team']} {score} {match['away_team']}")
        else:
            print("⚠ No recent matches found")
        
        return True
    except Exception as e:
        print(f"✗ Football-Data.org API test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Ipswich Town FC Database - Connection Tests")
    print("=" * 60)
    
    results = {
        'database': test_database(),
        'thesportsdb': test_thesportsdb(),
        'football_data': test_football_data(),
    }
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test, result in results.items():
        status = "✓ PASSED" if result else ("⚠ SKIPPED" if result is None else "✗ FAILED")
        print(f"{test:20s}: {status}")
    
    # Overall result
    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    skipped = sum(1 for r in results.values() if r is None)
    
    print("\n" + "=" * 60)
    if failed == 0:
        print("✓ All tests passed!")
        if skipped > 0:
            print(f"  ({skipped} test(s) skipped - configure API keys to enable)")
        print("\nYou're ready to start using the database!")
        print("Next step: Run scripts/fetch_current_season.py")
    else:
        print(f"✗ {failed} test(s) failed")
        print("\nPlease fix the issues above before proceeding.")
        sys.exit(1)
    print("=" * 60)


if __name__ == "__main__":
    main()
