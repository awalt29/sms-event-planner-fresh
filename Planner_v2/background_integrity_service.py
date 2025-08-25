#!/usr/bin/env python3
"""
Background Data Integrity Maintenance Service

This script runs data integrity checks and fixes in the background,
separate from SMS processing to avoid blocking user responses.

Usage:
- Run once: python background_integrity_service.py
- Run as cron job: */15 * * * * cd /path/to/app && python background_integrity_service.py
- Run as daemon: Use supervisor or similar process manager
"""

import os
import sys
import time
import logging
from datetime import datetime

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.services.data_integrity_service import DataIntegrityService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [INTEGRITY] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/integrity_maintenance.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_integrity_maintenance():
    """Run a single integrity check and maintenance cycle"""
    try:
        app = create_app()
        
        with app.app_context():
            logger.info("Starting data integrity maintenance cycle")
            
            integrity_service = DataIntegrityService()
            results = integrity_service.check_and_fix_all_issues()
            
            total_fixed = sum(results.values())
            
            if total_fixed > 0:
                logger.warning(f"Fixed {total_fixed} data integrity issues: {results}")
            else:
                logger.info("No data integrity issues found - database is clean")
            
            return results
            
    except Exception as e:
        logger.error(f"Data integrity maintenance failed: {e}")
        raise

def run_continuous_maintenance(interval_minutes=15):
    """Run integrity maintenance continuously with specified interval"""
    logger.info(f"Starting continuous integrity maintenance (every {interval_minutes} minutes)")
    
    while True:
        try:
            run_integrity_maintenance()
            logger.info(f"Next integrity check in {interval_minutes} minutes")
            time.sleep(interval_minutes * 60)
            
        except KeyboardInterrupt:
            logger.info("Integrity maintenance stopped by user")
            break
        except Exception as e:
            logger.error(f"Integrity maintenance error: {e}")
            logger.info(f"Retrying in {interval_minutes} minutes")
            time.sleep(interval_minutes * 60)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Background Data Integrity Maintenance")
    parser.add_argument("--continuous", action="store_true", 
                       help="Run continuously (default: run once)")
    parser.add_argument("--interval", type=int, default=15,
                       help="Minutes between checks in continuous mode (default: 15)")
    
    args = parser.parse_args()
    
    if args.continuous:
        run_continuous_maintenance(args.interval)
    else:
        results = run_integrity_maintenance()
        total_fixed = sum(results.values())
        print(f"Integrity check complete. Fixed {total_fixed} issues.")
        sys.exit(0 if total_fixed == 0 else 1)
