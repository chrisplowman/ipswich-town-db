#!/bin/bash
echo "Starting Ipswich Town DB initialization..."

# Install dependencies
pip install -r requirements.txt

# Initialize database
python scripts/create_database.py

# Fetch initial data
python scripts/fetch_current_season.py

echo "Setup complete! Database is ready."

# Keep the service alive (for free tier)
while true; do
  sleep 3600
done
