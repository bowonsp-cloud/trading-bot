"""
One-time historical data download
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
    logger.info("="*70)
    logger.info("HISTORICAL DATA DOWNLOAD")
    logger.info("="*70)
    
    # HARDCODED: Download semua 11 pairs
    symbols_to_download = [
        'EURUSD', 'GBPUSD', 'XAUUSD', 
        'USDJPY', 'AUDUSD', 'USDCHF', 
        'USDCAD', 'NZDUSD', 'EURGBP', 
        'EURJPY', 'GBPJPY'
    ]
    
    logger.info(f"Total symbols to download: {len(symbols_to_download)}")
    logger.info(f"Symbols: {', '.join(symbols_to_download)}")
    
    config.validate()
    supabase = SupabaseClient()
    
    # Download 30 hari terakhir
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    logger.info(f"Downloading from {start_date} to {end_date}")
    logger.info("="*70)
    
    for symbol in symbols_to_download:
        logger.info(f"\n{'='*70}")
        logger.info(f"Downloading {symbol}")
        logger.info(f"{'='*70}")
        
        try:
            downloader = DukascopyH1Downloader(symbol)
            df = downloader.download_range(start_date, end_date)
            
            if not df.empty:
                uploaded = supabase.upload_ohlc(df, symbol, 'H1')
                logger.info(f"✅ {symbol}: {uploaded} candles uploaded")
            else:
                logger.warning(f"⚠️  {symbol}: No data downloaded")
        
        except Exception as e:
            logger.error(f"❌ {symbol}: Error - {e}")
            continue
    
    logger.info("\n" + "="*70)
    logger.info("✅ Historical download complete!")
    logger.info("="*70)


if __name__ == "__main__":
    main()
