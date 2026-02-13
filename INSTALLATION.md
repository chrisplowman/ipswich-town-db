# Installation Summary & File Overview

## What You Have

A complete Ipswich Town FC database system with:
- PostgreSQL database schema
- Python scripts for data collection and management  
- API integrations (TheSportsDB & Football-Data.org)
- Automated update system
- Data export utilities

## Project Structure

```
ipswich-town-db/
├── README.md                    ← Main documentation
├── QUICKSTART.md               ← 15-minute setup guide
├── requirements.txt            ← Python dependencies
├── .env.example               ← Configuration template
├── .gitignore                 ← Git ignore rules
│
├── config/
│   ├── config.py              ← Main configuration (EDIT THIS)
│   └── __init__.py
│
├── database/
│   ├── schema.sql             ← Database structure
│   ├── db_manager.py          ← Database interface
│   └── __init__.py
│
├── api/
│   ├── thesportsdb_client.py  ← TheSportsDB API client
│   ├── football_data_client.py ← Football-Data.org API client
│   └── __init__.py
│
├── scripts/
│   ├── create_database.py     ← Initialize database (RUN FIRST)
│   ├── test_api_connection.py ← Test everything (RUN SECOND)
│   ├── fetch_current_season.py ← Fetch initial data (RUN THIRD)
│   ├── daily_update.py        ← Daily automation script
│   ├── export_data.py         ← Export to CSV/JSON
│   └── __init__.py
│
├── logs/                      ← Application logs (auto-created)
├── exports/                   ← Exported data (auto-created)
├── backups/                   ← Database backups (auto-created)
└── data/                      ← Historical data imports

```

## Installation Steps (Start Here!)

### Step 1: Extract Files
Unzip the ipswich-town-db folder to your desired location.

### Step 2: Install PostgreSQL
- **Windows**: https://www.postgresql.org/download/windows/
- **macOS**: `brew install postgresql@14`
- **Linux**: `sudo apt install postgresql`

### Step 3: Install Python Dependencies
```bash
cd ipswich-town-db
python -m venv venv

# Activate virtual environment:
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

pip install -r requirements.txt
```

### Step 4: Configure Database
Edit `config/config.py` line 11-17:
```python
DATABASE_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'ipswich_town_db',
    'user': 'itfc_admin',
    'password': 'YOUR_PASSWORD_HERE'  # ← Change this!
}
```

### Step 5: Create Database & User
```bash
# Connect to PostgreSQL
psql -U postgres

# Create user and database
CREATE USER itfc_admin WITH PASSWORD 'your_password';
CREATE DATABASE ipswich_town_db OWNER itfc_admin;
\q

# Initialize schema
python scripts/create_database.py
```

### Step 6: Configure API Keys (Optional)
Register for free API key at: https://www.football-data.org/

Edit `config/config.py` line 20-23:
```python
API_KEYS = {
    'football_data': 'YOUR_API_KEY_HERE',  # ← Add your key
    'thesportsdb': '3',  # Free tier
}
```

### Step 7: Test Everything
```bash
python scripts/test_api_connection.py
```

### Step 8: Fetch Initial Data
```bash
python scripts/fetch_current_season.py
```

## Key Configuration Files to Edit

### 1. config/config.py
**What to change:**
- Lines 11-17: Database password
- Lines 20-23: API keys (after registering)

**Leave as-is:**
- Everything else (unless you have specific needs)

### 2. .env.example
**Optional:** Copy to `.env` and use environment variables instead of editing config.py

## Common Commands

### Daily Operations
```bash
# Update match results
python scripts/daily_update.py

# Export season data
python scripts/export_data.py --season 2023/24

# Export all-time stats
python scripts/export_data.py --all-time

# Head-to-head analysis
python scripts/export_data.py --opponent "Norwich City"
```

### Database Queries
```bash
# Connect to database
psql -U itfc_admin -d ipswich_town_db

# View recent matches
SELECT * FROM ipswich_matches LIMIT 10;

# Season statistics
SELECT * FROM season_statistics WHERE season_name = '2023/24';

# Top scorers
SELECT * FROM top_scorers LIMIT 10;
```

