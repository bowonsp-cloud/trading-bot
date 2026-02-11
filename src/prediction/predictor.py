"""
Generate trading predictions menggunakan trained model
"""

import numpy as np
import pandas as pd
from tensorflow.keras.models import load_model
import joblib
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class TradingPredictor:
    """Generate predictions dari trained LSTM model"""
    
    def __init__(self, symbol: str, model_path: str, scaler_path: str):
        self.symbol = symbol
        self.sequence_length = 60
        
        # Load model & scaler
        try:
            self.model = load_model(model_path)
            self.scaler = joblib.load(scaler_path)
            logger.info(f"Model loaded: {symbol}")
        except Exception as e:
            logger.error(f"Failed to load model for {symbol}: {e}")
            raise
    
    def prepare_sequence(self, df: pd.DataFrame):
        """Prepare last sequence untuk prediction"""
        
        feature_cols = [
            'close', 'rsi_14', 'macd', 'macd_signal', 
            'ema_20', 'ema_50', 'ema_200', 'atr_14'
        ]
        
        # Drop NaN
        df = df.dropna(subset=feature_cols)
        
        if len(df) < self.sequence_length:
            logger.error(f"Not enough data: {len(df)} rows")
            return None, None
        
        # Get last sequence
        data = df[feature_cols].values[-self.sequence_length:]
        
        # Scale
        scaled_data = self.scaler.transform(data)
        
        # Reshape untuk LSTM: (1, sequence_length, features)
        X = scaled_data.reshape(1, self.sequence_length, len(feature_cols))
        
        # Get latest row untuk reference
        latest = df.iloc[-1]
        
        return X, latest
    
    def predict(self, df: pd.DataFrame):
        """
        Generate prediction
        
        Returns:
            dict dengan prediction details
        """
        
        X, latest = self.prepare_sequence(df)
        
        if X is None:
            return None
        
        # Predict
        prediction = self.model.predict(X, verbose=0)[0]
        
        # Get class dan confidence
        predicted_class = np.argmax(prediction)
        confidence = float(prediction[predicted_class])
        
        # Map ke signal
        signal_map = {0: "SELL", 1: "HOLD", 2: "BUY"}
        signal = signal_map[predicted_class]
        
        # Get prices
        current_price = float(latest['close'])
        atr = float(latest['atr_14'])
        
        # Calculate TP & SL
        if signal == "BUY":
            entry_price = current_price
            tp_price = current_price + (atr * 2.5)  # Risk:Reward 1:2.5
            sl_price = current_price - (atr * 1.0)
        elif signal == "SELL":
            entry_price = current_price
            tp_price = current_price - (atr * 2.5)
            sl_price = current_price + (atr * 1.0)
        else:  # HOLD
            entry_price = current_price
            tp_price = None
            sl_price = None
        
        # Calculate lot size (2% risk)
        # Simplified - seharusnya pakai account balance
        lot_size = 0.01
        
        result = {
            "symbol": self.symbol,
            "timeframe": "H1",
            "signal": signal,
            "confidence": round(confidence, 4),
            "entry_price": round(entry_price, 5),
            "tp_price": round(tp_price, 5) if tp_price else None,
            "sl_price": round(sl_price, 5) if sl_price else None,
            "lot_size": lot_size,
            "current_price": round(current_price, 5),
            "atr": round(atr, 5),
            "predicted_at": datetime.utcnow().isoformat(),
            "valid_until": (datetime.utcnow() + timedelta(hours=4)).isoformat(),
            "model_version": "v1.0",
            "algorithm": "LSTM"
        }
        
        # Probabilities untuk semua class
        result["probabilities"] = {
            "buy": round(float(prediction[2]), 4),
            "hold": round(float(prediction[1]), 4),
            "sell": round(float(prediction[0]), 4)
        }
        
        logger.info(f"{self.symbol}: {signal} (confidence: {confidence:.2%})")
        
        return result
