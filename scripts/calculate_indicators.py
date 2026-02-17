"""
Calculate and update technical indicators
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
import pandas as pd
from src.data.supabase_client import SupabaseClient
from src.features.technical_indicators import calculate_indicators
from src.utils.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def update_indicators_for_symbol(symbol: str, supabase: SupabaseClient):
    """Update indicators for one symbol"""
    
    logger.info(f"\n{'='*70}")
    logger.info(f"Updating indicators: {symbol}")
    logger.info(f"{'='*70}")
    
    # Get OHLC data
    response = supabase.client.table("ohlc_data").select("*").eq(
        "symbol", symbol
    ).eq(
        "timeframe", "H1"
    ).order("timestamp").execute()
    
    if not response.data:
        logger.warning(f"No data for {symbol}")
        return
    
    df = pd.DataFrame(response.data)
    logger.info(f"Loaded {len(df)} rows")
    
    # Calculate indicators
    df = calculate_indicators(df)
    
    if df.empty:
        logger.warning("No data after calculating indicators")
        return
    
    # Update database
    updated = 0
    
    for _, row in df.iterrows():
        try:
            update_data = {
                'rsi_14': float(row['rsi_14']) if pd.notna(row['rsi_14']) else None,
                'macd': float(row['macd']) if pd.notna(row['macd']) else None,
                'macd_signal': float(row['macd_signal']) if pd.notna(row['macd_signal']) else None,
                'macd_histogram': float(row['macd_histogram']) if pd.notna(row['macd_histogram']) else None,
                'bb_upper': float(row['bb_upper']) if pd.notna(row['bb_upper']) else None,
                'bb_middle': float(row['bb_middle']) if pd.notna(row['bb_middle']) else None,
                'bb_lower': float(row['bb_lower']) if pd.notna(row['bb_lower']) else None,
                'ema_20': float(row['ema_20']) if pd.notna(row['ema_20']) else None,
                'ema_50': float(row['ema_50']) if pd.notna(row['ema_50']) else None,
                'ema_200': float(row['ema_200']) if pd.notna(row['ema_200']) else None,
                'atr_14': float(row['atr_14']) if pd.notna(row['atr_14']) else None,
            }
            
            supabase.client.table("ohlc_data").update(update_data).eq(
                'id', row['id']
            ).execute()
            
            updated += 1
            
            if updated % 50 == 0:
                logger.info(f"  Updated {updated}/{len(df)} rows")
        
        except Exception as e:
            logger.error(f"Error updating row {row['id']}: {e}")
            continue
    
    logger.info(f"✅ {symbol}: Updated {updated} rows with indicators")


def main():
    logger.info("="*70)
    logger.info("CALCULATE TECHNICAL INDICATORS")
    logger.info("="*70)
    
    # Hardcoded semua 11 pairs
    ALL_SYMBOLS = [
        'EURUSD', 'GBPUSD', 'XAUUSD',
        'USDJPY', 'AUDUSD', 'USDCHF',
        'USDCAD', 'NZDUSD', 'EURGBP',
        'EURJPY', 'GBPJPY'
    ]
    
    logger.info(f"Symbols: {', '.join(ALL_SYMBOLS)}")
    logger.info(f"Total: {len(ALL_SYMBOLS)} pairs")
    logger.info("="*70)
    
    config.validate()
    supabase = SupabaseClient()
    
    for symbol in ALL_SYMBOLS:
        try:
            update_indicators_for_symbol(symbol.strip(), supabase)
        except Exception as e:
            logger.error(f"Error processing {symbol}: {e}")
    
    logger.info("\n✅ Indicators calculation complete!")

if __name__ == "__main__":
    main()
