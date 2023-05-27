import functools
import talib
from jqdata import * 
from functools import lru_cache
import pandas as pd
import numpy as np
from typing import *
from dateutil.parser import parse



########################
## utility functions ###
########################


def get_index_future_code(ins):
    """ 获取指数合约code """
    future_code_list = {'A':'A8888.XDCE', 'AG':'AG8888.XSGE', 'AL':'AL8888.XSGE', 'AU':'AU8888.XSGE',
                        'B':'B8888.XDCE', 'BB':'BB8888.XDCE', 'BU':'BU8888.XSGE', 'C':'C8888.XDCE', 
                        'CF':'CF8888.XZCE', 'CS':'CS8888.XDCE', 'CU':'CU8888.XSGE', 'ER':'ER8888.XZCE', 
                        'FB':'FB8888.XDCE', 'FG':'FG8888.XZCE', 'FU':'FU8888.XSGE', 'GN':'GN8888.XZCE', 
                        'HC':'HC8888.XSGE', 'I':'I8888.XDCE', 'IC':'IC8888.CCFX', 'IF':'IF8888.CCFX', 
                        'IH':'IH8888.CCFX', 'J':'J8888.XDCE', 'JD':'JD8888.XDCE', 'JM':'JM8888.XDCE', 
                        'JR':'JR8888.XZCE', 'L':'L8888.XDCE', 'LR':'LR8888.XZCE', 'M':'M8888.XDCE', 
                        'MA':'MA8888.XZCE', 'ME':'ME8888.XZCE', 'NI':'NI8888.XSGE', 'OI':'OI8888.XZCE', 
                        'P':'P8888.XDCE', 'PB':'PB8888.XSGE', 'PM':'PM8888.XZCE', 'PP':'PP8888.XDCE', 
                        'RB':'RB8888.XSGE', 'RI':'RI8888.XZCE', 'RM':'RM8888.XZCE', 'RO':'RO8888.XZCE', 
                        'RS':'RS8888.XZCE', 'RU':'RU8888.XSGE', 'SF':'SF8888.XZCE', 'SM':'SM8888.XZCE', 
                        'SN':'SN8888.XSGE', 'SR':'SR8888.XZCE', 'T':'T8888.CCFX', 'TA':'TA8888.XZCE', 
                        'TC':'TC8888.XZCE', 'TF':'TF8888.CCFX', 'V':'V8888.XDCE', 'WH':'WH8888.XZCE', 
                        'WR':'WR8888.XSGE', 'WS':'WS8888.XZCE', 'WT':'WT8888.XZCE', 'Y':'Y8888.XDCE', 
                        'ZC':'ZC8888.XZCE', 'ZN':'ZN8888.XSGE'}
    return future_code_list[ins]


