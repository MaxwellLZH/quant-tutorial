# 导入函数库
from jqdata import *
import random

from collections import defaultdict
import functools
from functools import lru_cache
import numpy as np
from typing import *


@functools.lru_cache()
def get_future_basic_info(dom):
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


class Instrument:

    def __init__(self, ins, context, unit='1d'):
        self.ins = ins
        self.context = context
        self.unit = unit
        self.params = {}

    @property
    def long_positions(self) -> Dict[str, float]:
        codes = get_future_contracts(self.ins)
        long_positions = self.context.subportfolios[0].long_positions
        output = {}
        for code in codes:
            if code in long_positions:
                amt = long_positions[code].total_amount
                if amt > 0:
                    output[code] = amt
        return output
    
    @property
    def short_positions(self) -> Dict[str, float]:
        codes = get_future_contracts(self.ins)
        short_positions = self.context.subportfolios[0].short_positions
        output = {}
        for code in codes:
            if code in short_positions:
                amt = short_positions[code].total_amount
                if amt > 0:
                    output[code] = amt
        return output
        
    @property
    def dom(self):
        return get_dominant_future(self.ins)

    @property
    def idx(self):
        return get_index_future_code(self.ins)

    @property
    def contract_unit(self):
        future_contract_size = {'A':10, 'AG':15, 'AL':5, 'AU':1000,
                        'B':10, 'BB':500, 'BU':10, 'C':10, 
                        'CF':5, 'CS':10, 'CU':5, 'ER':10, 
                        'FB':500, 'FG':20, 'FU':50, 'GN':10, 
                        'HC':10, 'I':100, 'IC':200, 'IF':300, 
                        'IH':300, 'J':100, 'JD':5, 'JM':60, 
                        'JR':20, 'L':5, 'LR':10, 'M':10, 
                        'MA':10, 'ME':10, 'NI':1, 'OI':10, 
                        'P':10, 'PB':5, 'PM':50, 'PP':5, 
                        'RB':10, 'RI':20, 'RM':10, 'RO':10, 
                        'RS':10, 'RU':10, 'SF':5, 'SM':5, 
                        'SN':1, 'SR':10, 'T':10000, 'TA':5, 
                        'TC':100, 'TF':10000, 'V':5, 'WH':20, 
                        'WR':10, 'WS':50, 'WT':10, 'Y':10, 
                        'ZC':100, 'ZN':5}
        info = get_future_basic_info(self.dom)
        if info is not None:
            contract_size = info['ContractUnit']
            return contract_size
        else:
            contract_size = future_contract_size[self.ins]

    def __repr__(self):
        return "Instrument({})".format(self.ins)

    ####################################################
    ## explicit API for setting and getting attribute ##
    ####################################################

    def set(self, key, value):
        self.params[key] = value

    def get(self, key, default="error"):
        if default == "error":
            return self.params[key]
        else:
            return self.params.get(key, default)

    #######################
    ## price information ##
    #######################

    def get_price_idx(self, count, unit=None, fields=['open','close','high','low','volume','money'],skip_paused=True):
        unit = unit or self.unit
        return attribute_history(self.idx, count=count, unit=unit, fields=fields, skip_paused=skip_paused)

    def get_price_dom(self, count, unit=None, fields=['open','close','high','low','volume','money'],skip_paused=True):
        unit = unit or self.unit
        return attribute_history(self.dom, count=count, unit=unit, fields=fields, skip_paused=skip_paused)

    @property
    def last_close_price_idx(self):
        return attribute_history(self.idx, count=1, unit=self.unit, fields=['close'])['close'][-1]

    @property
    def last_close_price_dom(self):
        return attribute_history(self.dom, count=1, unit=self.unit, fields=['close'])['close'][-1]

    ####################
    ## trading orders ##
    ####################

    def build_target_long_position(self, amount, code=None, pindex=0, close_today=False):
        code = code or self.dom
        order = order_target(code, amount=amount, style=None, side='long', pindex=pindex, close_today=close_today)

        if order is not None:
            if order.action == 'open':
                # 开仓是没有浮盈浮亏的，所以不需要记录
                log.error(f"【多头开仓】code='{code}', amount={order.amount}, price={order.price}")
            elif order.action == 'close':
                avg_cost = self.get_avg_cost_long_position(code=code, pindex=pindex)
                # 平仓需要计算浮盈浮亏
                price = order.price
                earnings = (price - avg_cost) * order.amount * self.contract_unit
                log.error(f"【多头平仓】code='{code}', amount={order.amount}, price={order.price}, avg_cost={avg_cost}, earnings={earnings}")
            else:
                raise ValueError('Order type not supported: {}'.format(order.action))
            return order
        else:
            log.error('【多头开仓失败】code: {} amount: {}'.format(code, amount))
            return None

    def build_target_short_position(self, amount, code=None, pindex=0, close_today=False):
        code = code or self.dom
        order = order_target(code, amount=amount, style=None, side='short', pindex=pindex, close_today=close_today)
        
        if order is not None:
            if order.action == 'open':
                # 开仓是没有浮盈浮亏的，所以不需要记录
                log.error(f"【空头开仓】code='{code}', amount={order.amount}, price={order.price}")
            elif order.action == 'close':
                avg_cost = self.get_avg_cost_short_position(code=code, pindex=pindex)
                # 平仓需要计算浮盈浮亏
                price = order.price
                earnings = (avg_cost - price) * order.amount * self.contract_unit
                log.error(f"【空头平仓】code='{code}', amount={order.amount}, price={order.price}, avg_cost={avg_cost}, earnings={earnings}")
            else:
                raise ValueError('Order type not supported: {}'.format(order.action))
            return order
        else:
            log.error('【空头开仓失败】code: {} amount: {}'.format(code, amount))
            return None

    def close_long_position(self, code=None):
        code = code or self.dom
        return self.build_target_long_position(amount=0, code=code)

    def close_short_position(self, code=None):
        code = code or self.dom
        return self.build_target_short_position(amount=0, code=code)

    def close_all_long_positions(self):
        for code, lots in self.long_positions.items():
            if lots > 0:
                self.close_long_position(code=code)

    def close_all_short_positions(self):
        for code, lots in self.short_positions.items():
            if lots > 0:
                self.close_short_position(code=code)

    def get_current_long_position(self, code=None, pindex=0):
        return self.long_positions.get(code, 0)

    def get_current_short_position(self, code=None, pindex=0):
        return self.short_positions.get(code, 0)

    def get_current_long_short_position(self, code=None, pindex=0):
        long_pos = self.get_current_long_position(code=code, pindex=pindex)
        short_pos = self.get_current_short_position(code=code, pindex=pindex)
        return long_pos, short_pos

    ###############################
    ## get position information ###
    ###############################

    def _get_position_info(self, field, side='long', code=None, pindex=0):
        code = code or self.dom
        if side == 'long':
            portfolio = self.context.subportfolios[pindex].long_positions
        else:
            portfolio = self.context.subportfolios[pindex].short_positions
        
        if code not in portfolio.keys():
            return None
        else:
            return portfolio[code].__getattribute__(field)

    def get_avg_cost_long_position(self, code=None, pindex=0):
        return self._get_position_info(field='avg_cost', side='long', code=code, pindex=pindex)

    def get_avg_cost_short_position(self, code=None, pindex=0):
        return self._get_position_info(field='avg_cost', side='short', code=code, pindex=pindex)
    
    def get_value_long_position(self, code=None, pindex=0):
        return self._get_position_info(field='value', side='long', code=code, pindex=pindex)

    def get_value_short_position(self, code=None, pindex=0):
        return self._get_position_info(field='value', side='short', code=code, pindex=pindex)

    def get_price_long_position(self, code=None, pindex=0):
        return self._get_position_info(field='price', side='long', code=code, pindex=pindex)
    
    def get_price_short_position(self, code=None, pindex=0):
        return self._get_position_info(field='price', side='short', code=code, pindex=pindex)

    def get_earnings_long_position(self, code=None, pindex=0):
        cost = self.get_avg_cost_long_position(code=code, pindex=pindex)
        price = self.get_price_long_position(code=code, pindex=pindex)
        pos = self.get_current_long_position(code=code, pindex=pindex)
        return (price - cost) * pos * self.contract_unit

    def get_earnings_short_position(self, code=None, pindex=0):
        cost = self.get_avg_cost_short_position(code=code, pindex=pindex)
        price = self.get_price_short_position(code=code, pindex=pindex)
        pos = self.get_current_short_position(code=code, pindex=pindex)
        return (cost - price) * pos * self.contract_unit

    #######################
    ## Utility functions ##
    #######################

    def move_position_to_dominant_contract(self, pindex=0):
        """ 移仓模块：当主力合约更换时，平当前持仓，更换为最新主力合约 """
        dom = self.dom

        long_positions = [(k, v) for k, v in self.long_positions.items() if v > 0]
        for code, lots in long_positions:
            if lots > 0 and code != dom:
                # double check
                lots_true = self.get_current_long_position(code=code, pindex=pindex)
                # 如果出现过强制平仓，那么会出现仓位和Instrument计算的long\short positions不一致
                self.long_positions[code] = lots_true

                self.close_long_position(code=code)
                self.build_target_long_position(amount=lots, code=dom)
                log.error("【移仓换月-多头】from='{}', to='{}', amount={}".format(code, dom, lots_true))

        short_positions = [(k, v) for k, v in self.short_positions.items() if v > 0]
        for code, lots in short_positions:
            if lots > 0 and code != dom:
                # double check
                lots_true = self.get_current_short_position(code=code, pindex=pindex)
                # 如果出现过强制平仓，那么会出现仓位和Instrument计算的long\short positions不一致
                
                self.short_positions[code] = lots_true

                self.close_short_position(code=code)
                self.build_target_short_position(amount=lots, code=dom)              
                log.error("【移仓换月-空头】from='{}', to='{}', amount='{}'".format(code, dom, lots_true))

    @staticmethod
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





