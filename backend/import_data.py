#!/usr/bin/env python
"""Script to import CSV data into Elasticsearch"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.csv_importer import csv_importer
from app.services.elasticsearch_service import es_service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting data import to Elasticsearch...")
    
    if not es_service.es or not es_service.es.ping():
        logger.error("Cannot connect to Elasticsearch. Check your configuration.")
        logger.error("Make sure your .env file has the correct credentials")
        return
    
    logger.info("Connected to Elasticsearch successfully")
    
    results = csv_importer.run_full_import("data/")
    
    logger.info("=" * 50)
    logger.info("Import completed!")
    logger.info(f"Deputies imported: {results.get('deputes', 0)}")
    logger.info(f"Seances imported: {results.get('seances', 0)}")
    logger.info(f"Legislative texts imported: {results.get('legislatifs', 0)}")
    logger.info(f"Debates imported: {results.get('debats', 0)}")
    logger.info("=" * 50)

if __name__ == "__main__":
    main()