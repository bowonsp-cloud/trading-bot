import pandas as pd
import ta
import logging

logger = logging.getLogger(__name__)


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate all technical indicators"""
    
    if df.empty:
        logger.warning("Empty dataframe")
        return df
    
    df = df.copy()
    df = df.sort_values('timestamp')
    
    # Check minimum data
    if len(df) < 200:
        logger.warning(f"Not enough data: {len(df)} rows (need 200+)")
        return df
    
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
        
        # JANGAN drop NaN - biarkan NULL untuk rows yang belum cukup data
        # Yang penting adalah rows terakhir (latest) sudah punya indicators
        
        # Count rows yang punya indicators lengkap
        indicator_cols = ['rsi_14', 'macd', 'ema_20', 'ema_50', 'ema_200', 'atr_14']
        valid_rows = df[indicator_cols].notna().all(axis=1).sum()
        
        logger.info(f"Calculated indicators: {valid_rows}/{len(df)} rows have complete data")
        
        return df
    
    except Exception as e:
        logger.error(f"Error calculating indicators: {e}")
        return df