## 初始化函数，设定基准等等
def initialize(context):
    set_info(context)
    # 设定沪深300作为基准
    set_benchmark('000300.XSHG')
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    # 过滤掉order系列API产生的比error级别低的log
    # log.set_level('order', 'error')
    # 输出内容到日志 log.info()
    log.info('初始函数开始运行且全局只运行一次')

    ### 期货相关设定 ###
    # 设定账户为金融账户
    set_subportfolios([SubPortfolioConfig(cash=context.portfolio.starting_cash, type='index_futures')])
    # 期货类每笔交易时的手续费是：买入时万分之0.23,卖出时万分之0.23,平今仓为万分之23
    set_order_cost(OrderCost(open_commission=0.000023, close_commission=0.000023,close_today_commission=0.0023), type='index_futures')
    # 设定保证金比例
    set_option('futures_margin_rate', 0.15)

    # 设置期货交易的滑点
    set_slippage(StepRelatedSlippage(2))
    # 运行函数（reference_security为运行时间的参考标的；传入的标的只做种类区分，因此传入'IF8888.CCFX'或'IH1602.CCFX'是一样的）
    # 注意：before_open/open/close/after_close等相对时间不可用于有夜盘的交易品种，有夜盘的交易品种请指定绝对时间（如9：30）
      # 开盘前运行
    run_daily( before_market_open, time='09:00', reference_security='IF8888.CCFX')
      # 开盘时运行
    run_daily( market_open, time='09:30', reference_security='IF8888.CCFX')
      # 收盘后运行
    run_daily( after_market_close, time='15:30', reference_security='IF8888.CCFX')


