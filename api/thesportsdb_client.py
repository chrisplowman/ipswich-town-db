"""
TheSportsDB API Client
Free API for sports data - https://www.thesportsdb.com/
"""
import requests
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from config.config import API_KEYS, API_ENDPOINTS, IPSWICH_TEAM_IDS, SCRAPING_CONFIG

logger = logging.getLogger(__name__)


class TheSportsDBClient:
    """Client for TheSportsDB API"""
    
    def __init__(self):
        self.api_key = API_KEYS['thesportsdb']
        self.base_url = API_ENDPOINTS['thesportsdb']['base_url']
        self.team_id = IPSWICH_TEAM_IDS['thesportsdb']
        self.rate_limit_delay = SCRAPING_CONFIG['rate_limit_delay']
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': SCRAPING_CONFIG['user_agent']
        })
    
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict]:
        """Make API request with rate limiting"""
        url = f"{self.base_url}/{self.api_key}{endpoint}"
        
        try:
            time.sleep(self.rate_limit_delay)  # Rate limiting
            response = self.session.get(url, params=params, timeout=SCRAPING_CONFIG['timeout'])
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None
    
    def get_team_info(self) -> Optional[Dict]:
        """Get Ipswich Town team information"""
        endpoint = API_ENDPOINTS['thesportsdb']['search_team']
        data = self._make_request(endpoint, {'t': 'Ipswich Town'})
        
        if data and 'teams' in data and data['teams']:
            return data['teams'][0]
        return None
    
    def get_last_matches(self, count: int = 15) -> List[Dict]:
        """Get last N matches for Ipswich Town"""
        endpoint = API_ENDPOINTS['thesportsdb']['team_events']
        data = self._make_request(endpoint, {'id': self.team_id})
        
        if not data or 'results' not in data:
            return []
        
        matches = []
        for event in (data['results'] or [])[:count]:
            match = self._parse_event(event)
            if match:
                matches.append(match)
        
        return matches
    
    def get_next_matches(self, count: int = 15) -> List[Dict]:
        """Get next N matches for Ipswich Town"""
        endpoint = API_ENDPOINTS['thesportsdb']['team_next_events']
        data = self._make_request(endpoint, {'id': self.team_id})
        
        if not data or 'events' not in data:
            return []
        
        matches = []
        for event in (data['events'] or [])[:count]:
            match = self._parse_event(event)
            if match:
                matches.append(match)
        
        return matches
    
    def get_event_details(self, event_id: str) -> Optional[Dict]:
        """Get detailed information about a specific match"""
        endpoint = API_ENDPOINTS['thesportsdb']['event_details']
        data = self._make_request(endpoint, {'id': event_id})
        
        if data and 'events' in data and data['events']:
            return self._parse_event(data['events'][0], detailed=True)
        return None
    
    def get_team_players(self) -> List[Dict]:
        """Get all players for Ipswich Town"""
        endpoint = API_ENDPOINTS['thesportsdb']['team_players']
        data = self._make_request(endpoint, {'id': self.team_id})
        
        if not data or 'player' not in data:
            return []
        
        players = []
        for player_data in data['player'] or []:
            player = self._parse_player(player_data)
            if player:
                players.append(player)
        
        return players
    
    def _parse_event(self, event: Dict, detailed: bool = False) -> Optional[Dict]:
        """Parse match event data"""
        try:
            # Determine home/away
            is_home = event.get('strHomeTeam') == 'Ipswich Town'
            
            match_data = {
                'api_id': event.get('idEvent'),
                'match_date': event.get('dateEvent'),
                'kick_off_time': event.get('strTime'),
                'home_team': event.get('strHomeTeam'),
                'away_team': event.get('strAwayTeam'),
                'home_score': self._parse_score(event.get('intHomeScore')),
                'away_score': self._parse_score(event.get('intAwayScore')),
                'competition': event.get('strLeague'),
                'season': event.get('strSeason'),
                'venue': event.get('strVenue'),
                'round': event.get('intRound'),
                'status': self._determine_status(event),
            }
            
            if detailed:
                match_data.update({
                    'home_score_ht': self._parse_score(event.get('intHomeScoreHT')),
                    'away_score_ht': self._parse_score(event.get('intAwayScoreHT')),
                    'home_shots': self._parse_int(event.get('intHomeShots')),
                    'away_shots': self._parse_int(event.get('intAwayShots')),
                    'home_possession': self._parse_int(event.get('intHomePossession')),
                    'away_possession': self._parse_int(event.get('intAwayPossession')),
                    'home_yellow_cards': self._parse_int(event.get('intHomeYellowCards')),
                    'away_yellow_cards': self._parse_int(event.get('intAwayYellowCards')),
                    'home_red_cards': self._parse_int(event.get('intHomeRedCards')),
                    'away_red_cards': self._parse_int(event.get('intAwayRedCards')),
                    'referee': event.get('strReferee'),
                    'attendance': self._parse_int(event.get('intSpectators')),
                })
            
            return match_data
        except Exception as e:
            logger.error(f"Error parsing event: {e}")
            return None
    
    def _parse_player(self, player_data: Dict) -> Optional[Dict]:
        """Parse player data"""
        try:
            return {
                'api_id': player_data.get('idPlayer'),
                'player_name': player_data.get('strPlayer'),
                'position': player_data.get('strPosition'),
                'nationality': player_data.get('strNationality'),
                'date_of_birth': player_data.get('dateBorn'),
                'squad_number': self._parse_int(player_data.get('strNumber')),
                'height': player_data.get('strHeight'),
                'weight': player_data.get('strWeight'),
            }
        except Exception as e:
            logger.error(f"Error parsing player: {e}")
            return None
    
    @staticmethod
    def _parse_score(score: Any) -> Optional[int]:
        """Parse score value"""
        if score is None or score == '':
            return None
        try:
            return int(score)
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def _parse_int(value: Any) -> Optional[int]:
        """Parse integer value"""
        if value is None or value == '':
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def _determine_status(event: Dict) -> str:
        """Determine match status"""
        home_score = event.get('intHomeScore')
        away_score = event.get('intAwayScore')
        
        if home_score is not None and away_score is not None:
            return 'finished'
        
        # Check if match is in the past
        match_date_str = event.get('dateEvent')
        if match_date_str:
            try:
                match_date = datetime.strptime(match_date_str, '%Y-%m-%d').date()
                if match_date < datetime.now().date():
                    return 'finished'
            except ValueError:
                pass
        
        return 'scheduled'


# Example usage
if __name__ == "__main__":
    client = TheSportsDBClient()
    
    print("=== Team Info ===")
    team_info = client.get_team_info()
    if team_info:
        print(f"Team: {team_info.get('strTeam')}")
        print(f"Stadium: {team_info.get('strStadium')}")
        print(f"Founded: {team_info.get('intFormedYear')}")
    
    print("\n=== Last 5 Matches ===")
    last_matches = client.get_last_matches(5)
    for match in last_matches:
        print(f"{match['match_date']}: {match['home_team']} {match['home_score']}-{match['away_score']} {match['away_team']}")
    
    print("\n=== Next 5 Matches ===")
    next_matches = client.get_next_matches(5)
    for match in next_matches:
        print(f"{match['match_date']}: {match['home_team']} vs {match['away_team']}")
