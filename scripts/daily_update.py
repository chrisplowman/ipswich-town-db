"""
Daily Update Script
Run this daily to update match results and statistics
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from datetime import datetime, timedelta

from database.db_manager import DatabaseManager
from api.thesportsdb_client import TheSportsDBClient
from api.football_data_client import FootballDataClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DailyUpdater:
    """Handles daily updates of match data"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.thesportsdb = TheSportsDBClient()
        self.football_data = FootballDataClient()
    
    def run_daily_update(self):
        """Run all daily update tasks"""
        logger.info("Starting daily update")
        
        try:
            # Update recent match results
            self._update_recent_matches()
            
            # Update upcoming fixtures
            self._update_upcoming_matches()
            
            # Check for any postponements or cancellations
            self._check_match_status_changes()
            
            logger.info("Daily update completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Daily update failed: {e}")
            return False
    
    def _update_recent_matches(self):
        """Update results for recent matches"""
        logger.info("Updating recent matches...")
        
        # Get matches from last 7 days
        yesterday = (datetime.now() - timedelta(days=1)).date()
        week_ago = (datetime.now() - timedelta(days=7)).date()
        
        # Fetch recent matches from APIs
        try:
            # TheSportsDB
            recent_matches = self.thesportsdb.get_last_matches(10)
            logger.info(f"Found {len(recent_matches)} recent matches from TheSportsDB")
            
            for match_data in recent_matches:
                self._update_match_from_api(match_data, 'thesportsdb')
            
        except Exception as e:
            logger.error(f"Error updating from TheSportsDB: {e}")
        
        try:
            # Football-Data.org
            date_from = week_ago.strftime('%Y-%m-%d')
            date_to = yesterday.strftime('%Y-%m-%d')
            recent_matches = self.football_data.get_matches_by_date(date_from, date_to)
            logger.info(f"Found {len(recent_matches)} recent matches from Football-Data.org")
            
            for match_data in recent_matches:
                self._update_match_from_api(match_data, 'football_data')
                
        except Exception as e:
            logger.error(f"Error updating from Football-Data.org: {e}")
    
    def _update_upcoming_matches(self):
        """Update information about upcoming fixtures"""
        logger.info("Updating upcoming matches...")
        
        try:
            # TheSportsDB
            upcoming = self.thesportsdb.get_next_matches(15)
            logger.info(f"Found {len(upcoming)} upcoming matches")
            
            for match_data in upcoming:
                self._update_match_from_api(match_data, 'thesportsdb')
                
        except Exception as e:
            logger.error(f"Error fetching upcoming matches: {e}")
    
    def _check_match_status_changes(self):
        """Check for postponements or cancellations"""
        logger.info("Checking for match status changes...")
        
        # Get scheduled matches
        upcoming = self.db.get_upcoming_matches(30)
        
        for match in upcoming:
            # Check if match has been postponed/cancelled
            # This would require checking against API data
            pass
    
    def _update_match_from_api(self, match_data: dict, source: str):
        """Update a single match from API data"""
        try:
            # Find existing match by API ID or date/teams
            api_id = match_data.get('api_id')
            
            if not api_id:
                return
            
            # Check if match exists
            if source == 'thesportsdb':
                query = "SELECT id FROM matches WHERE api_id_thesportsdb = %s;"
            else:
                query = "SELECT id FROM matches WHERE api_id_football_data = %s;"
            
            result = self.db.execute_query(query, (api_id,))
            
            if result and len(result) > 0:
                match_id = result[0]['id']
                
                # Update match if it has a score
                home_score = match_data.get('home_score')
                away_score = match_data.get('away_score')
                
                if home_score is not None and away_score is not None:
                    self.db.update_match_score(
                        match_id,
                        home_score,
                        away_score,
                        match_data.get('status', 'finished')
                    )
                    logger.info(f"Updated match {match_id}: {home_score}-{away_score}")
                
                # Update statistics if available
                if match_data.get('home_possession'):
                    stats = self._extract_statistics(match_data)
                    self.db.add_match_statistics(match_id, stats)
            
        except Exception as e:
            logger.error(f"Error updating match: {e}")
    
    def _extract_statistics(self, match_data: dict) -> dict:
        """Extract statistics from match data"""
        # Determine which team is Ipswich
        is_home = match_data.get('home_team') == 'Ipswich Town'
        
        stats = {
            'ipswich_possession': match_data.get('home_possession') if is_home else match_data.get('away_possession'),
            'opposition_possession': match_data.get('away_possession') if is_home else match_data.get('home_possession'),
            'ipswich_shots': match_data.get('home_shots') if is_home else match_data.get('away_shots'),
            'opposition_shots': match_data.get('away_shots') if is_home else match_data.get('home_shots'),
        }
        
        return stats


def main():
    """Main entry point"""
    print("=" * 60)
    print(f"Daily Update - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()
    
    updater = DailyUpdater()
    success = updater.run_daily_update()
    
    if success:
        print("\n" + "=" * 60)
        print("SUCCESS: Daily update completed")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("ERROR: Daily update failed")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
