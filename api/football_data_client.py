"""
Football-Data.org API Client
Register for free API key at https://www.football-data.org/
"""
import requests
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from config.config import API_KEYS, API_ENDPOINTS, IPSWICH_TEAM_IDS, SCRAPING_CONFIG

logger = logging.getLogger(__name__)


class FootballDataClient:
    """Client for Football-Data.org API"""
    
    def __init__(self):
        self.api_key = API_KEYS['football_data']
        self.base_url = API_ENDPOINTS['football_data']['base_url']
        self.team_id = IPSWICH_TEAM_IDS['football_data']
        self.session = requests.Session()
        self.session.headers.update({
            'X-Auth-Token': self.api_key,
            'User-Agent': SCRAPING_CONFIG['user_agent']
        })
        
        # Rate limiting: Free tier allows 10 requests per minute
        self.rate_limit_delay = 6  # 6 seconds = 10 requests per minute
        self.last_request_time = 0
    
    def _rate_limit(self):
        """Enforce rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make API request with rate limiting"""
        if not self.api_key:
            logger.warning("Football-Data.org API key not configured")
            return None
        
        self._rate_limit()
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.get(url, params=params, timeout=SCRAPING_CONFIG['timeout'])
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                logger.warning("Rate limit exceeded, waiting...")
                time.sleep(60)  # Wait 1 minute if rate limited
                return self._make_request(endpoint, params)
            logger.error(f"HTTP error: {e}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None
    
    def get_team_info(self) -> Optional[Dict]:
        """Get Ipswich Town team information"""
        endpoint = f"/teams/{self.team_id}"
        data = self._make_request(endpoint)
        
        if data:
            return {
                'api_id': str(data.get('id')),
                'team_name': data.get('name'),
                'short_name': data.get('shortName'),
                'tla': data.get('tla'),  # Three-letter abbreviation
                'stadium': data.get('venue'),
                'founded': data.get('founded'),
                'website': data.get('website'),
                'colors': data.get('clubColors'),
            }
        return None
    
    def get_team_matches(self, status: str = 'FINISHED', limit: int = 100) -> List[Dict]:
        """
        Get matches for Ipswich Town
        status: SCHEDULED, LIVE, IN_PLAY, PAUSED, FINISHED, POSTPONED, SUSPENDED, CANCELLED
        """
        endpoint = f"/teams/{self.team_id}/matches"
        params = {'status': status, 'limit': limit}
        data = self._make_request(endpoint, params)
        
        if not data or 'matches' not in data:
            return []
        
        matches = []
        for match_data in data['matches']:
            match = self._parse_match(match_data)
            if match:
                matches.append(match)
        
        return matches
    
    def get_matches_by_date(self, date_from: str, date_to: str) -> List[Dict]:
        """
        Get Ipswich Town matches between two dates
        Dates in format: YYYY-MM-DD
        """
        endpoint = f"/teams/{self.team_id}/matches"
        params = {
            'dateFrom': date_from,
            'dateTo': date_to
        }
        data = self._make_request(endpoint, params)
        
        if not data or 'matches' not in data:
            return []
        
        matches = []
        for match_data in data['matches']:
            match = self._parse_match(match_data)
            if match:
                matches.append(match)
        
        return matches
    
    def get_match_details(self, match_id: str) -> Optional[Dict]:
        """Get detailed information about a specific match"""
        endpoint = f"/matches/{match_id}"
        data = self._make_request(endpoint)
        
        if data:
            return self._parse_match(data, detailed=True)
        return None
    
    def get_team_squad(self) -> List[Dict]:
        """Get current Ipswich Town squad"""
        endpoint = f"/teams/{self.team_id}"
        data = self._make_request(endpoint)
        
        if not data or 'squad' not in data:
            return []
        
        players = []
        for player_data in data['squad']:
            player = self._parse_player(player_data)
            if player:
                players.append(player)
        
        return players
    
    def get_competition_standings(self, competition_code: str) -> Optional[List[Dict]]:
        """
        Get league table for a competition
        competition_code: 'ELC' (Championship), 'PL' (Premier League), etc.
        """
        endpoint = f"/competitions/{competition_code}/standings"
        data = self._make_request(endpoint)
        
        if not data or 'standings' not in data:
            return None
        
        # Usually returns multiple standing types (TOTAL, HOME, AWAY)
        # We'll return the TOTAL standings
        for standing in data['standings']:
            if standing['type'] == 'TOTAL':
                return standing['table']
        
        return None
    
    def _parse_match(self, match_data: Dict, detailed: bool = False) -> Optional[Dict]:
        """Parse match data"""
        try:
            match = {
                'api_id': str(match_data.get('id')),
                'match_date': match_data.get('utcDate', '').split('T')[0] if match_data.get('utcDate') else None,
                'kick_off_time': match_data.get('utcDate', '').split('T')[1].split('Z')[0] if match_data.get('utcDate') else None,
                'home_team': match_data['homeTeam']['name'],
                'away_team': match_data['awayTeam']['name'],
                'home_team_id': str(match_data['homeTeam']['id']),
                'away_team_id': str(match_data['awayTeam']['id']),
                'competition': match_data['competition']['name'],
                'season': self._extract_season(match_data),
                'status': self._map_status(match_data.get('status')),
                'round': match_data.get('matchday'),
                'venue': match_data.get('venue'),
            }
            
            # Score data
            score = match_data.get('score', {})
            if score:
                match.update({
                    'home_score': score.get('fullTime', {}).get('home'),
                    'away_score': score.get('fullTime', {}).get('away'),
                    'home_score_ht': score.get('halfTime', {}).get('home'),
                    'away_score_ht': score.get('halfTime', {}).get('away'),
                })
            
            if detailed:
                # Referee info
                referees = match_data.get('referees', [])
                if referees:
                    match['referee'] = referees[0].get('name')
                
                # Additional match details if available
                match['attendance'] = match_data.get('attendance')
            
            return match
        except Exception as e:
            logger.error(f"Error parsing match: {e}")
            return None
    
    def _parse_player(self, player_data: Dict) -> Optional[Dict]:
        """Parse player data"""
        try:
            return {
                'api_id': str(player_data.get('id')),
                'player_name': player_data.get('name'),
                'position': player_data.get('position'),
                'nationality': player_data.get('nationality'),
                'date_of_birth': player_data.get('dateOfBirth'),
                'squad_number': player_data.get('shirtNumber'),
            }
        except Exception as e:
            logger.error(f"Error parsing player: {e}")
            return None
    
    @staticmethod
    def _extract_season(match_data: Dict) -> str:
        """Extract season from match data"""
        season_data = match_data.get('season', {})
        start_date = season_data.get('startDate', '')
        end_date = season_data.get('endDate', '')
        
        if start_date and end_date:
            start_year = start_date[:4]
            end_year = end_date[:4]
            if start_year != end_year:
                return f"{start_year}/{end_year[2:]}"  # e.g., "2023/24"
            return start_year
        
        return ''
    
    @staticmethod
    def _map_status(status: str) -> str:
        """Map Football-Data.org status to our status"""
        status_map = {
            'SCHEDULED': 'scheduled',
            'TIMED': 'scheduled',
            'IN_PLAY': 'live',
            'PAUSED': 'live',
            'FINISHED': 'finished',
            'POSTPONED': 'postponed',
            'CANCELLED': 'cancelled',
            'SUSPENDED': 'postponed',
            'AWARDED': 'finished',
        }
        return status_map.get(status, 'scheduled')


# Example usage
if __name__ == "__main__":
    client = FootballDataClient()
    
    if not client.api_key:
        print("Please set FOOTBALL_DATA_API_KEY in config.py")
        print("Register at: https://www.football-data.org/")
    else:
        print("=== Team Info ===")
        team_info = client.get_team_info()
        if team_info:
            print(f"Team: {team_info.get('team_name')}")
            print(f"Stadium: {team_info.get('stadium')}")
            print(f"Founded: {team_info.get('founded')}")
        
        print("\n=== Recent Finished Matches ===")
        matches = client.get_team_matches('FINISHED', limit=5)
        for match in matches:
            print(f"{match['match_date']}: {match['home_team']} {match['home_score']}-{match['away_score']} {match['away_team']}")
        
        print("\n=== Upcoming Matches ===")
        upcoming = client.get_team_matches('SCHEDULED', limit=5)
        for match in upcoming:
            print(f"{match['match_date']}: {match['home_team']} vs {match['away_team']}")
