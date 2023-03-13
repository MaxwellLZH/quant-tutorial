import functools
import talib
from jqdata import * 
from collections import defaultdict
from functools import lru_cache
import numpy as np
from typing import *


class Indicators:

    def __init__(self, code: str, unit="1d"):
        self.code = code
        self.unit = unit

    def get_price_history(self, count, unit=None, return_field=None):
        unit = unit or self.unit
        df = attribute_history(self.dom, count=count, unit=unit, fields=['open','close','high','low','volume','money'], skip_paused=True)
        if return_field is not None:
            return df[return_field]

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
