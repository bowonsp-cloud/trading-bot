"""
Configuration management
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration"""
    
    # Supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    
    # Trading
    SYMBOLS = os.getenv("SYMBOLS", "EURUSD,GBPUSD,XAUUSD").split(",")
    SYMBOLS = [s.strip() for s in SYMBOLS]
    
    # Data
    LOOKBACK_HOURS = int(os.getenv("LOOKBACK_HOURS", "720"))
    TIMEFRAME = "H1"
    
    # Model
    SEQUENCE_LENGTH = int(os.getenv("SEQUENCE_LENGTH", "60"))
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", "32"))
    EPOCHS = int(os.getenv("EPOCHS", "100"))
    MIN_CONFIDENCE = float(os.getenv("MIN_CONFIDENCE", "0.70"))  # ← TAMBAHKAN INI
    
    @classmethod
    def validate(cls):
        """Validate configuration"""
        if not cls.SUPABASE_URL:
            raise ValueError("SUPABASE_URL is required")
        if not cls.SUPABASE_SERVICE_KEY:
            raise ValueError("SUPABASE_SERVICE_KEY is required")
        
        return True


# Create singleton instance
config = Config()
