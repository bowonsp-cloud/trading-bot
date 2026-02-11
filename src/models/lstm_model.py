"""
LSTM Model untuk prediksi trading
"""

import numpy as np
import pandas as pd
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.preprocessing import MinMaxScaler
import joblib
import logging

logger = logging.getLogger(__name__)


class TradingLSTM:
    """LSTM model untuk prediksi BUY/SELL/HOLD"""
    
    def __init__(self, sequence_length=60):
        self.sequence_length = sequence_length
        self.model = None
        self.scaler = MinMaxScaler()
        
    def build_model(self, input_shape):
        """Build LSTM architecture"""
        model = Sequential([
            LSTM(128, return_sequences=True, input_shape=input_shape),
            Dropout(0.3),
            LSTM(64, return_sequences=True),
            Dropout(0.3),
            LSTM(32),
            Dropout(0.3),
            Dense(64, activation='relu'),
            Dropout(0.2),
            Dense(32, activation='relu'),
            Dense(3, activation='softmax')  # BUY, HOLD, SELL
        ])
        
        model.compile(
            optimizer='adam',
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        self.model = model
        return model
    
    def prepare_data(self, df: pd.DataFrame):
        """Prepare data untuk training"""
        
        # Features untuk training
        feature_cols = [
            'close', 'rsi_14', 'macd', 'macd_signal', 
            'ema_20', 'ema_50', 'ema_200', 'atr_14'
        ]
        
        # Drop rows dengan NaN
        df = df.dropna(subset=feature_cols)
        
        if len(df) < self.sequence_length + 10:
            logger.error(f"Not enough data: {len(df)} rows")
            return None, None
        
        # Extract features
        data = df[feature_cols].values
        
        # Scale data
        scaled_data = self.scaler.fit_transform(data)
        
        # Create sequences
        X, y = [], []
        
        for i in range(self.sequence_length, len(scaled_data)):
            X.append(scaled_data[i-self.sequence_length:i])
            
            # Label: BUY (2) if price up, SELL (0) if price down, HOLD (1) otherwise
            price_change = (df['close'].iloc[i] - df['close'].iloc[i-1]) / df['close'].iloc[i-1]
            
            if price_change > 0.001:  # > 0.1% = BUY
                label = 2
            elif price_change < -0.001:  # < -0.1% = SELL
                label = 0
            else:  # HOLD
                label = 1
            
            y.append(label)
        
        X = np.array(X)
        y = np.array(y)
        
        logger.info(f"Prepared {len(X)} sequences")
        logger.info(f"  BUY: {np.sum(y == 2)}, HOLD: {np.sum(y == 1)}, SELL: {np.sum(y == 0)}")
        
        return X, y
    
    def train(self, X_train, y_train, X_val, y_val, epochs=100):
        """Train model"""
        
        if self.model is None:
            self.build_model((X_train.shape[1], X_train.shape[2]))
        
        early_stop = EarlyStopping(
            monitor='val_loss', 
            patience=10, 
            restore_best_weights=True
        )
        
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=32,
            callbacks=[early_stop],
            verbose=1
        )
        
        return history
    
    def predict(self, X):
        """Predict with probabilities"""
        if self.model is None:
            raise ValueError("Model not trained yet")
        
        predictions = self.model.predict(X, verbose=0)
        return predictions
    
    def save(self, model_path, scaler_path):
        """Save model and scaler"""
        self.model.save(model_path)
        joblib.dump(self.scaler, scaler_path)
        logger.info(f"Model saved: {model_path}")
        logger.info(f"Scaler saved: {scaler_path}")
    
    def load(self, model_path, scaler_path):
        """Load model and scaler"""
        from tensorflow.keras.models import load_model
        self.model = load_model(model_path)
        self.scaler = joblib.load(scaler_path)
        logger.info(f"Model loaded: {model_path}")
