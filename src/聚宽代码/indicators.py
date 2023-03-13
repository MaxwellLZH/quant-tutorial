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
        uint = unit or self.unit
        df = attribute_history(self.dom, count=count, unit=self.uint, fields=['open','close','high','low','volume','money'], skip_paused=True)
        if return_field is not None:
            return df[return_field]

    