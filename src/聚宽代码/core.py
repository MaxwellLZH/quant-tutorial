import talib
from jqdata import * 
from functools import lru_cache
import pandas as pd
import numpy as np
import re
import math
from typing import *
from dateutil.parser import parse
from copy import deepcopy
from datetime import datetime


########################
## utility functions ###
########################


def get_index_future_code(ins) -> str:
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


def get_main_cont_future_code(ins) -> str:
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


def get_future_basic_info(code):
    """ 获取期货主合约的信息 """
    from math import nan
    
    match = re.match(r"(?P<underlying_symbol>[A-Z]{1,})(?P<delivery_month>[0-9]{1,})", code)
    if not match:
        raise ValueError("未知期货标的：{}".format(code))
    
    if "9999" in code or "8888" in code:
        code = get_dominant_future(match.groupdict()["underlying_symbol"])
        match = re.match(r"(?P<underlying_symbol>[A-Z]{1,})(?P<delivery_month>[0-9]{1,})", code)
            
    if code.endswith("XZCE"):
        code = match.groupdict()["underlying_symbol"] + match.groupdict()["delivery_month"][1:]
        
    q = query(jy.Fut_ContractMain).filter(jy.Fut_ContractMain.ContractCode == code.split(".")[0])
    result = jy.run_query(query_object=q).to_dict("record")

    if result:
        result = result.pop()
        min_point_match = re.match("(?P<value>^[0-9]+([.]{1}[0-9]+){0,1})", str(result["LittlestChangeUnit"]))
        if min_point_match:
            min_point = min_point_match.groupdict(nan)["value"]
        else:
            min_point = nan
            
        return {"ContractUnit": result["CMValue"],
               "PriceScale": float(str(min_point)[:-1] + "1") if float(min_point) < 1 else 1,
               "MinPoint": float(min_point)}
    else:
        log.error('【基础信息获取失败】code: {}'.format(code))
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
    
    def set_code(self, code: str):
        self.code = code
        return self
    
    def __repr__(self):
        return f"{self.__class__.__name__}(code={self.code})"


class MACrossIndicator(BaseIndicator):

    def __init__(self, unit="1d", fast_window: int=5, slow_window: int=10, ma_type=1):
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

    def __init__(self, unit, side: str):
        """
        side: one of {long, short}
        """
        self.unit = unit
        if side not in ('long', 'short'):
            raise ValueError("side must be one of long, short.")
        self.side = side

    def _set_initial_stop_loss(self, open_price):
        raise NotImplementedError
    
    def _update_stop_loss(self):
        # 默认止损价格不改变
        return self._stop_loss_price
    
    def set_code(self, code: str):
        self.code = code
        return self

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

    def should_stop_loss(self, current_price=None) -> bool:
        if current_price is None:
            # 如果不提供current_price, 默认用上一个单位日期的close price
            current_price = get_price_history(code=self.code, unit=self.unit, count=5)["close"].values[-1]

        if self.side == "long" and current_price < self._stop_loss_price:
            return True
        elif self.side == "short" and current_price > self._stop_loss_price:
            return True
        else:
            return False
        
    def calculate_max_loss(self, current_price) -> float:
        # 计算在当前价格下，单位合约下的最大损失
        if self.side == "long":
            return max(current_price - self._stop_loss_price, 0)
        else:
            return max(self._stop_loss_price - current_price, 0)

    @property
    def stop_loss_price(self):
        return self._stop_loss_price


class ATRStopLossV1(BaseStopLoss):
    """ 一个简单的ATR止损策略：
        1. 以开仓价或者开仓价格前一天的价格作为基准价格
        2. 在基准价格的基础上，以m倍的n天ATR作为止损幅度
    """
    def __init__(self, unit, side,
                 m: float, n: int, 
                 base_price_type: str = "open"
                 ):
        super.__init__(unit, side)
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


##################################################
## Trade  
# 1. 买入价位、盈利目标、止损价位、收益风险比例
# 2. 风险管理：单笔交易和所有交易的最大可承受损失比例
# 3. 每笔交易的开仓和止损信号来源
##################################################

class Trade:

    def __init__(self, code, order_price, side: str, stop_loss: BaseStopLoss):
        self.code = code
        self.order_price = order_price
        self.side = side
        self.stopper = stop_loss.set_code(code)
        self.lots = None
        self.open_time = None

        future_info = get_future_basic_info(code)
        if future_info is None:
            raise ValueError(f"无法获取{self.code}基础信息")
        self.contract_unit = future_info["ContractUnit"]

    def calculate_maximum_lots(self, max_loss_buffer: float) -> int:
        # calculate the maximum loss for 1 unit
        max_loss_per_unit = self.stopper.calculate_max_loss(current_price=self.order_price)
        return math.floor(max_loss_buffer / (max_loss_per_unit * self.contract_unit))
    
    def calculate_maximum_loss(self, current_price: float) -> float:
        if self.lots is None:
            raise ValueError("Call Trade.execute first.")
        return self.lots * self.contract_unit * self.stopper.calculate_max_loss(current_price=current_price)

    def open_position(self, lots: int, pindex=0, close_today=False) -> int:
        """ 执行开仓的交易，返回实际开仓成功的手数 """
        # TODO: 使用限价单：https://www.joinquant.com/help/api/help#api:OrderStyle
        order = order_target(self.code, amount=lots, style=None, side=self.side, pindex=pindex, close_today=close_today)
        
        if order is not None:
            self.real_open_price = real_open_price = order.price
            self.lots = order.amount
            self.open_time = datetime.now()

            # 用实际的开仓价格重新设置止损
            self.stopper._set_initial_stop_loss(open_price=real_open_price)

            log.error(f"【开仓】code={self.code} side={self.side} lots={self.lots} real_open_price={real_open_price}")
            return order.amount
        else:
            log.error(f"【开仓失败】code={self.code} side={self.side} lots={self.lots}")
            return 0
        
    def run_daily(self, pindex=0) -> "Trade":
        """ 在开仓之后，每天更新指标 & 判断是否需要止损。 """
        
        self.stopper.update_stop_loss()
        need_close = self.stopper.should_stop_loss()

        if need_close:
            order = order_target(self.code, amount=0, style=None, side=self.side, pindex=pindex)

        assert order is not None and order.action == "close"
        log.error(f"【平仓】code={self.code} side={self.side} lots={self.lots}")

        self.lots = 0
        
        # TODO: 移仓换月
        return self


