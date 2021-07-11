from PoboAPI import *
import datetime
import numpy as np


# 重置参数
def reset():
    # 每次交易unit数目
    g.unit = 0
    # 加仓次数
    g.add_time = 0
    # 持仓状态
    g.position = 0


def check_break(price_list, price, T):
    up = max(price_list[1][-T - 1 : -2])
    down = min(price_list[2][-T - 1 : -2])
    if price > up:
        return 1
    elif price < down:
        return -1
    else:
        return 0


def get_next_signal(price, last_price, ATR, position):  # 加仓或止损
    # 多头加仓或空头加仓
    if (price >= last_price + 0.5 * ATR and position == 1) or (
        price <= last_price - 0.5 * ATR and position == -1
    ):
        return 1
    # 多头止损或空头止损
    elif (price <= last_price - 2 * ATR and position == 1) or (
        price >= last_price + 2 * ATR and position == -1
    ):
        return -1
    else:
        return 0


def get_unit(asset, ATR, symbol):
    future_coef_list = {"cu": 5}
    return int((asset * 0.01 / ATR) / future_coef_list[symbol])


# 开始事件，用于初始化一些参数
def OnStart(context):
    log.info("I'm starting...")
    # 设置唐奇安通道时间窗口
    g.window = 20
    # 最大unit数目
    g.limit_unit = 6
    # 每次交易unit数目
    g.unit = 0
    # 加仓次数
    g.add_time = 0
    # 持仓状态，设定持空仓时为-1，持多仓时为1
    g.position = 0
    # 最近一次交易的合约
    g.last_code = None
    # 上一次交易的价格
    g.last_price = 0
    # 合约
    g.future_index = "cu"
    # 登录交易账号，需在主页用户管理中设置账号，并把期货测试替换成您的账户名称
    context.myacc = None
    if "回测期货" in context.accounts:
        print("登录交易账号[回测期货]")
        if context.accounts["回测期货"].Login():
            context.myacc = context.accounts["回测期货"]


def OnMarketQuotationInitialEx(context, exchange, daynight):
    if exchange != "SHFE":
        return
    # 获取主力合约
    g.code = GetMainContract("SHFE", "cu", 20)
    # 订阅K线数据，用于驱动OnBar事件
    SubscribeBar(g.code, BarType.Day)


