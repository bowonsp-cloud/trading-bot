"""
Generate trading predictions untuk semua symbols
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
import pandas as pd
from datetime import datetime

from src.data.supabase_client import SupabaseClient
from src.prediction.predictor import TradingPredictor
from src.utils.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_for_symbol(symbol: str, supabase: SupabaseClient):
    """Generate prediction untuk 1 symbol"""
    
    logger.info(f"\n{'='*70}")
    logger.info(f"Generating prediction: {symbol}")
    logger.info(f"{'='*70}")
    
    # Model paths
    model_path = f"models/saved/{symbol}_H1_model.h5"
    scaler_path = f"models/saved/{symbol}_H1_scaler.pkl"
    
    # Check if model exists
    if not os.path.exists(model_path):
        logger.warning(f"Model not found: {model_path}")
        return None
    
    # Get latest data
    response = supabase.client.table("ohlc_data").select("*").eq(
        "symbol", symbol
    ).eq(
        "timeframe", "H1"
    ).order("timestamp", desc=False).execute()
    
    if not response.data:
        logger.warning(f"No data for {symbol}")
        return None
    
    df = pd.DataFrame(response.data)
    logger.info(f"Loaded {len(df)} candles")
    
    # Initialize predictor
    try:
        predictor = TradingPredictor(symbol, model_path, scaler_path)
    except Exception as e:
        logger.error(f"Failed to initialize predictor: {e}")
        return None
    
    # Generate prediction
    prediction = predictor.predict(df)
    
    if prediction is None:
        logger.error("Prediction failed")
        return None
    
    # Log prediction
    logger.info(f"Signal: {prediction['signal']}")
    logger.info(f"Confidence: {prediction['confidence']:.2%}")
    logger.info(f"Entry: {prediction['entry_price']}")
    
    if prediction['signal'] != 'HOLD':
        logger.info(f"TP: {prediction['tp_price']}")
        logger.info(f"SL: {prediction['sl_price']}")
    
    # Save to database (hanya jika confidence tinggi dan bukan HOLD)
    if prediction['confidence'] >= config.MIN_CONFIDENCE and prediction['signal'] != 'HOLD':
        
        # Prepare data untuk database
        db_prediction = {
            'symbol': prediction['symbol'],
            'timeframe': prediction['timeframe'],
            'signal': prediction['signal'],
            'confidence': prediction['confidence'],
            'entry_price': prediction['entry_price'],
            'tp_price': prediction['tp_price'],
            'sl_price': prediction['sl_price'],
            'lot_size': prediction['lot_size'],
            'valid_until': prediction['valid_until'],
            'model_version': prediction['model_version'],
            'algorithm': prediction['algorithm'],
            'status': 'pending'
        }
        
        try:
            supabase.client.table("predictions").insert(db_prediction).execute()
            logger.info(f"✅ Prediction saved to database")
        except Exception as e:
            logger.error(f"Failed to save prediction: {e}")
    
    else:
        logger.info(f"Skipped saving (confidence: {prediction['confidence']:.2%}, signal: {prediction['signal']})")
    
    return prediction


def main():
    logger.info("="*70)
    logger.info("GENERATE TRADING PREDICTIONS")
    logger.info("="*70)
    logger.info(f"Min Confidence: {config.MIN_CONFIDENCE}")
    logger.info("="*70)
    
    config.validate()
    supabase = SupabaseClient()
    
    # Generate predictions
    results = {}
    
   # Generate predictions untuk semua symbols di config
    for symbol in config.SYMBOLS:
        try:
            prediction = generate_for_symbol(symbol, supabase)
            results[symbol] = prediction
        except Exception as e:
            logger.error(f"Error generating prediction for {symbol}: {e}", exc_info=True)
    
    # Summary
    logger.info("\n" + "="*70)
    logger.info("PREDICTION SUMMARY")
    logger.info("="*70)
    
    for symbol, prediction in results.items():
        if prediction:
            logger.info(f"{symbol}: {prediction['signal']} ({prediction['confidence']:.2%})")
        else:
            logger.info(f"{symbol}: Failed")
    
    logger.info("\n✅ Prediction generation complete!")


if __name__ == "__main__":
    main()
