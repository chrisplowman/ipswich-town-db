# Ipswich Town FC Database Project

A comprehensive database system for collecting, storing, and automatically updating Ipswich Town FC match data and statistics.

## Table of Contents
1. [Project Overview](#project-overview)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Database Setup](#database-setup)
5. [Data Collection](#data-collection)
6. [API Integration](#api-integration)
7. [Automation](#automation)
8. [Usage](#usage)
9. [Future Enhancements](#future-enhancements)

## Project Overview

This project uses:
- **PostgreSQL** - Database management
- **Python 3.8+** - Data collection and processing
- **Free APIs** - TheSportsDB, Football-Data.org
- **Web Scraping** - Historical data from public sources
- **Cron/Task Scheduler** - Automated updates

## Prerequisites

### Required Software
- Python 3.8 or higher
- PostgreSQL 12 or higher
- pip (Python package manager)
- Git (optional, for version control)

### System Requirements
- 2GB RAM minimum
- 5GB disk space (for database and historical data)
- Internet connection for API calls

## Installation

### 1. Install Python Dependencies

Create a virtual environment and install required packages:

```bash
# Create project directory
mkdir ipswich-town-db
cd ipswich-town-db

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

### 2. Install PostgreSQL

**Windows:**
- Download from https://www.postgresql.org/download/windows/
- Run installer, set password for 'postgres' user
- Default port: 5432

**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

## Database Setup

### 1. Create Database

```bash
# Connect to PostgreSQL
psql -U postgres

# In PostgreSQL prompt:
CREATE DATABASE ipswich_town_db;
CREATE USER itfc_admin WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE ipswich_town_db TO itfc_admin;
\q
```

### 2. Initialize Database Schema

```bash
# Run the schema creation script
python scripts/create_database.py
```

This creates all necessary tables:
- `seasons`
- `competitions`
- `teams`
- `players`
- `matches`
- `match_statistics`
- `lineups`
- `player_match_stats`
- `goals`
- `cards`

### 3. Configure Database Connection

Edit `config/config.py` with your database credentials:

```python
DATABASE_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'ipswich_town_db',
    'user': 'itfc_admin',
    'password': 'your_secure_password'
}
```

## Data Collection

### Phase 1: Historical Data Collection

#### Option A: Web Scraping (Comprehensive)

```bash
# Scrape historical data from multiple sources
python scripts/scrape_historical_data.py --start-year 1950 --end-year 2023
```

This script collects:
- Match results
- Goalscorers
- Attendance figures
- Competition information

**Sources used:**
- 11v11.com (with rate limiting to respect their servers)
- Transfermarkt
- Soccerway

#### Option B: Manual Import (Quick Start)

For a quick start, import basic historical data:

```bash
python scripts/import_basic_history.py data/ipswich_basic_history.csv
```

### Phase 2: Current Season Setup

#### Register for Free APIs

1. **TheSportsDB**
   - Visit: https://www.thesportsdb.com/api.php
   - Free tier: 1 request per 2 seconds
   - No registration required for basic tier
   - API Key: Use `3` for testing, or donate for full access

2. **Football-Data.org**
   - Visit: https://www.football-data.org/
   - Register for free API key
   - Free tier: 10 requests per minute
   - Add key to `config/config.py`

#### Update API Configuration

Edit `config/config.py`:

```python
API_KEYS = {
    'football_data': 'your_football_data_api_key_here',
    'thesportsdb': '3',  # Free testing key
}
```

## API Integration

### Manual Data Fetch

Fetch current season matches:

```bash
# Fetch all Ipswich Town matches for current season
python scripts/fetch_current_season.py

# Fetch specific match details
python scripts/fetch_match_details.py --match-id 12345

# Update match statistics
python scripts/update_match_stats.py --date 2024-01-15
```

### Test API Connection

```bash
python scripts/test_api_connection.py
```

This verifies:
- Database connection
- API key validity
- Data retrieval functionality

## Automation

### Set Up Automated Updates

#### Option A: Cron Jobs (Linux/macOS)

```bash
# Edit crontab
crontab -e

# Add these lines:
# Update matches daily at 1 AM
0 1 * * * cd /path/to/ipswich-town-db && /path/to/venv/bin/python scripts/daily_update.py >> logs/daily_update.log 2>&1

# Update match statistics hourly on match days (Saturdays/Tuesdays)
0 * * * 6,2 cd /path/to/ipswich-town-db && /path/to/venv/bin/python scripts/update_live_matches.py >> logs/live_update.log 2>&1
```

#### Option B: Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Name: "Ipswich Town Daily Update"
4. Trigger: Daily at 1:00 AM
5. Action: Start a program
   - Program: `C:\path\to\venv\Scripts\python.exe`
   - Arguments: `C:\path\to\ipswich-town-db\scripts\daily_update.py`
   - Start in: `C:\path\to\ipswich-town-db`

#### Option C: Python Scheduler (Cross-platform)

Run the scheduler service:

```bash
python scripts/scheduler_service.py
```

This runs continuously and handles:
- Daily fixture updates
- Match day live updates
- Weekly statistics refresh
- Monthly data validation

## Usage

### Query the Database

#### Python Interface

```python
from database.db_manager import DatabaseManager

db = DatabaseManager()

# Get all matches for a season
matches = db.get_season_matches('2023/24')

# Get player statistics
stats = db.get_player_stats('Luke Woolfenden', '2023/24')

# Get head-to-head record
h2h = db.get_head_to_head('Ipswich Town', 'Norwich City')
```

#### SQL Queries

```sql
-- Connect to database
psql -U itfc_admin -d ipswich_town_db

-- Get all wins in current season
SELECT m.match_date, m.home_team, m.away_team, m.home_score, m.away_score
FROM matches m
JOIN seasons s ON m.season_id = s.id
WHERE s.season_name = '2023/24'
  AND ((m.home_team = 'Ipswich Town' AND m.home_score > m.away_score)
    OR (m.away_team = 'Ipswich Town' AND m.away_score > m.home_score));

-- Top scorers all-time
SELECT p.player_name, COUNT(*) as goals
FROM goals g
JOIN players p ON g.player_id = p.id
GROUP BY p.player_name
ORDER BY goals DESC
LIMIT 10;
```

### Export Data

```bash
# Export season summary to CSV
python scripts/export_data.py --season 2023/24 --output season_summary.csv

# Export all data to JSON
python scripts/export_data.py --format json --output ipswich_complete.json

# Backup database
python scripts/backup_database.py --output backups/
```

### Data Visualization

```bash
# Generate season report
python scripts/generate_report.py --season 2023/24

# Create performance charts
python scripts/create_charts.py --season 2023/24 --output charts/
```

## Project Structure

```
ipswich-town-db/
├── config/
│   ├── __init__.py
│   └── config.py              # Configuration settings
├── database/
│   ├── __init__.py
│   ├── schema.sql             # Database schema
│   ├── db_manager.py          # Database interface
│   └── models.py              # Data models
├── scripts/
│   ├── create_database.py     # Initialize database
│   ├── scrape_historical_data.py
│   ├── fetch_current_season.py
│   ├── update_match_stats.py
│   ├── daily_update.py        # Automated daily update
│   ├── scheduler_service.py   # Scheduler service
│   ├── test_api_connection.py
│   ├── export_data.py
│   └── generate_report.py
├── scrapers/
│   ├── __init__.py
│   ├── base_scraper.py
│   ├── eleven_scraper.py      # 11v11.com scraper
│   └── transfermarkt_scraper.py
├── api/
│   ├── __init__.py
│   ├── thesportsdb_client.py
│   └── football_data_client.py
├── data/
│   └── ipswich_basic_history.csv
├── logs/
│   └── .gitkeep
├── backups/
│   └── .gitkeep
├── requirements.txt
└── README.md
```

## Troubleshooting

### Database Connection Issues
```bash
# Test PostgreSQL connection
psql -U itfc_admin -d ipswich_town_db -c "SELECT 1;"
```

### API Rate Limiting
- Free tier APIs have rate limits
- The scripts include automatic rate limiting
- If you hit limits, wait or upgrade to paid tier

### Missing Data
```bash
# Validate database integrity
python scripts/validate_data.py

# Identify missing matches
python scripts/find_gaps.py --season 2023/24
```

## Future Enhancements

### Immediate Improvements (Free)
- Add more historical data sources
- Implement player transfer tracking
- Create web dashboard using Flask/Django
- Add team formation analysis

### Paid Service Upgrades
- **API-Football** ($10-50/month) - Real-time data, detailed statistics
- **Opta Sports** (Enterprise) - Professional-grade analytics
- **StatsBomb** (Paid tier) - Advanced metrics and event data

### Advanced Features
- Machine learning predictions
- Interactive web interface
- Mobile app integration
- Real-time notifications
- Social media sentiment analysis

## Contributing

This is a personal project, but feel free to fork and adapt for your own club!

## License

MIT License - Free to use and modify

## Support

For issues or questions:
1. Check the logs in `logs/` directory
2. Review error messages in console output
3. Verify API keys and database credentials in `config/config.py`

## Acknowledgments

- TheSportsDB for free API access
- Football-Data.org for match data
- 11v11.com for historical records
- Ipswich Town FC for being a great club to support!