def get_main_cont_future_code(ins):
    """ 获取主力连续合约code """
    future_code_list = {'A':'A9999.XDCE', 'AG':'AG9999.XSGE', 'AL':'AL9999.XSGE', 'AU':'AU9999.XSGE',
                        'B':'B9999.XDCE', 'BB':'BB9999.XDCE', 'BU':'BU9999.XSGE', 'C':'C9999.XDCE', 
                        'CF':'CF9999.XZCE', 'CS':'CS9999.XDCE', 'CU':'CU9999.XSGE', 'ER':'ER9999.XZCE', 
                        'FB':'FB9999.XDCE', 'FG':'FG9999.XZCE', 'FU':'FU9999.XSGE', 'GN':'GN9999.XZCE', 
                        'HC':'HC9999.XSGE', 'I':'I9999.XDCE', 'IC':'IC9999.CCFX', 'IF':'IF9999.CCFX', 
                        'IH':'IH9999.CCFX', 'J':'J9999.XDCE', 'JD':'JD9999.XDCE', 'JM':'JM9999.XDCE', 
                        'JR':'JR9999.XZCE', 'L':'L9999.XDCE', 'LR':'LR9999.XZCE', 'M':'M9999.XDCE', 
                        'MA':'MA9999.XZCE', 'ME':'ME9999.XZCE', 'NI':'NI9999.XSGE', 'OI':'OI9999.XZCE', 
                        'P':'P9999.XDCE', 'PB':'PB9999.XSGE', 'PM':'PM9999.XZCE', 'PP':'PP9999.XDCE', 
                        'RB':'RB9999.XSGE', 'RI':'RI9999.XZCE', 'RM':'RM9999.XZCE', 'RO':'RO9999.XZCE', 
                        'RS':'RS9999.XZCE', 'RU':'RU9999.XSGE', 'SF':'SF9999.XZCE', 'SM':'SM9999.XZCE', 
                        'SN':'SN9999.XSGE', 'SR':'SR9999.XZCE', 'T':'T9999.CCFX', 'TA':'TA9999.XZCE', 
                        'TC':'TC9999.XZCE', 'TF':'TF9999.CCFX', 'V':'V9999.XDCE', 'WH':'WH9999.XZCE', 
                        'WR':'WR9999.XSGE', 'WS':'WS9999.XZCE', 'WT':'WT9999.XZCE', 'Y':'Y9999.XDCE', 
                        'ZC':'ZC9999.XZCE', 'ZN':'ZN9999.XSGE'}
    return future_code_list[ins]

@functools.lru_cache()
def get_future_basic_info(dom):
    """ 获取期货主合约的信息 """
    from jqdata import jy
    import re
    q = query(jy.Fut_ContractMain).filter(jy.Fut_ContractMain.ContractCode==dom.split(".")[0])
    result = jy.run_query(query_object=q).to_dict("record")
    if result:
        result = result.pop()
        min_point = re.match("(?P<value>^[0-9]+([.]{1}[0-9]+){0,1})", result["LittlestChangeUnit"]).groupdict(np.nan)["value"]
        return {"ContractUnit": result["CMValue"],
                "PriceScale": float(str(min_point)[:-1] + "1") if float(min_point) < 1 else 1,
                "MinPoint": float(min_point),
                "MinMarginRatio": result["InitialMarginRatio"]
                }
    else:
        log.error('【基础信息获取失败】code: {}'.format(dom))
        return None
    

def get_current_date(as_str=False) -> "date":
    d = get_trade_days(count=10)[-1]
    return d.strftime("%Y-%m-%d") if as_str else d


def get_prev_trading_date(prev: int = 1, as_str=False) -> "date":
    d = get_trade_days(count=prev+1)[-1-prev]
    return d.strftime("%Y-%m-%d") if as_str else d


def get_price_history(code, unit="1d", count=None, start_date=None, return_field=None):
    if start_date is not None:
        if isinstance(start_date, str):
            start_date = parse(start_date)
        current_date = get_current_date()
        count = (current_date - start_date).days

    if count is None:
        raise ValueError("Both start_date and count are None")

    df = attribute_history(code, count=count, unit=unit, fields=['open','close','high','low','volume','money'], skip_paused=True)
    if start_date is not None:
        df = df.loc[start_date:]

    if return_field is not None:
        return df[return_field]
    else:
        return df


##################
## Indicators ###
#################

class BaseIndicator:
        
    def suggest(self) -> int:
        """ 1 -> 买入 -1 -> 卖出 0 -> No Action """
        raise NotImplementedError
    
    def __repr__(self):
        return f"{self.__class__.__name__}(code={self.code})"


