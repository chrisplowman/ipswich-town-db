"""
Configuration settings for Ipswich Town FC Database
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Database Configuration
DATABASE_CONFIG = {
    'host': os.getenv('DB_HOST', 'dpg-d67jtcrnv86c739qhdn0-a'),
    'port': os.getenv('DB_PORT', 5432),
    'database': os.getenv('DB_NAME', 'ipswich_town_db'),
    'user': os.getenv('DB_USER', 'ipswich_town_db_user'),
    'password': os.getenv('DB_PASSWORD', 'lRCz9kZO4uMCS8p3NTzJR4PVEarISwtB')
}

# API Keys
API_KEYS = {
    'football_data': os.getenv('FOOTBALL_DATA_API_KEY', ''),  # Register at https://www.football-data.org/
    'thesportsdb': os.getenv('THESPORTSDB_API_KEY', '3'),  # Free testing key, donate for full access
}

# API Endpoints
API_ENDPOINTS = {
    'thesportsdb': {
        'base_url': 'https://www.thesportsdb.com/api/v1/json',
        'search_team': '/searchteams.php',
        'team_events': '/eventslast.php',
        'team_next_events': '/eventsnext.php',
        'league_table': '/lookuptable.php',
        'event_details': '/lookupevent.php',
        'team_players': '/lookup_all_players.php',
    },
    'football_data': {
        'base_url': 'https://api.football-data.org/v4',
        'team': '/teams',
        'matches': '/matches',
        'competitions': '/competitions',
    }
}

# Team IDs for APIs
IPSWICH_TEAM_IDS = {
    'thesportsdb': '133884',  # TheSportsDB team ID for Ipswich Town
    'football_data': '349',    # Football-Data.org team ID
}

# Competition IDs
COMPETITION_IDS = {
    'championship': {
        'thesportsdb': '4330',
        'football_data': 'ELC',  # Championship
    },
    'premier_league': {
        'thesportsdb': '4328',
        'football_data': 'PL',
    },
    'fa_cup': {
        'thesportsdb': '4329',
        'football_data': 'FAC',
    },
    'league_cup': {
        'thesportsdb': '4331',
        'football_data': 'LC',
    }
}

# Web Scraping Configuration
SCRAPING_CONFIG = {
    'user_agent': 'IpswichTownFC-Database/1.0 (Educational Project)',
    'rate_limit_delay': 2,  # Seconds between requests
    'timeout': 30,  # Request timeout in seconds
    'max_retries': 3,
    'retry_delay': 5,
}

# Scraper URLs
SCRAPER_URLS = {
    '11v11': 'https://www.11v11.com/teams/ipswich-town/',
    'transfermarkt': 'https://www.transfermarkt.com/ipswich-town/startseite/verein/677',
    'soccerway': 'https://uk.soccerway.com/teams/england/ipswich-town-fc/679/',
}

# Logging Configuration
LOGGING_CONFIG = {
    'log_dir': BASE_DIR / 'logs',
    'log_file': 'ipswich_db.log',
    'level': 'INFO',  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'max_bytes': 10485760,  # 10MB
    'backup_count': 5,
}

# Automation Schedule
SCHEDULE_CONFIG = {
    'daily_update_time': '01:00',  # 1 AM daily
    'match_day_update_interval': 3600,  # Every hour on match days (seconds)
    'weekly_validation_day': 'Sunday',
    'weekly_validation_time': '03:00',  # 3 AM on Sundays
}

# Data Export Configuration
EXPORT_CONFIG = {
    'output_dir': BASE_DIR / 'exports',
    'backup_dir': BASE_DIR / 'backups',
}

# Create necessary directories
for directory in [
    LOGGING_CONFIG['log_dir'],
    EXPORT_CONFIG['output_dir'],
    EXPORT_CONFIG['backup_dir'],
    BASE_DIR / 'data',
]:
    directory.mkdir(exist_ok=True)

# Validation rules
VALIDATION_CONFIG = {
    'max_score': 20,  # Flag matches with scores over this
    'max_attendance': 50000,  # Flag attendance over this
    'min_match_duration': 90,  # Minimum match duration in minutes
    'max_cards_per_match': 10,  # Flag matches with more cards
}
