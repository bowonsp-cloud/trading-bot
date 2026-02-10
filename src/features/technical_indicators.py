"""
Calculate technical indicators
"""

import pandas as pd
import ta
import logging

logger = logging.getLogger(__name__)


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate all technical indicators"""
    
    if df.empty or len(df) < 200:
        logger.warning("Not enough data for indicators")
        return df
    
    df = df.copy()
    df = df.sort_values('timestamp')
    
    try:
        # RSI
        df['rsi_14'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
        
        # MACD
        macd = ta.trend.MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        df['macd_histogram'] = macd.macd_diff()
        
        # Bollinger Bands
        bb = ta.volatility.BollingerBands(df['close'])
        df['bb_upper'] = bb.bollinger_hband()
        df['bb_middle'] = bb.bollinger_mavg()
        df['bb_lower'] = bb.bollinger_lband()
        
        # EMA
        df['ema_20'] = ta.trend.EMAIndicator(df['close'], window=20).ema_indicator()
        df['ema_50'] = ta.trend.EMAIndicator(df['close'], window=50).ema_indicator()
        df['ema_200'] = ta.trend.EMAIndicator(df['close'], window=200).ema_indicator()
        
        # ATR
        df['atr_14'] = ta.volatility.AverageTrueRange(
            df['high'], df['low'], df['close'], window=14
        ).average_true_range()
        
        # Drop NaN
        df = df.dropna()
        
        logger.info(f"Calculated indicators for {len(df)} rows")
        
        return df
    
    except Exception as e:
        logger.error(f"Error calculating indicators: {e}")
        return df
