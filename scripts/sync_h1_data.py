"""
Sync H1 OHLC data dari Dukascopy ke Supabase
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
from datetime import datetime

from src.data.dukascopy_downloader import DukascopyH1Downloader
from src.data.supabase_client import SupabaseClient
from src.utils.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def sync_symbol(symbol: str, supabase: SupabaseClient) -> int:
    """Sync data untuk 1 symbol"""
    
    # Get latest timestamp dari database
    response = supabase.client.table("ohlc_data").select(
        "timestamp"
    ).eq(
        "symbol", symbol
    ).eq(
        "timeframe", "H1"
    ).order(
        "timestamp", desc=True
    ).limit(1).execute()
    
    if response.data:
        latest_ts = response.data[0]['timestamp']
        latest_ts = pd.to_datetime(latest_ts)
        if latest_ts.tz is not None:
            latest_ts = latest_ts.tz_localize(None)
        start_date = latest_ts + timedelta(hours=1)
    else:
        # Tidak ada data, download 7 hari
        start_date = datetime.utcnow() - timedelta(days=7)
    
    end_date = datetime.utcnow()
    
    # Skip kalau tidak ada data baru
    if start_date >= end_date:
        logger.info(f"{symbol}: Already up to date")
        return 0
    
    # Download
    downloader = DukascopyH1Downloader(symbol)
    df = downloader.download_range(start_date, end_date)
    
    if df.empty:
        logger.warning(f"{symbol}: No new data")
        return 0
    
    # Upload
    uploaded = supabase.upload_ohlc(df, symbol, 'H1')
    return uploaded


def main():
    logger.info("="*70)
    logger.info("SYNC H1 DATA")
    logger.info("="*70)
    logger.info(f"Symbols: {', '.join(config.SYMBOLS)}")
    logger.info(f"Total: {len(config.SYMBOLS)} pairs")
    logger.info("="*70)
    
    config.validate()
    supabase = SupabaseClient()
    
    results = {}
    
    for symbol in config.SYMBOLS:
        logger.info(f"\nSyncing {symbol}")
        try:
            uploaded = sync_symbol(symbol, supabase)
            results[symbol] = uploaded
            if uploaded > 0:
                logger.info(f"✅ {symbol}: {uploaded} candles")
            else:
                logger.info(f"✅ {symbol}: Already up to date")
        except Exception as e:
            logger.error(f"❌ {symbol}: Error - {e}")
            results[symbol] = 0
    
    # Summary
    logger.info("\n" + "="*70)
    logger.info("SYNC SUMMARY")
    logger.info("="*70)
    for symbol, count in results.items():
        logger.info(f"  {symbol}: {count} new candles")
    logger.info("✅ Sync complete!")


if __name__ == "__main__":
    import pandas as pd
    from datetime import timedelta
    main()
