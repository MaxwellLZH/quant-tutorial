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
    """
    增减自然日

    Parameters
    ----------
    n : int
        增减的自然日天数，可以为负

    curr: datetime, 默认为当天日期
        日期

    Returns
    -------
    dt : datetime
        调整后的日期
    """
    # from dateutils.relativedelta import relativedelta
    from datetime import timedelta
    curr = curr or GetCurrentTime().date()
    return curr + timedelta(days=n)


def add_trading_days(n, curr=None, exchange="SHFE"):
    """
    增减交易日

    Parameters
    ----------
    n : int
        增减的交易日天数，可以为负

    curr: datetime, 默认为当天日期
        日期

    exchange: str, 默认为SHFE
        交易所代码

    Returns
    -------
    dt : datetime
        调整后的日期
    """
    from datetime import timedelta
    import math

    n = int(n)
    curr = curr or GetCurrentTime().date()
    dt = curr + timedelta(math.floor(n * 1.7))
    if n < 0:
        tds = GetTradingDates(exchange, dt, curr)
    else:
        tds = GetTradingDates(exchange, curr, dt)
    return tds[n]


def get_actively_trading_merchant_codes(exchange="SHFE", lookback=90, threshold=1e8):
    """
    获取指定交易所下活跃度超过一定阈值的期货代码列表

    Parameters
    ----------
    exchange: str, 默认为SHFE
        交易所代码

    lookback: int, 默认90天
        观察期时长

    threshold: float, 默认为1e8
        活跃度阈值

    Returns
    -------
    codes : List[str]
        含期货代码的列表
    """
    merchant_codes = GetVarieties(exchange)
