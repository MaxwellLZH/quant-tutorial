import functools
import talib
from jqdata import * 
from collections import defaultdict
from functools import lru_cache
import numpy as np
from typing import *
from dateutil.parser import parse


class Indicator:

    def __init__(self, code: str, unit="1d"):
        self.code = code
        self.unit = unit
        
    def __repr__(self):
        return f"Indicator(code={self.code})"

    def get_price_history(self, count=None, start_date=None, unit=None, return_field=None):
        unit = unit or self.unit

        if start_date is not None:
            if isinstance(start_date, str):
                start_date = parse(start_date)
            current_date = self.get_current_date()
            count = (current_date - start_date).days

        if count is None:
            raise ValueError("Both start_date and count are None")

        df = attribute_history(self.code, count=count, unit=unit, fields=['open','close','high','low','volume','money'], skip_paused=True)
        if start_date is not None:
            df = df.loc[start_date:]

        if return_field is not None:
            return df[return_field]
        else:
            return df
        
    def get_current_date(self):
        return self.get_price_history(count=10).index[-1]

    def ma(self, window: int, ma_type: int = 1):
        """ 
        {0: 'Simple Moving Average',
        1: 'Exponential Moving Average',
        2: 'Weighted Moving Average',
        3: 'Double Exponential Moving Average',
        4: 'Triple Exponential Moving Average',
        5: 'Triangular Moving Average',
        6: 'Kaufman Adaptive Moving Average',
        7: 'MESA Adaptive Moving Average',
        8: 'Triple Generalized Double Exponential Moving Average'}
        """
        df_close = self.get_price_history(count=window+10, return_field="close")
        return talib.MA(df_close, window, matype=ma_type).values[-1]
    
    def sip(self, start_date, position):
        df = self.get_price_history(start_date=start_date)
        if position == "long":
            return df['high'].max()
        elif position == "short":
            return df['low'].min()
        else:
            raise ValueError("Only long and short is supported for position keyword.")

    def sip(self, start_date, position):
        df = self.get_price_history(start_date=start_date)
        if position == "long":
            return df['close'].max()
        elif position == "short":
            return df['close'].min()
        else:
            raise ValueError("Only long and short is supported for position keyword.")