######################
# 风险管理大脑
#####################

class BaseMoneyMaker:

    def __init__(self, context,
                instruments: List[str],
                open_indicators: Union[List[BaseIndicator], Dict[str, List[BaseIndicator]]],
                stop_loss_method: Union[BaseStopLoss, Dict[str, BaseStopLoss]]
                 ):
        """
        open_indicators: A list of BaseIndicator objects or A mapping from instrument name to its own list of BaseIndicators
        stop_loss_methods: A StopLoss object or A mapping from instrument name to its own stop loss strategy
        """
        self.context = context
        self.instruments = instruments
        
        self.open_indicators: Dict[str, List[BaseIndicator]] = dict()
        self.stop_loss_method: Dict[str, BaseStopLoss] = dict()

        for ins in instruments:
            # 信号默认在连续合约上生成
            cont_code = get_main_cont_future_code(ins)
            if isinstance(open_indicators, list):
                self.open_indicators[ins] = [deepcopy(i).set_code(cont_code) for i in open_indicators]
            else:
                self.open_indicators[ins] = open_indicators[ins]

            # 止损默认也基于连续合约
            if isinstance(stop_loss_method, dict):
                self.stop_loss_method[ins] = stop_loss_method[ins]
            else:
                self.stop_loss_method[ins] = deepcopy(stop_loss_method).set_code(cont_code)
            
        self.trade_book: Dict[str, List[Trade]] = dict()   # mapping from instrument name to all the trades

    def _assign_instrument_weight(self, ins) -> float:
        # 为每个品种分配可交易金额的权重，如不可交易则返回0
        return 1

    def calculate_instrument_weight(self) -> Dict[str, float]:
        # 计算每个品种的交易金额占比
        weights = {}
        for ins in self.instruments:
            if self.check_ins_tradable(ins):
                w = self._assign_instrument_weight(ins)
                if w > 0:
                    weights[ins] = w
        # normalize
        norm = sum(weights.values())
        return {k: v / norm for k, v in weights.items()}

    def check_ins_tradable(self, ins) -> bool:
        return True

    def get_total_long_position(self, ins) -> int:
        # 获取某个期货品种的多头总数
        trades: List[Trade] = self.trade_book.get(ins, list())
        return sum([t.lots for t in trades if t.side == "long"])
    
    def get_total_short_position(self, ins) -> int:
        # 获取某个期货品种的空头总数
        trades: List[Trade] = self.trade_book.get(ins, list())
        return sum([t.lots for t in trades if t.side == "short"])

    def run_daily(self):
        for ins, weight in self.calculate_instrument_weight().items():
            # 现有持仓的止损和移仓换月
            if ins in self.trade_book:
                for trade in self.trade_book[ins]:
                    if trade.lots > 0:
                        trade = trade.run_daily()                    
                
            # 在连续合约上产生交易信号
            ins_cont_code = get_main_cont_future_code(ins)
            
            indicators = self.open_indicators[ins]
            signals = [i.suggest() for i in indicators]
            cnt_buy_signal, cnt_sell_signal = sum(i==1 for i in signals), sum(i==-1 for i in signals)

            # 有买入信号 & 当前无空头
            if cnt_buy_signal > 0 and self.get_total_short_position(ins) == 0:
                pass

            



# for ins in g.instruments:
#     RealFuture = get_dominant_future(ins)
#     if RealFuture == '':
#         pass


# 移仓模块：当主力合约更换时，平当前持仓，更换为最新主力合约        
# def replace_old_futures(context,ins,dom):
    
#     LastFuture = g.MappingReal[ins]
    
#     if LastFuture in context.portfolio.long_positions.keys():
#         lots_long = context.portfolio.long_positions[LastFuture].total_amount
#         order_target(LastFuture,0,side='long')
#         order_target(dom,lots_long,side='long')
#         print('主力合约更换，平多仓换新仓')
    
#     if LastFuture in context.portfolio.short_positions.keys():
#         lots_short = context.portfolio.short_positions[LastFuture].total_amount
#         order_target(LastFuture,0,side='short')
#         order_target(dom,lots_short,side='short')
#         print('主力合约更换，平空仓换新仓')


# 获取交易手数函数（ATR倒数头寸）
def get_lots(cash,symbol):
    RealFuture = get_dominant_future(symbol)
    # 获取价格list
    Price_dict = attribute_history(RealFuture,10,'1d',['open'])
    # 如果没有数据，返回
    if len(Price_dict) == 0: 
        return
    else:
        open_future = Price_dict.iloc[-1]
    # 返回手数
    if RealFuture in g.ATR.keys():
        return cash*0.02/(g.ATR[RealFuture]*future_basic_info(RealFuture)['ContractUnit'])
    else:# 函数运行之初会出现没将future写入ATR字典当中的情况
        return cash*0.0001/future_basic_info(RealFuture)['ContractUnit']