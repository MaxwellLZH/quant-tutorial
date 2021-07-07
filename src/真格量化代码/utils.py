# Utility functions
from PoboAPI import *


def get_days_to_expire(contract):
    """
    获得距离期货期权到期日的自然日天数
    
    Parameters
    ----------
    contract : str
        合约代码

    Returns
    -------
    n_days : int
        距离到期日的自然日天数
    """
    info = GetContractInfo(contract)
    due_date = info.get("行权到期日", info["最后交易日"])
    cur_time = GetCurrentTime()
    return (due_date - cur_time.date()).days



def get_trading_days_to_expire(contract, exchange="SHFE"):
    """
    获得距离期货期权到期日的交易日天数
    
    Parameters
    ----------
    contract : str
        合约代码

    Returns
    -------
    n_days : int
        距离到期日的交易日天数
    """
    info = GetContractInfo(contract)
    due_date = info.get("行权到期日", info["最后交易日"])
    tds = GetTradingDates(exchange, GetCurrentTime(), due_date)
    # 返回的交易日列表是包含两端日期的
    return len(tds) - 1 if tds[-1] == due_date else len(tds)



def add_days(n, curr=None):
    pass


def add_trading_days(n, curr=None):
    """获得curr时点加上n个交易日的日期
    :param n: int, 
    :param n: 
    """


def get_actively_trading_merchant_codes(exchange="SHFE", lookback=90, threshold=1e8):
    """获取指定交易所下活跃的期货品种"""
    from 

    merchant_codes = GetVarieties(exchange)