class MACrossIndicator(BaseIndicator):

    def __init__(self, code, unit="1d", fast_window: int=5, slow_window: int=10, ma_type=1):
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
        self.code = code
        self.unit = unit
        self.fast_window = fast_window
        self.slow_window = slow_window
        self.ma_type = ma_type

    def suggest(self) -> int:
        p_close = get_price_history(code=self.code, count=self.slow_window+5, return_field="close", unit=self.unit)
        # not enough data points
        if len(p_close) <= self.slow_window + 1:
            return 0

        slow_ma = talib.MA(p_close, self.slow_window, matype=self.ma_type)
        fast_ma = talib.MA(p_close, self.fast_window, matype=self.ma_type)

        # 快均线上穿慢均线，买入信号
        if fast_ma[-2] < slow_ma[-2] and fast_ma[-1] > slow_ma[-1]:
            return 1
        # 快均线下穿慢均线，卖出信号
        elif fast_ma[-2] > slow_ma[-2] and fast_ma[-1] < slow_ma[-1]:
            return -1
        else:
            return 0
        

###############
## Stop Loss ##
###############

class BaseStopLoss:

    def __init__(self, code, unit, side: str):
        """
        side: one of {long, short}
        """
        self.code = code
        self.unit = unit
        if side not in ('long', 'short'):
            raise ValueError("side must be one of long, short.")
        self.side = side

    def _set_initial_stop_loss(self, open_price):
        raise NotImplementedError
    
    def _update_stop_loss(self):
        # 默认止损价格不改变
        return self._stop_loss_price
    
    def update_stop_loss(self):
        # 多头的止损必须是单调递增的，空头的止损必须是单调递减的
        orig_stop_loss = self._stop_loss_price
        new_stop_loss = self._update_stop_loss()

        if self.side == "long" and new_stop_loss > orig_stop_loss:
            self._stop_loss_price = new_stop_loss
            log.info(f"【多头止损点更新】code={self.code} from={orig_stop_loss} to={new_stop_loss}")
        
        if self.side == "short" and new_stop_loss < orig_stop_loss:
            self._stop_loss_price = min(self._stop_loss_price, new_stop_loss)
            log.info(f"【空头止损点更新】code={self.code} from={orig_stop_loss} to={new_stop_loss}")

    def should_stop_loss(self, current_price) -> bool:
        if self.side == "long" and current_price < self._stop_loss_price:
            return True
        elif self.side == "short" and current_price > self._stop_loss_price:
            return True
        else:
            return False

    @property
    def stop_loss_price(self):
        return self._stop_loss_price


class ATRStopLossV1(BaseStopLoss):
    """ 一个简单的ATR止损策略：
        1. 以开仓价或者开仓价格前一天的价格作为基准价格
        2. 在基准价格的基础上，以m倍的n天ATR作为止损幅度
    """
    def __init__(self, code, unit, side,
                 m: float, n: int, 
                 base_price_type: str = "open"
                 ):
        super.__init__(code, unit, side)
        self.m = m
        self.n = n
        if base_price_type not in ("open", "prev_close", "prev_adv", "prev_disad"):
            raise ValueError(f'Base price type should be one of {("open", "prev_close", "prev_adv", "prev_disad")}')
        self.base_price_type = base_price_type

    def _set_initial_stop_loss(self, open_price):
        df = get_price_history(code=self.code, unit=self.unit, count=self.n+5)
        atr = talib.ATR(high=df['high'], low=df['low'], close=df['close'], timeperiod=self.n).values[-1]
        if pd.isna(atr):
            raise ValueError(F"品种{self.code}没有足够{self.n}天的数据来计算ATR")
        
        if self.base_price_type == "open":
            base_price = open_price
        else:
            prev_date = get_prev_trading_date(prev=1, as_str=True)
            prev_price = df.loc[prev_date]

            if self.base_price_type == "prev_close":
                base_price = prev_price["close"]
            elif base_price == "prev_adv":
                pass
            elif base_price == "prev_disad":
                pass
        
        if self.side == "long":
            self._stop_loss_price = base_price - self.m * atr
        else:
            self._stop_loss_price = base_price + self.m * atr


##############
## Trade  ###
#############

class Trade:

    def __init__(self, code, open_price, side: str, amount: float):
        self.code = code
        self.open_price = open_price
        self.side = side
        self.amount = amount

    def 