# 实时行情事件，当有新行情出现时调用该事件Ex
def OnBar(context, code, bartype):

    # 取得当前价格
    dyndata = GetQuote(g.code)
    current_price = dyndata.now

    option = PBObj()
    if g.last_code:
        option.contract = g.last_code
        option.buysellflag = "1"
        currentBalance = context.myacc.GetPositions(option)
        if currentBalance:
            g.sellpos = currentBalance[0].volume
        option.buysellflag = "0"
        currentBalance = context.myacc.GetPositions(option)
        if currentBalance:
            g.buypos = currentBalance[0].volume

    # 如果期货标的改变，重置参数
    if g.last_code == None:
        g.last_code = g.code
    elif g.last_code != g.code:
        if g.position == -1:
            # 平空
            QuickInsertOrder(
                context.myacc, g.last_code, "buy", "close", current_price, g.sellpos
            )
            g.position = 0
        elif g.position == 1:
            # 平多
            QuickInsertOrder(
                context.myacc, g.last_code, "sell", "close", current_price, g.buypos
            )
            g.position = 0
        g.last_code = g.code
        reset()
        log.info("主力合约改变，平仓！")

    # 获取最近20天的开高低收价格列表
    price_list = GetHisDataByField2(
        g.code,
        ["close", "high", "low"],
        BarType.Day,
        end_date=GetCurrentTime(),
        count=g.window + 1,
    )

    # 如果没有数据，返回
    if len(price_list) == 0:
        return
    close_price = price_list[0][-1]

    # 创建ATR对象
    ATR_list = CreateIndicator("ATR")
    # 设定参数
    param = {"N": 20}
    ATR_list.SetParameter(param)
    # 设定要计算ATR的品种和K线周期
    if ATR_list:
        ATR_list.Attach(g.code, BarType.Day)
    # 开始计算
    ATR_list.Calc()
    ATR_array = ATR_list.GetValue("ATR")
    # 选取最新的ATR值
    ATR = ATR_array[-1]

    if g.position != 0:
        signal = get_next_signal(close_price, g.last_price, ATR, g.position)
        # 判断加仓且持仓没有达到上限
        if signal == 1 and g.add_time < g.limit_unit:
            # 计算加仓量
            g.unit = get_unit(
                context.myacc.AccountBalance.AssetsBalance, ATR, g.future_index
            )
            # 多头加仓
            if g.position == 1:
                QuickInsertOrder(
                    context.myacc, g.code, "buy", "open", current_price, g.unit
                )
                # 添加止损单，当价格向下突破到一定程度时就平仓
                InsertAbsStopLossPosition(
                    context.myacc, g.code, "buy", current_price * 0.95, g.unit
                )
                log.info("多头加仓成功:" + str(GetCurrentTime()) + str(g.code) + str(g.unit))
                # 更新交易价格
                g.last_prcie = close_price
                # 统计加仓次数
                g.add_time += 1
            # 空头加仓
            elif g.position == -1:
                QuickInsertOrder(
                    context.myacc, g.code, "sell", "open", current_price, g.unit
                )
                # 添加止损单，当价格向下突破到一定程度时就平仓
                InsertAbsStopLossPosition(
                    context.myacc, g.code, "sell", current_price * 1.05, g.unit
                )
                log.info("空头加仓成功:" + str(GetCurrentTime()) + str(g.code) + str(g.unit))
                # 更新交易价格
                g.last_prcie = close_price
                # 统计加仓次数
                g.add_time += 1

        # 判断平仓止损
        elif signal == -1:
            # 多头平仓
            if g.position == 1:
                QuickInsertOrder(
                    context.myacc, g.last_code, "sell", "close", current_price, g.buypos
                )
                log.info("多头止损成功:" + str(GetCurrentTime()) + str(g.code))
                log.info("----------------------------------------------------------")
            # 空头平仓
            elif g.position == -1:
                QuickInsertOrder(
                    context.myacc, g.last_code, "buy", "close", current_price, g.sellpos
                )
                log.info("空头止损成功:" + str(GetCurrentTime()) + str(g.code))
                log.info("----------------------------------------------------------")
            # 重新初始化参数
            reset()

    # 得到开仓信号
    open_signal = check_break(price_list, close_price, g.window)

    # 多头开仓
    if open_signal == 1 and g.position != 1:
        # 检测否需要空头平仓
        if g.position == -1:
            QuickInsertOrder(
                context.myacc, g.last_code, "buy", "close", current_price, g.sellpos
            )
            # 重新初始化参数
            reset()
            log.info("空头平仓成功:" + str(GetCurrentTime()) + str(g.code))
            log.info("----------------------------------------------------------")
        # 多头开仓
        g.unit = get_unit(
            context.myacc.AccountBalance.AssetsBalance, ATR, g.future_index
        )
        QuickInsertOrder(context.myacc, g.code, "buy", "open", current_price, g.unit)
        # 设置止损单
        InsertAbsStopLossPosition(
            context.myacc, g.code, "buy", current_price * 0.95, g.unit
        )
        g.position = 1
        log.info("多头建仓成功:" + str(GetCurrentTime()) + str(g.code) + str(g.unit))
        log.info("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        g.add_time = 1
        g.last_prcie = close_price
        g.last_code = g.code

    # 空头开仓
    elif open_signal == -1 and g.position != -1:
        # 检测否需要多头平仓
        if g.position == 1:
            QuickInsertOrder(
                context.myacc, g.last_code, "sell", "close", current_price, g.buypos
            )
            # 重新初始化参数
            reset()
            log.info("多头平仓成功:" + str(GetCurrentTime()) + str(g.code))
            log.info("----------------------------------------------------------")
        # 空头开仓
        g.unit = get_unit(
            context.myacc.AccountBalance.AssetsBalance, ATR, g.future_index
        )
        QuickInsertOrder(context.myacc, g.code, "sell", "open", current_price, g.unit)
        # 设置止损单
        InsertAbsStopLossPosition(
            context.myacc, g.code, "sell", current_price * 1.05, g.unit
        )
        g.position = -1
        log.info("空头建仓成功:" + str(GetCurrentTime()) + str(g.code) + str(g.unit))
        log.info("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        g.add_time = 1
        g.last_price = close_price
        g.last_code = g.code
