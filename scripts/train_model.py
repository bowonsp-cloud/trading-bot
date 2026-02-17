"""
Train LSTM model
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

from src.data.supabase_client import SupabaseClient
from src.models.lstm_model import TradingLSTM
from src.utils.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def train_for_symbol(symbol: str, supabase: SupabaseClient):
    """Train model untuk 1 symbol"""
    
    logger.info(f"\n{'='*70}")
    logger.info(f"Training model: {symbol}")
    logger.info(f"{'='*70}")
    
    # Get data
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
    
    # Initialize model
    lstm = TradingLSTM(sequence_length=60)
    
    # Prepare data
    X, y = lstm.prepare_data(df)
    
    if X is None:
        logger.error("Failed to prepare data")
        return
    
    # Split train/test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, shuffle=False
    )
    
    logger.info(f"Train: {len(X_train)}, Test: {len(X_test)}")
    
    # Train
    history = lstm.train(X_train, y_train, X_test, y_test, epochs=100)
    
    # Evaluate
    test_loss, test_acc = lstm.model.evaluate(X_test, y_test, verbose=0)
    logger.info(f"\n✅ Training complete!")
    logger.info(f"   Test Accuracy: {test_acc*100:.2f}%")
    logger.info(f"   Test Loss: {test_loss:.4f}")
    
    # Save model
    os.makedirs("models/saved", exist_ok=True)
    model_path = f"models/saved/{symbol}_H1_model.h5"
    scaler_path = f"models/saved/{symbol}_H1_scaler.pkl"
    
    lstm.save(model_path, scaler_path)
    
    return test_acc


def main():
    logger.info("="*70)
    logger.info("TRAIN ML MODELS")
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
    
    results = {}
    
    for symbol in ALL_SYMBOLS:
        try:
            acc = train_for_symbol(symbol.strip(), supabase)
            results[symbol] = acc
        except Exception as e:
            logger.error(f"Error training {symbol}: {e}", exc_info=True)
    
    logger.info("\n" + "="*70)
    logger.info("TRAINING COMPLETE")
    logger.info("="*70)
    
    for symbol, acc in results.items():
        if acc:
            logger.info(f"  {symbol}: {acc*100:.2f}% accuracy")

if __name__ == "__main__":
    main()
