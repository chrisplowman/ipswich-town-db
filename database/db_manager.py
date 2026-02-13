"""
Database Manager for Ipswich Town FC Database
Handles all database operations
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import List, Dict, Optional, Any
import logging
from datetime import datetime

from config.config import DATABASE_CONFIG, LOGGING_CONFIG

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOGGING_CONFIG['level']),
    format=LOGGING_CONFIG['format'],
    handlers=[
        logging.FileHandler(LOGGING_CONFIG['log_dir'] / LOGGING_CONFIG['log_file']),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self):
        self.config = DATABASE_CONFIG
        self._test_connection()
    
    def _test_connection(self):
        """Test database connection on initialization"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1;")
            logger.info("Database connection successful")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = psycopg2.connect(**self.config)
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database operation failed: {e}")
            raise
        finally:
            conn.close()
    
    def execute_query(self, query: str, params: tuple = None, fetch: bool = True) -> Optional[List[Dict]]:
        """Execute a SQL query and optionally fetch results"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                if fetch:
                    return [dict(row) for row in cur.fetchall()]
                return None
    
    # Season Operations
    def add_season(self, season_name: str, start_date: str, end_date: str) -> int:
        """Add a new season"""
        query = """
            INSERT INTO seasons (season_name, start_date, end_date)
            VALUES (%s, %s, %s)
            ON CONFLICT (season_name) DO UPDATE SET
                start_date = EXCLUDED.start_date,
                end_date = EXCLUDED.end_date
            RETURNING id;
        """
        result = self.execute_query(query, (season_name, start_date, end_date))
        logger.info(f"Added/updated season: {season_name}")
        return result[0]['id']
    
    def get_season_id(self, season_name: str) -> Optional[int]:
        """Get season ID by name"""
        query = "SELECT id FROM seasons WHERE season_name = %s;"
        result = self.execute_query(query, (season_name,))
        return result[0]['id'] if result else None
    
    # Team Operations
    def add_team(self, team_name: str, **kwargs) -> int:
        """Add or update a team"""
        fields = ['team_name']
        values = [team_name]
        
        optional_fields = {
            'short_name': kwargs.get('short_name'),
            'stadium': kwargs.get('stadium'),
            'city': kwargs.get('city'),
            'country': kwargs.get('country', 'England'),
            'founded_year': kwargs.get('founded_year'),
            'api_id_thesportsdb': kwargs.get('api_id_thesportsdb'),
            'api_id_football_data': kwargs.get('api_id_football_data'),
        }
        
        for field, value in optional_fields.items():
            if value is not None:
                fields.append(field)
                values.append(value)
        
        placeholders = ', '.join(['%s'] * len(fields))
        fields_str = ', '.join(fields)
        
        query = f"""
            INSERT INTO teams ({fields_str})
            VALUES ({placeholders})
            ON CONFLICT (team_name) DO UPDATE SET
                {', '.join([f"{f} = EXCLUDED.{f}" for f in fields[1:]])}
            RETURNING id;
        """ if len(fields) > 1 else f"""
            INSERT INTO teams ({fields_str})
            VALUES ({placeholders})
            ON CONFLICT (team_name) DO NOTHING
            RETURNING id;
        """
        
        result = self.execute_query(query, tuple(values))
        if result:
            logger.info(f"Added/updated team: {team_name}")
            return result[0]['id']
        else:
            # Team already exists, get its ID
            return self.get_team_id(team_name)
    
    def get_team_id(self, team_name: str) -> Optional[int]:
        """Get team ID by name"""
        query = "SELECT id FROM teams WHERE team_name = %s;"
        result = self.execute_query(query, (team_name,))
        return result[0]['id'] if result else None
    
    def get_competition_id(self, competition_name: str) -> Optional[int]:
        """Get competition ID by name"""
        query = "SELECT id FROM competitions WHERE name = %s;"
        result = self.execute_query(query, (competition_name,))
        return result[0]['id'] if result else None
    
    # Match Operations
    def add_match(self, match_data: Dict[str, Any]) -> int:
        """Add a new match"""
        query = """
            INSERT INTO matches (
                season_id, competition_id, match_date, kick_off_time,
                home_team_id, away_team_id, home_score, away_score,
                half_time_home_score, half_time_away_score,
                venue, attendance, referee, match_status, match_round,
                api_id_thesportsdb, api_id_football_data, notes
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (id) DO UPDATE SET
                home_score = EXCLUDED.home_score,
                away_score = EXCLUDED.away_score,
                match_status = EXCLUDED.match_status,
                attendance = EXCLUDED.attendance,
                updated_at = CURRENT_TIMESTAMP
            RETURNING id;
        """
        
        values = (
            match_data.get('season_id'),
            match_data.get('competition_id'),
            match_data.get('match_date'),
            match_data.get('kick_off_time'),
            match_data.get('home_team_id'),
            match_data.get('away_team_id'),
            match_data.get('home_score'),
            match_data.get('away_score'),
            match_data.get('half_time_home_score'),
            match_data.get('half_time_away_score'),
            match_data.get('venue'),
            match_data.get('attendance'),
            match_data.get('referee'),
            match_data.get('match_status', 'scheduled'),
            match_data.get('match_round'),
            match_data.get('api_id_thesportsdb'),
            match_data.get('api_id_football_data'),
            match_data.get('notes'),
        )
        
        result = self.execute_query(query, values)
        match_id = result[0]['id']
        logger.info(f"Added match ID: {match_id}")
        return match_id
    
    def update_match_score(self, match_id: int, home_score: int, away_score: int, 
                          status: str = 'finished') -> None:
        """Update match score and status"""
        query = """
            UPDATE matches
            SET home_score = %s, away_score = %s, match_status = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s;
        """
        self.execute_query(query, (home_score, away_score, status, match_id), fetch=False)
        logger.info(f"Updated match {match_id}: {home_score}-{away_score}")
    
    def get_season_matches(self, season_name: str) -> List[Dict]:
        """Get all Ipswich Town matches for a season"""
        query = """
            SELECT * FROM ipswich_matches
            WHERE season_name = %s
            ORDER BY match_date;
        """
        return self.execute_query(query, (season_name,))
    
    def get_upcoming_matches(self, days: int = 14) -> List[Dict]:
        """Get upcoming matches in the next N days"""
        query = """
            SELECT * FROM ipswich_matches
            WHERE match_date BETWEEN CURRENT_DATE AND CURRENT_DATE + %s
              AND match_status = 'scheduled'
            ORDER BY match_date;
        """
        return self.execute_query(query, (f'{days} days',))
    
    # Player Operations
    def add_player(self, player_data: Dict[str, Any]) -> int:
        """Add or update a player"""
        query = """
            INSERT INTO players (
                player_name, date_of_birth, nationality, position,
                squad_number, joined_date, left_date,
                api_id_thesportsdb, api_id_football_data
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                squad_number = EXCLUDED.squad_number,
                position = EXCLUDED.position,
                updated_at = CURRENT_TIMESTAMP
            RETURNING id;
        """
        
        values = (
            player_data.get('player_name'),
            player_data.get('date_of_birth'),
            player_data.get('nationality'),
            player_data.get('position'),
            player_data.get('squad_number'),
            player_data.get('joined_date'),
            player_data.get('left_date'),
            player_data.get('api_id_thesportsdb'),
            player_data.get('api_id_football_data'),
        )
        
        result = self.execute_query(query, values)
        player_id = result[0]['id']
        logger.info(f"Added player: {player_data.get('player_name')}")
        return player_id
    
    def get_player_id(self, player_name: str) -> Optional[int]:
        """Get player ID by name"""
        query = "SELECT id FROM players WHERE player_name = %s;"
        result = self.execute_query(query, (player_name,))
        return result[0]['id'] if result else None
    
    # Statistics Operations
    def add_match_statistics(self, match_id: int, stats: Dict[str, Any]) -> None:
        """Add match statistics"""
        query = """
            INSERT INTO match_statistics (
                match_id, ipswich_possession, opposition_possession,
                ipswich_shots, opposition_shots,
                ipswich_shots_on_target, opposition_shots_on_target,
                ipswich_corners, opposition_corners,
                ipswich_fouls, opposition_fouls,
                ipswich_offsides, opposition_offsides,
                ipswich_passes, opposition_passes,
                ipswich_pass_accuracy, opposition_pass_accuracy
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (match_id) DO UPDATE SET
                ipswich_possession = EXCLUDED.ipswich_possession,
                opposition_possession = EXCLUDED.opposition_possession,
                ipswich_shots = EXCLUDED.ipswich_shots,
                opposition_shots = EXCLUDED.opposition_shots,
                updated_at = CURRENT_TIMESTAMP;
        """
        
        values = (
            match_id,
            stats.get('ipswich_possession'),
            stats.get('opposition_possession'),
            stats.get('ipswich_shots'),
            stats.get('opposition_shots'),
            stats.get('ipswich_shots_on_target'),
            stats.get('opposition_shots_on_target'),
            stats.get('ipswich_corners'),
            stats.get('opposition_corners'),
            stats.get('ipswich_fouls'),
            stats.get('opposition_fouls'),
            stats.get('ipswich_offsides'),
            stats.get('opposition_offsides'),
            stats.get('ipswich_passes'),
            stats.get('opposition_passes'),
            stats.get('ipswich_pass_accuracy'),
            stats.get('opposition_pass_accuracy'),
        )
        
        self.execute_query(query, values, fetch=False)
        logger.info(f"Added statistics for match {match_id}")
    
    def add_goal(self, goal_data: Dict[str, Any]) -> int:
        """Add a goal"""
        query = """
            INSERT INTO goals (
                match_id, player_id, team_id, minute, goal_type,
                is_penalty, is_own_goal, assist_player_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """
        
        values = (
            goal_data.get('match_id'),
            goal_data.get('player_id'),
            goal_data.get('team_id'),
            goal_data.get('minute'),
            goal_data.get('goal_type', 'Open Play'),
            goal_data.get('is_penalty', False),
            goal_data.get('is_own_goal', False),
            goal_data.get('assist_player_id'),
        )
        
        result = self.execute_query(query, values)
        return result[0]['id']
    
    # Query Operations
    def get_top_scorers(self, season_name: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Get top scorers, optionally for a specific season"""
        if season_name:
            query = """
                SELECT p.player_name, COUNT(g.id) as goals
                FROM goals g
                JOIN players p ON g.player_id = p.id
                JOIN matches m ON g.match_id = m.id
                JOIN seasons s ON m.season_id = s.id
                JOIN teams t ON g.team_id = t.id
                WHERE t.team_name = 'Ipswich Town'
                  AND g.is_own_goal = FALSE
                  AND s.season_name = %s
                GROUP BY p.player_name
                ORDER BY goals DESC
                LIMIT %s;
            """
            return self.execute_query(query, (season_name, limit))
        else:
            query = """
                SELECT * FROM top_scorers
                LIMIT %s;
            """
            return self.execute_query(query, (limit,))
    
    def get_season_statistics(self, season_name: str) -> List[Dict]:
        """Get statistics for a season"""
        query = """
            SELECT * FROM season_statistics
            WHERE season_name = %s;
        """
        return self.execute_query(query, (season_name,))
    
    def get_head_to_head(self, opponent: str) -> Dict[str, Any]:
        """Get head-to-head record against an opponent"""
        query = """
            SELECT 
                COUNT(*) as total_matches,
                COUNT(CASE WHEN result = 'Win' THEN 1 END) as wins,
                COUNT(CASE WHEN result = 'Draw' THEN 1 END) as draws,
                COUNT(CASE WHEN result = 'Loss' THEN 1 END) as losses,
                SUM(ipswich_score) as goals_for,
                SUM(opponent_score) as goals_against
            FROM ipswich_matches
            WHERE opponent = %s AND match_status = 'finished';
        """
        result = self.execute_query(query, (opponent,))
        return result[0] if result else {}
