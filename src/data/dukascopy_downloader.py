"""
Download OHLC H1 data dari Dukascopy
"""

import requests
import pandas as pd
import struct
import lzma
from datetime import datetime, timedelta
from typing import Optional
import logging
import time

logger = logging.getLogger(__name__)


class DukascopyH1Downloader:
    """Download H1 OHLC data dari Dukascopy"""
    
    BASE_URL = "https://datafeed.dukascopy.com/datafeed"
    
    SYMBOLS = {
        'EURUSD': 'EURUSD',
        'GBPUSD': 'GBPUSD', 
        'USDJPY': 'USDJPY',
        'AUDUSD': 'AUDUSD',
        'USDCHF': 'USDCHF',
        'XAUUSD': 'XAUUSD',
    }
    
    def __init__(self, symbol: str):
        if symbol not in self.SYMBOLS:
            raise ValueError(f"Symbol {symbol} tidak didukung")
        
        self.symbol = symbol
        self.dukascopy_symbol = self.SYMBOLS[symbol]
        self.price_divisor = 1000 if 'JPY' in symbol else 100000
    
    def _get_bi5_url(self, dt: datetime) -> str:
        year = dt.year
        month = dt.month - 1
        day = dt.day
        hour = dt.hour
        
        url = (
            f"{self.BASE_URL}/{self.dukascopy_symbol}/"
            f"{year}/{month:02d}/{day:02d}/{hour:02d}h_ticks.bi5"
        )
        return url
    
    def _decompress_bi5(self, data: bytes) -> Optional[bytes]:
    """Decompress LZMA compressed bi5 data"""
    try:
        return lzma.decompress(data)  # ← 4 spaces indent
    except lzma.LZMAError as e:
        # File corrupt dari Dukascopy - skip
        logger.warning(f"Corrupt data (skip): {e}")
        return None
    except Exception as e:
        logger.error(f"Decompression error: {e}")
        return None
    
    def _parse_ticks_to_ohlc(self, data: bytes, hour_start: datetime) -> Optional[dict]:
        if not data or len(data) == 0:
            return None
        
        chunk_size = 20
        num_ticks = len(data) // chunk_size
        
        if num_ticks == 0:
            return None
        
        prices = []
        volumes = []
        
        for i in range(num_ticks):
            offset = i * chunk_size
            chunk = data[offset:offset + chunk_size]
            
            if len(chunk) < chunk_size:
                break
            
            try:
                tick_time, ask, bid, ask_vol, bid_vol = struct.unpack('>5i', chunk)
                mid_price = (ask + bid) / 2 / self.price_divisor
                prices.append(mid_price)
                volumes.append(bid_vol + ask_vol)
            except struct.error:
                continue
        
        if not prices:
            return None
        
        ohlc = {
            'timestamp': hour_start,
            'open': round(prices[0], 5),
            'high': round(max(prices), 5),
            'low': round(min(prices), 5),
            'close': round(prices[-1], 5),
            'volume': sum(volumes)
        }
        
        return ohlc
    
    def download_hour(self, dt: datetime) -> Optional[dict]:
        hour_start = dt.replace(minute=0, second=0, microsecond=0)
        url = self._get_bi5_url(hour_start)
        
        try:
            logger.info(f"Downloading: {self.symbol} {hour_start}")
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                decompressed = self._decompress_bi5(response.content)
                if decompressed:
                    return self._parse_ticks_to_ohlc(decompressed, hour_start)
            
            return None
        
        except Exception as e:
            logger.error(f"Error: {e}")
            return None
    
    def download_range(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        data_list = []
        current = start_date.replace(minute=0, second=0, microsecond=0)
        end = end_date.replace(minute=0, second=0, microsecond=0)
        
        while current <= end:
            ohlc = self.download_hour(current)
            if ohlc:
                ohlc['symbol'] = self.symbol
                data_list.append(ohlc)
            
            current += timedelta(hours=1)
            time.sleep(0.5)
        
        if data_list:
            df = pd.DataFrame(data_list)
            df = df[['symbol', 'timestamp', 'open', 'high', 'low', 'close', 'volume']]
            df.sort_values('timestamp', inplace=True)
            return df
        
        return pd.DataFrame()
