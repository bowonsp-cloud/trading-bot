"""
Supabase client
"""

from supabase import create_client, Client
import pandas as pd
import os
from dotenv import load_dotenv
import logging
from datetime import datetime

load_dotenv()
logger = logging.getLogger(__name__)


class SupabaseClient:
    
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY")
        
        if not url or not key:
            raise ValueError("SUPABASE_URL dan SUPABASE_SERVICE_KEY required")
        
        self.client: Client = create_client(url, key)
    
    def get_latest_timestamp(self, symbol: str, timeframe: str = 'H1'):
        try:
            response = self.client.table("ohlc_data").select("timestamp").eq(
                "symbol", symbol
            ).eq(
                "timeframe", timeframe
            ).order("timestamp", desc=True).limit(1).execute()
            
            if response.data:
                # FIX: Convert to timezone-naive datetime
                ts = pd.to_datetime(response.data[0]['timestamp'])
                # Remove timezone info to make it naive
                if ts.tz is not None:
                    ts = ts.tz_localize(None)
                return ts
            return None
        except Exception as e:
            logger.error(f"Error: {e}")
            return None
    
    def upload_ohlc(self, df: pd.DataFrame, symbol: str, timeframe: str = 'H1'):
        if df.empty:
            return 0
        
        df = df.copy()
        df['symbol'] = symbol
        df['timeframe'] = timeframe
        
        # FIX: Make sure timestamp is timezone-naive before converting to string
        if hasattr(df['timestamp'].dtype, 'tz') and df['timestamp'].dtype.tz is not None:
            df['timestamp'] = df['timestamp'].dt.tz_localize(None)
        
        df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        records = df.to_dict('records')
        
        try:
            self.client.table("ohlc_data").upsert(
                records,
                on_conflict='symbol,timeframe,timestamp'
            ).execute()
            
            return len(records)
        except Exception as e:
            logger.error(f"Upload error: {e}")
            return 0
    
    def log_activity(self, level, module, action, message, details=None):
        try:
            log_entry = {
                'log_level': level,
                'module': module,
                'action': action,
                'message': message,
                'details': details,
                'timestamp': datetime.utcnow().isoformat()
            }
            self.client.table("system_logs").insert(log_entry).execute()
        except:
            pass
