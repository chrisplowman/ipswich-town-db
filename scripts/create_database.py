"""
Initialize database schema
Run this script to create all tables and initial data
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from pathlib import Path
import logging

from config.config import DATABASE_CONFIG, LOGGING_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_database():
    """Create the database and schema"""
    
    # First connect to postgres database to create our database
    conn_params = DATABASE_CONFIG.copy()
    db_name = conn_params.pop('database')
    conn_params['database'] = 'postgres'
    
    try:
        # Create database if it doesn't exist
        conn = psycopg2.connect(**conn_params)
        conn.autocommit = True
        cur = conn.cursor()
        
        # Check if database exists
        cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}';")
        exists = cur.fetchone()
        
        if not exists:
            logger.info(f"Creating database: {db_name}")
            cur.execute(f"CREATE DATABASE {db_name};")
            logger.info(f"Database {db_name} created successfully")
        else:
            logger.info(f"Database {db_name} already exists")
        
        cur.close()
        conn.close()
        
        # Now connect to our database and create schema
        logger.info("Creating database schema...")
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cur = conn.cursor()
        
        # Read and execute schema file
        schema_file = Path(__file__).parent.parent / 'database' / 'schema.sql'
        with open(schema_file, 'r') as f:
            schema_sql = f.read()
        
        cur.execute(schema_sql)
        conn.commit()
        
        logger.info("Database schema created successfully")
        
        # Verify tables were created
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        
        tables = cur.fetchall()
        logger.info(f"Created {len(tables)} tables:")
        for table in tables:
            logger.info(f"  - {table[0]}")
        
        cur.close()
        conn.close()
        
        logger.info("\n✓ Database initialization complete!")
        logger.info(f"\nYou can now connect using:")
        logger.info(f"  psql -U {DATABASE_CONFIG['user']} -d {db_name}")
        
        return True
        
    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        return False
    except FileNotFoundError as e:
        logger.error(f"Schema file not found: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Ipswich Town FC Database Initialization")
    print("=" * 60)
    print()
    
    success = create_database()
    
    if success:
        print("\n" + "=" * 60)
        print("SUCCESS: Database is ready to use!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Update API keys in config/config.py")
        print("2. Run scripts/fetch_current_season.py to fetch latest matches")
        print("3. Set up automation with scripts/daily_update.py")
    else:
        print("\n" + "=" * 60)
        print("ERROR: Database initialization failed")
        print("=" * 60)
        print("\nPlease check:")
        print("1. PostgreSQL is installed and running")
        print("2. Database credentials in config/config.py are correct")
        print("3. User has sufficient privileges")
        sys.exit(1)