## Automation Setup

### Linux/macOS (Cron)
```bash
crontab -e

# Add daily 1 AM update:
0 1 * * * cd /path/to/ipswich-town-db && /path/to/venv/bin/python scripts/daily_update.py >> logs/cron.log 2>&1
```

### Windows (Task Scheduler)
1. Open Task Scheduler
2. Create Basic Task
3. Name: "Ipswich Town Daily Update"
4. Trigger: Daily, 1:00 AM
5. Action: Start a program
   - Program: `C:\path\to\venv\Scripts\python.exe`
   - Arguments: `scripts\daily_update.py`
   - Start in: `C:\path\to\ipswich-town-db`

## What Each Script Does

### create_database.py
Creates PostgreSQL database and all tables. Run once during setup.

### test_api_connection.py
Tests database connection and API access. Run after configuration.

### fetch_current_season.py
Downloads recent matches, fixtures, and squad. Run once to populate database.

### daily_update.py
Updates match scores and statistics. Run daily via automation.

### export_data.py
Exports data to CSV/JSON files for analysis elsewhere.

## Data Sources

### Free APIs (No Registration)
- **TheSportsDB**: Basic match data, scores, fixtures
  - Rate limit: 1 request per 2 seconds
  - Coverage: Good for basic data

### Free APIs (Registration Required)
- **Football-Data.org**: More detailed match data
  - Rate limit: 10 requests per minute
  - Coverage: Excellent for Championship/Premier League
  - Register: https://www.football-data.org/

### Future Paid Options (When You're Ready)
- **API-Football**: £10-50/month, real-time data
- **Opta Sports**: Enterprise-grade analytics
- **StatsBomb**: Advanced event data

## Database Schema Highlights

### Key Tables
- **matches**: All match data (scores, dates, venues)
- **match_statistics**: Possession, shots, fouls, etc.
- **players**: Squad information
- **goals**: Who scored when
- **cards**: Yellow/red cards
- **seasons**: Season information
- **competitions**: League, cup competitions

### Useful Views
- **ipswich_matches**: Pre-formatted match list
- **top_scorers**: All-time goalscorers
- **season_statistics**: Wins/draws/losses by season

## Getting Help

### Issues During Setup?
1. Read error messages carefully
2. Check QUICKSTART.md for troubleshooting
3. Verify PostgreSQL is running: `systemctl status postgresql`
4. Test API keys: `python scripts/test_api_connection.py`

### Want to Add Historical Data?
See README.md "Historical Data Collection" section for web scraping options.

### Need to Reset Database?
```bash
psql -U postgres -c "DROP DATABASE ipswich_town_db;"
psql -U postgres -c "CREATE DATABASE ipswich_town_db OWNER itfc_admin;"
python scripts/create_database.py
```

## Next Steps After Installation

1. ✓ Run daily_update.py to keep data current
2. ✓ Set up automation (cron/Task Scheduler)
3. ✓ Explore data with SQL queries
4. ✓ Export data for analysis in Excel/Python
5. ✓ Consider adding historical data via web scraping

## System Requirements

- **Python**: 3.8 or higher
- **PostgreSQL**: 12 or higher  
- **Disk Space**: 5GB (for database and historical data)
- **RAM**: 2GB minimum
- **Internet**: Required for API calls

## Free Tier Limitations

- **TheSportsDB**: 1 request per 2 seconds (2,880/day)
- **Football-Data.org**: 10 requests per minute (14,400/day)

These limits are more than sufficient for daily updates. You'd only hit limits with intensive bulk historical data collection.

## License

MIT License - Free to use and modify for personal or commercial use.

## Support Ipswich Town!

This is a fan project. If you find it useful, consider:
- Attending matches at Portman Road
- Buying official merchandise
- Sharing your database insights with other fans!

Come On You Blues! 💙
