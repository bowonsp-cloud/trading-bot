"""
Sync H1 data
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
from datetime import datetime, timedelta
from src.data.dukascopy_downloader import DukascopyH1Downloader
from src.data.supabase_client import SupabaseClient
from src.utils.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    logger.info("Starting data sync...")
    
    config.validate()
    supabase = SupabaseClient()
    
    for symbol in config.SYMBOLS:
        logger.info(f"Syncing {symbol}")
        
        latest = supabase.get_latest_timestamp(symbol)
        start = latest + timedelta(hours=1) if latest else datetime.utcnow() - timedelta(hours=config.LOOKBACK_HOURS)
        end = datetime.utcnow()
        
        downloader = DukascopyH1Downloader(symbol.strip())
        df = downloader.download_range(start, end)
        
        if not df.empty:
            uploaded = supabase.upload_ohlc(df, symbol, 'H1')
            logger.info(f"✅ {symbol}: {uploaded} candles")
    
    logger.info("Sync complete!")


if __name__ == "__main__":
    main()
