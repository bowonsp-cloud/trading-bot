"""
Configuration
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    SYMBOLS = os.getenv("SYMBOLS", "EURUSD,GBPUSD,XAUUSD").split(",")
    LOOKBACK_HOURS = int(os.getenv("LOOKBACK_HOURS", "720"))
    
    @classmethod
    def validate(cls):
        if not cls.SUPABASE_URL or not cls.SUPABASE_SERVICE_KEY:
            raise ValueError("Supabase credentials required")
        return True


config = Config()
