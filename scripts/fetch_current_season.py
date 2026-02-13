"""
Fetch current season matches from APIs
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from datetime import datetime

from database.db_manager import DatabaseManager
from api.thesportsdb_client import TheSportsDBClient
from api.football_data_client import FootballDataClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CurrentSeasonFetcher:
    """Fetch and store current season data"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.thesportsdb = TheSportsDBClient()
        self.football_data = FootballDataClient()
        self.current_season = self._get_current_season()
    
    def _get_current_season(self) -> str:
        """Determine current season based on date"""
        now = datetime.now()
        year = now.year
        month = now.month
        
        # Football season typically runs August-May
        if month >= 8:
            return f"{year}/{str(year + 1)[2:]}"
        else:
            return f"{year - 1}/{str(year)[2:]}"
    
    def fetch_all(self):
        """Fetch all current season data"""
        logger.info(f"Fetching data for {self.current_season} season")
        
        # Ensure season exists in database
        self._ensure_season_exists()
        
        # Fetch from both APIs
        logger.info("Fetching from TheSportsDB...")
        self._fetch_from_thesportsdb()
        
        logger.info("Fetching from Football-Data.org...")
        self._fetch_from_football_data()
        
        logger.info("Data fetch complete!")
    
    def _ensure_season_exists(self):
        """Ensure current season is in database"""
        season_id = self.db.get_season_id(self.current_season)
        
        if not season_id:
            # Calculate season dates
            start_year = int(self.current_season.split('/')[0])
            start_date = f"{start_year}-08-01"
            end_date = f"{start_year + 1}-05-31"
            
            season_id = self.db.add_season(self.current_season, start_date, end_date)
            logger.info(f"Created season: {self.current_season}")
        
        return season_id
    
    def _fetch_from_thesportsdb(self):
        """Fetch data from TheSportsDB"""
        try:
            # Get last matches
            last_matches = self.thesportsdb.get_last_matches(20)
            logger.info(f"Found {len(last_matches)} recent matches")
            
            for match_data in last_matches:
                self._store_match(match_data, 'thesportsdb')
            
            # Get upcoming matches
            next_matches = self.thesportsdb.get_next_matches(20)
            logger.info(f"Found {len(next_matches)} upcoming matches")
            
            for match_data in next_matches:
                self._store_match(match_data, 'thesportsdb')
            
            # Get squad
            players = self.thesportsdb.get_team_players()
            logger.info(f"Found {len(players)} players")
            
            for player_data in players:
                self._store_player(player_data, 'thesportsdb')
                
        except Exception as e:
            logger.error(f"Error fetching from TheSportsDB: {e}")
    
    def _fetch_from_football_data(self):
        """Fetch data from Football-Data.org"""
        try:
            # Get all matches (finished and scheduled)
            finished_matches = self.football_data.get_team_matches('FINISHED', limit=50)
            logger.info(f"Found {len(finished_matches)} finished matches")
            
            for match_data in finished_matches:
                self._store_match(match_data, 'football_data')
            
            scheduled_matches = self.football_data.get_team_matches('SCHEDULED', limit=50)
            logger.info(f"Found {len(scheduled_matches)} scheduled matches")
            
            for match_data in scheduled_matches:
                self._store_match(match_data, 'football_data')
            
            # Get squad
            squad = self.football_data.get_team_squad()
            logger.info(f"Found {len(squad)} players")
            
            for player_data in squad:
                self._store_player(player_data, 'football_data')
                
        except Exception as e:
            logger.error(f"Error fetching from Football-Data.org: {e}")
    
    def _store_match(self, match_data: dict, source: str):
        """Store match in database"""
        try:
            # Get or create season
            season_name = match_data.get('season', self.current_season)
            season_id = self.db.get_season_id(season_name)
            
            if not season_id:
                # Create season on the fly
                year = int(season_name.split('/')[0])
                season_id = self.db.add_season(
                    season_name,
                    f"{year}-08-01",
                    f"{year + 1}-05-31"
                )
            
            # Get or create competition
            competition_name = match_data.get('competition', 'Unknown')
            competition_id = self.db.get_competition_id(competition_name)
            
            if not competition_id:
                # Competition doesn't exist - skip for now or create basic entry
                logger.warning(f"Competition not found: {competition_name}")
                return
            
            # Get or create teams
            home_team = match_data.get('home_team')
            away_team = match_data.get('away_team')
            
            if not home_team or not away_team:
                logger.warning("Missing team information")
                return
            
            home_team_id = self.db.get_team_id(home_team)
            if not home_team_id:
                home_team_id = self.db.add_team(home_team)
            
            away_team_id = self.db.get_team_id(away_team)
            if not away_team_id:
                away_team_id = self.db.add_team(away_team)
            
            # Prepare match data for database
            db_match_data = {
                'season_id': season_id,
                'competition_id': competition_id,
                'match_date': match_data.get('match_date'),
                'kick_off_time': match_data.get('kick_off_time'),
                'home_team_id': home_team_id,
                'away_team_id': away_team_id,
                'home_score': match_data.get('home_score'),
                'away_score': match_data.get('away_score'),
                'half_time_home_score': match_data.get('home_score_ht'),
                'half_time_away_score': match_data.get('away_score_ht'),
                'venue': match_data.get('venue'),
                'attendance': match_data.get('attendance'),
                'referee': match_data.get('referee'),
                'match_status': match_data.get('status', 'scheduled'),
                'match_round': str(match_data.get('round')) if match_data.get('round') else None,
            }
            
            # Add API-specific ID
            if source == 'thesportsdb':
                db_match_data['api_id_thesportsdb'] = match_data.get('api_id')
            elif source == 'football_data':
                db_match_data['api_id_football_data'] = match_data.get('api_id')
            
            # Store match
            match_id = self.db.add_match(db_match_data)
            
            # Store statistics if available
            if match_data.get('home_possession'):
                stats = {
                    'ipswich_possession': None,
                    'opposition_possession': None,
                    'ipswich_shots': None,
                    'opposition_shots': None,
                }
                
                # Determine which team is Ipswich
                is_home = home_team == 'Ipswich Town'
                
                if is_home:
                    stats['ipswich_possession'] = match_data.get('home_possession')
                    stats['opposition_possession'] = match_data.get('away_possession')
                    stats['ipswich_shots'] = match_data.get('home_shots')
                    stats['opposition_shots'] = match_data.get('away_shots')
                else:
                    stats['ipswich_possession'] = match_data.get('away_possession')
                    stats['opposition_possession'] = match_data.get('home_possession')
                    stats['ipswich_shots'] = match_data.get('away_shots')
                    stats['opposition_shots'] = match_data.get('home_shots')
                
                self.db.add_match_statistics(match_id, stats)
            
        except Exception as e:
            logger.error(f"Error storing match: {e}")
    
    def _store_player(self, player_data: dict, source: str):
        """Store player in database"""
        try:
            # Add API-specific ID
            if source == 'thesportsdb':
                player_data['api_id_thesportsdb'] = player_data.get('api_id')
            elif source == 'football_data':
                player_data['api_id_football_data'] = player_data.get('api_id')
            
            self.db.add_player(player_data)
            
        except Exception as e:
            logger.error(f"Error storing player: {e}")


def main():
    print("=" * 60)
    print("Fetching Current Season Data")
    print("=" * 60)
    print()
    
    try:
        fetcher = CurrentSeasonFetcher()
        fetcher.fetch_all()
        
        print("\n" + "=" * 60)
        print("SUCCESS: Data fetched and stored!")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print("\n" + "=" * 60)
        print("ERROR: Data fetch failed")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