def set_info(context):
    g.ins = Instrument(ins="AG", context=context)

## 开盘前运行函数
def before_market_open(context):
    # 输出运行时间
    log.info('函数运行时间(before_market_open)：'+str(context.current_dt.time()))

## 开盘时运行函数
def market_open(context):
    ins = g.ins
    lst_amount = [5, 10, 20, 30]

    if random.random() < 0.5:
        ins.build_target_long_position(amount=random.choice(lst_amount))
    
    if random.random() < 0.3:
        ins.build_target_short_position(amount=random.choice(lst_amount))

    if random.random() < 0.1:
        ins.close_all_long_positions()
    
    if random.random() < 0.1:
        ins.close_all_short_positions()


## 收盘后运行函数
def after_market_close(context):
    log.info(str('函数运行时间(after_market_close):'+str(context.current_dt.time())))
    # 得到当天所有成交记录
    trades = get_trades()
    for _trade in trades.values():
        log.info('成交记录：'+str(_trade))
    log.info('一天结束')
    log.info('##############################################################')

    ins: Instrument = g.ins
    
    log.info("long positions: {}".format(ins.long_positions))
    log.info("short positions: {}".format(ins.short_positions))

########################## 获取期货合约信息，请保留 #################################
# 获取金融期货合约到期日
def get_CCFX_end_date(future_code):
    # 获取金融期货合约到期日
    return get_security_info(future_code).end_date

