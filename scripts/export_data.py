"""
Export data from database to various formats
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path

from database.db_manager import DatabaseManager
from config.config import EXPORT_CONFIG

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataExporter:
    """Export database data to various formats"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.output_dir = EXPORT_CONFIG['output_dir']
        self.output_dir.mkdir(exist_ok=True)
    
    def export_season(self, season_name: str, format: str = 'csv') -> str:
        """Export all data for a season"""
        logger.info(f"Exporting {season_name} season data...")
        
        # Get season matches
        matches = self.db.get_season_matches(season_name)
        
        if not matches:
            logger.warning(f"No matches found for season {season_name}")
            return None
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"ipswich_{season_name.replace('/', '-')}_{timestamp}"
        
        if format == 'csv':
            filepath = self.output_dir / f"{filename}.csv"
            self._export_to_csv(matches, filepath)
        elif format == 'json':
            filepath = self.output_dir / f"{filename}.json"
            self._export_to_json(matches, filepath)
        else:
            logger.error(f"Unsupported format: {format}")
            return None
        
        logger.info(f"Exported to: {filepath}")
        return str(filepath)
    
    def export_all_time_stats(self, format: str = 'csv') -> str:
        """Export all-time statistics"""
        logger.info("Exporting all-time statistics...")
        
        # Get top scorers
        top_scorers = self.db.get_top_scorers(limit=50)
        
        # Get all matches
        all_matches = self.db.execute_query("""
            SELECT * FROM ipswich_matches
            ORDER BY match_date DESC;
        """)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format == 'csv':
            # Export matches
            matches_file = self.output_dir / f"ipswich_all_matches_{timestamp}.csv"
            self._export_to_csv(all_matches, matches_file)
            
            # Export scorers
            scorers_file = self.output_dir / f"ipswich_top_scorers_{timestamp}.csv"
            self._export_to_csv(top_scorers, scorers_file)
            
            logger.info(f"Exported matches to: {matches_file}")
            logger.info(f"Exported scorers to: {scorers_file}")
            return str(matches_file)
            
        elif format == 'json':
            filepath = self.output_dir / f"ipswich_all_data_{timestamp}.json"
            data = {
                'matches': all_matches,
                'top_scorers': top_scorers,
                'exported_at': datetime.now().isoformat()
            }
            self._export_to_json(data, filepath)
            logger.info(f"Exported to: {filepath}")
            return str(filepath)
    
    def export_head_to_head(self, opponent: str, format: str = 'csv') -> str:
        """Export head-to-head record against an opponent"""
        logger.info(f"Exporting head-to-head vs {opponent}...")
        
        # Get matches
        matches = self.db.execute_query("""
            SELECT * FROM ipswich_matches
            WHERE opponent = %s
            ORDER BY match_date DESC;
        """, (opponent,))
        
        if not matches:
            logger.warning(f"No matches found against {opponent}")
            return None
        
        # Get summary
        summary = self.db.get_head_to_head(opponent)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_opponent = opponent.replace(' ', '_').replace('/', '-')
        
        if format == 'csv':
            filepath = self.output_dir / f"h2h_{safe_opponent}_{timestamp}.csv"
            
            # Add summary as first rows
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Head-to-Head Summary'])
                writer.writerow(['Metric', 'Value'])
                for key, value in summary.items():
                    writer.writerow([key, value])
                writer.writerow([])  # Empty row
                writer.writerow(['Match History'])
                
                # Write matches
                if matches:
                    writer.writerow(matches[0].keys())
                    for match in matches:
                        writer.writerow(match.values())
            
            logger.info(f"Exported to: {filepath}")
            return str(filepath)
            
        elif format == 'json':
            filepath = self.output_dir / f"h2h_{safe_opponent}_{timestamp}.json"
            data = {
                'opponent': opponent,
                'summary': summary,
                'matches': matches,
                'exported_at': datetime.now().isoformat()
            }
            self._export_to_json(data, filepath)
            logger.info(f"Exported to: {filepath}")
            return str(filepath)
    
    def _export_to_csv(self, data: list, filepath: Path):
        """Export data to CSV"""
        if not data:
            logger.warning("No data to export")
            return
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
    
    def _export_to_json(self, data, filepath: Path):
        """Export data to JSON"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Export Ipswich Town FC data')
    parser.add_argument('--season', help='Season to export (e.g., 2023/24)')
    parser.add_argument('--all-time', action='store_true', help='Export all-time statistics')
    parser.add_argument('--opponent', help='Export head-to-head vs opponent')
    parser.add_argument('--format', choices=['csv', 'json'], default='csv', help='Export format')
    
    args = parser.parse_args()
    
    exporter = DataExporter()
    
    try:
        if args.season:
            exporter.export_season(args.season, args.format)
        elif args.all_time:
            exporter.export_all_time_stats(args.format)
        elif args.opponent:
            exporter.export_head_to_head(args.opponent, args.format)
        else:
            print("Please specify what to export:")
            print("  --season 2023/24       Export specific season")
            print("  --all-time             Export all-time data")
            print("  --opponent 'Norwich'   Export head-to-head")
            print("\nAdd --format json for JSON output (default is CSV)")
            sys.exit(1)
        
        print("\n✓ Export complete!")
        
    except Exception as e:
        logger.error(f"Export failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
