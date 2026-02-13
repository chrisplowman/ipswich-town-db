# Quick Start Guide

## Step-by-Step Setup (15 minutes)

### 1. Install PostgreSQL

**Windows:**
1. Download from https://www.postgresql.org/download/windows/
2. Run installer, set password for 'postgres' user
3. Remember your password!

**macOS:**
```bash
brew install postgresql@14
brew services start postgresql@14
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### 2. Install Python Dependencies

```bash
# Navigate to project directory
cd ipswich-town-db

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### 3. Configure Database

Edit `config/config.py` and set your database password:
```python
DATABASE_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'ipswich_town_db',
    'user': 'itfc_admin',
    'password': 'YOUR_PASSWORD_HERE'  # Change this!
}
```

### 4. Create Database

```bash
# Create the PostgreSQL user and database
psql -U postgres

# In PostgreSQL prompt:
CREATE USER itfc_admin WITH PASSWORD 'your_password';
CREATE DATABASE ipswich_town_db OWNER itfc_admin;
\q

# Initialize the schema
python scripts/create_database.py
```

### 5. Configure API Keys (Optional but Recommended)

**Football-Data.org (Free):**
1. Visit https://www.football-data.org/
2. Click "Register" and create account
3. Copy your API key
4. Add to `config/config.py`:
```python
API_KEYS = {
    'football_data': 'YOUR_API_KEY_HERE',
    'thesportsdb': '3',
}
```

**TheSportsDB:**
- Free tier works with key '3' (already configured)
- For unlimited access, donate at https://www.thesportsdb.com/

### 6. Test Everything

```bash
python scripts/test_api_connection.py
```

You should see:
```
✓ Database connection successful
✓ TheSportsDB API working
✓ Football-Data.org API working
```

### 7. Fetch Current Season Data

```bash
python scripts/fetch_current_season.py
```

This will:
- Download recent matches
- Download upcoming fixtures  
- Download current squad
- Store everything in your database

### 8. Query Your Data

```bash
# Connect to database
psql -U itfc_admin -d ipswich_town_db

# View recent matches
SELECT * FROM ipswich_matches LIMIT 5;

# View season statistics
SELECT * FROM season_statistics;

# Exit
\q
```

## What's Next?

### Set Up Automation

**Option 1: Simple (Run manually when needed)**
```bash
python scripts/daily_update.py
```

**Option 2: Automated (Linux/macOS)**
```bash
crontab -e
# Add this line for daily 1 AM updates:
0 1 * * * cd /path/to/ipswich-town-db && /path/to/venv/bin/python scripts/daily_update.py
```

**Option 3: Automated (Windows)**
1. Open Task Scheduler
2. Create Basic Task → Daily → 1:00 AM
3. Action: Start program
4. Program: `C:\path\to\venv\Scripts\python.exe`
5. Arguments: `scripts\daily_update.py`
6. Start in: `C:\path\to\ipswich-town-db`

### Explore the Data

Try these SQL queries:

```sql
-- Top scorers this season
SELECT * FROM top_scorers LIMIT 10;

-- All home wins
SELECT * FROM ipswich_matches 
WHERE venue = 'Home' AND result = 'Win'
ORDER BY match_date DESC;

-- Average attendance
SELECT AVG(attendance) FROM ipswich_matches 
WHERE attendance IS NOT NULL;

-- Head-to-head vs Norwich
SELECT * FROM ipswich_matches 
WHERE opponent = 'Norwich City';
```

### Export Data

```bash
# Export to CSV
psql -U itfc_admin -d ipswich_town_db -c "COPY ipswich_matches TO '/tmp/matches.csv' CSV HEADER;"
```

## Troubleshooting

**"psycopg2" installation fails:**
```bash
# Try installing system dependencies first
# Ubuntu/Debian:
sudo apt install libpq-dev python3-dev
# macOS:
brew install postgresql
```

**Database connection fails:**
- Check PostgreSQL is running: `sudo systemctl status postgresql` (Linux)
- Verify password in config/config.py
- Check user has access: `psql -U itfc_admin -d ipswich_town_db`

**API returns no data:**
- Check internet connection
- Verify API keys in config/config.py
- Check rate limits (free tiers have limits)
- Try running test script: `python scripts/test_api_connection.py`

**"ModuleNotFoundError":**
- Make sure virtual environment is activated
- Run: `pip install -r requirements.txt`

## Need Help?

Check the main README.md for detailed documentation on:
- Database schema
- API usage
- Advanced queries
- Data export options
- Adding historical data
