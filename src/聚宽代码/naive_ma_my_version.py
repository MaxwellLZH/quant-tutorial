# TODO: 移仓换月  OK
# TODO: ATR止损
# TODO: 调整资金分配比例
# TODO: 一手都不够买的情况
# 对比使用指数合约 vs. 使用主力合约生成信号


from jqdata import * 
from collections import defaultdict
from functools import lru_cache


def initialize(context):
    # 设置参数
    set_info(context)
    # 不设定基准，在多品种的回测当中基准没有参考意义
    set_benchmark('511880.XSHG')
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    # 过滤掉order系列API产生的比error级别低的log
    log.set_level('order', 'info')
    ### 期货相关设定 ###
    # 设定账户为金融账户
    set_subportfolios([SubPortfolioConfig(cash=context.portfolio.starting_cash, type='futures')])
    # 期货类每笔交易时的手续费是：买入时万分之2.5,卖出时万分之2.5,平今仓为万分之2.5
    set_order_cost(OrderCost(open_commission=0.00025, close_commission=0.00025,close_today_commission=0.00025), type='index_futures')
    # 设定保证金比例15%
    set_option('futures_margin_rate', 0.15)
    # 开盘前运行
    run_daily(before_market_open, time='before_open', reference_security='RB8888.XSGE')
    # 开盘时运行
    run_daily(market_open, time='open', reference_security='RB8888.XSGE')
    # 收盘后运行
    run_daily(after_market_close, time='after_close', reference_security='RB8888.XSGE')
    # 设置滑点（单边万5，双边千1）
    set_slippage(PriceRelatedSlippage(0.001),type='future')
  

def set_info(context):
    #######变量设置########
    g.LastRealPrice = {} # 最新真实合约价格字典(用于吊灯止损）
    g.HighPrice = {} # 各品种最高价字典（用于吊灯止损）
    g.LowPrice = {} # 各品种最低价字典（用于吊灯止损）
    g.TradeLots = {}  # 各品种的交易手数信息
    g.PriceArray = {} # 信号计算价格字典
    g.Price_dict = {} # 各品种价格列表字典
    g.CoolDownTimer = defaultdict(0) # 计数器（用于防止止损重入）
    g.MappingReal = {} # 真实合约映射（key为symbol，value为主力合约）

    #######参数设置########
    g.FastWindow = 5 # 快线窗口长度
    g.SlowWindow = 20 # 慢线窗口长度
    g.Cross = 0 # 均线交叉判定信号
    g.stop = 0.05 # 止损比例
    g.margin_rate = 0.15 # 定义保证金率
    # 交易的期货品种信息
    g.instruments = ['TA','P','CU','ZN','C','AG','RU','AL','L','RB','CS','SF','JD','CF','J','M','V','I']

    # 价格列表初始化
    set_future_list(context)


def set_future_list(context):
    for ins in g.instruments:
        dom = get_dominant_future(ins)
        log.info('添加了以下主力合约: {}'.format(dom))
        # 填充映射字典
        g.MappingReal[ins] = dom
        #设置主力合约已上市的品种基本参数
        if dom == '':
            pass


'''
换月模块逻辑（ins是期货品种的symbol（如‘RB’），dom或future指合约（如'RB1610.XSGE'）,idx指指数合约（如’RB8888.XSGE‘）
    1.在第一天开始时，将所有期货品种最初的主力合约写入MappingReal与MappingIndex当中
    2.每天开盘获取一遍ins对应的主力合约，判断是否在MappingReal中，若不在，则执行replace模块
    3.replace模块中，卖出原来持有的主力合约，等量买入新合约；修改MappingReal
'''
## 开盘前运行函数
def before_market_open(context):
    # 输出运行时间
    log.info('函数运行时间(before_market_open)：'+str(context.current_dt.time()))
    send_message('开始交易')
    
    # 过滤无主力合约的品种，传入并修改期货字典信息
    for ins in g.instruments:
        dom = get_dominant_future(ins)
        if dom == '':
            pass
        elif ins not in g.MappingReal:
            # 新品种暂不处理
            pass
        else:
            # 判断是否需要移仓换月
            if dom == g.MappingReal[ins]:
                pass
            else:
                try:
                    move_position_between_contract(context, ins, dom, pindex=0)
                except:
                    log.error('移仓换月失败: ins:{} dom:{}'.format(ins, dom))
                g.MappingReal[ins] = dom
            
            # 每个品种使用初始资金starting_cash的10%开仓
            g.TradeLots[dom] = get_lots(context.portfolio.starting_cash / len(g.instruments), ins)
            

## 开盘时运行函数
def market_open(context):
    # 输出函数运行时间
    log.info('函数运行时间(market_open):'+str(context.current_dt.time()))

    for ins in g.instruments:
        # 过滤空主力合约品种
        if g.MappingReal[ins] == '':
            continue

        RealFuture = g.MappingReal[ins]
        
        # 获取当月合约交割日期, 当月合约交割日当天不开仓
        end_date = get_CCFX_end_date(RealFuture)
        if (context.current_dt.date() == end_date):
            log.info('合约交割日期，跳过......')
            return




        g.LastRealPrice[RealFuture] = attribute_history(RealFuture,1,'1d',['close'])['close'][-1]
        # 获取价格list
        g.PriceArray[IndexFuture] = attribute_history(IndexFuture,50,'1d',['close','open','high','low'])
        g.CurrentPrice = g.PriceArray[IndexFuture]['close'][-1]
        g.ClosePrice = g.PriceArray[IndexFuture]['close']
        # 如果没有数据，返回
        if len(g.PriceArray[IndexFuture]) < 50:
            return
        else:
            
            #设置两条均线
            MaFast = g.ClosePrice[-g.FastWindow:].mean()
            MaSlow = g.ClosePrice[-g.SlowWindow:].mean()
            
            #判断均线交叉（金叉死叉）
            if MaFast>MaSlow:
                g.Cross = 1
            elif MaFast<MaSlow:
                g.Cross = -1
            else:
                g.Cross = 0
                
            #判断交易信号：均线交叉+可二次入场条件成立
            if  g.Cross == 1 and g.Reentry_long == False:
                g.Signal = 1
            elif g.Cross == -1 and g.Reentry_short == False:
                g.Signal = -1
            else:
                g.Signal = 0
                
            # 执行交易
            Trade(context,RealFuture)
            # 止损后，运行防止充入模块
            Dont_Re_entry(context,RealFuture)
            # 计数器+1
            if RealFuture in g.Times.keys():
                g.Times[RealFuture] += 1 
            else:
                g.Times[RealFuture] = 0
       
           
## 收盘后运行函数
def after_market_close(context):
    log.info(str('函数运行时间(after_market_close):'+str(context.current_dt.time())))
    # 得到当天所有成交记录
    trades = get_trades()
    for _trade in trades.values():
        log.info('成交记录：'+str(_trade))
    log.info('一天结束')
    log.info('##############################################################')
    

## 交易模块 
def Trade(context,RealFuture):
    
    # 快线高于慢线，且追踪止损失效，则可开多仓
    if g.Signal == 1 and context.portfolio.long_positions[RealFuture].total_amount == 0:
        if context.portfolio.long_positions[RealFuture].total_amount != 0:
            log.info('空头有持仓：%s'%(RealFuture))
        order_target(RealFuture,0,side='short')
        order_target(RealFuture,g.TradeLots[RealFuture],side='long')
        g.HighPrice[RealFuture] = g.LastRealPrice[RealFuture]
        g.LowPrice[RealFuture] = False
        log.info('正常买多合约：%s'%(RealFuture))
        
    
    elif g.Signal == -1 and context.portfolio.short_positions[RealFuture].total_amount == 0:
        if context.portfolio.short_positions[RealFuture].total_amount != 0:
            log.info('多头有持仓：%s'%(RealFuture))
        order_target(RealFuture,0,side ='long')
        order_target(RealFuture,g.TradeLots[RealFuture],side='short')
        g.LowPrice[RealFuture] = g.LastRealPrice[RealFuture]
        g.HighPrice[RealFuture] = False
        log.info('正常卖空合约：%s'%(RealFuture))
    else:
         TrailingStop(context,RealFuture)
        
        
# 追踪止损后,防止立刻重入模块
# 因为追踪止损条件领先于金叉死叉，所以在止损后，要防止系统再次高位入场
def Dont_Re_entry(context,future):
    # 防重入模块：上一次止损后20根bar内不交易，但如果出现价格突破事件则20根bar的限制失效
    #设置最高价与最低价（注意：需要错一位，不能算入当前价格）
    g.Highest_high_2_20 = g.ClosePrice[-21:-1].max()
    g.Lowest_low_2_20 = g.ClosePrice[-21:-1].min()
    
    if  g.Reentry_long == True:
        if g.Times[future] > 20 or g.CurrentPrice > g.Highest_high_2_20 :
            g.Reentry_long = False
    if  g.Reentry_short == True:
        if g.Times[future] > 20 or g.CurrentPrice < g.Lowest_low_2_20 :
            g.Reentry_short = False
        

# 追踪止损模块（百分比止损）
def TrailingStop(context,RealFuture):
    
    # 记录多空仓位
    long_positions = context.portfolio.long_positions
    short_positions = context.portfolio.short_positions
    
    # 通过for循环逐一平仓（多头）
    if RealFuture in long_positions.keys():
        if long_positions[RealFuture].total_amount > 0:
            if g.HighPrice[RealFuture]:
                g.HighPrice[RealFuture] = max(g.HighPrice[RealFuture], g.LastRealPrice[RealFuture])
                if g.LastRealPrice[RealFuture]  < g.HighPrice[RealFuture]*(1-g.stop):
                    log.info('多头止损:\t' +  RealFuture)
                    order_target(RealFuture,0,side = 'long')
                    g.Reentry_long = True
                    
    # 通过for循环逐一平仓（空头）
    if RealFuture in short_positions.keys():
        if short_positions[RealFuture].total_amount > 0:
            if g.LowPrice[RealFuture]:
                g.LowPrice[RealFuture] = min(g.LowPrice[RealFuture], g.LastRealPrice[RealFuture])
                if g.LastRealPrice[RealFuture]  > g.LowPrice[RealFuture]*(1+g.stop):
                    log.info('空头止损:\t' + RealFuture)
                    order_target(RealFuture,0,side = 'short')
                    g.Reentry_short = True


# 移仓模块：当主力合约更换时，平当前持仓，更换为最新主力合约        
def move_position_between_contract(context, ins, dom, pindex=0):
    """ 移仓换月
    :param ins: 期货品种代码
    :param dom: 当前主力合约的code
    """
    cur_hold = g.MappingReal[ins]

    if cur_hold in context.subportfolios[pindex].long_positions.keys():
        lots_long = context.subportfolios[pindex].long_positions[cur_hold].total_amount
        order_target(security=cur_hold,
                     amount=0,
                     side='long',
                     pindex=pindex)
        order_target(security=dom,
                     amount=lots_long,
                     side='long',
                     pindex=pindex)
        log.info("移仓换月：多头：From {} To {} Amount {}".format(cur_hold, dom, lots_long))

    if cur_hold in context.subportfolios[pindex].short_positions.keys():
        lots_short = context.subportfolios[pindex].short_positions[cur_hold].total_amount
        order_target(security=cur_hold,
                     amount=0,
                     side='short',
                     pindex=pindex)
        order_target(security=dom,
                     amount=lots_short,
                     side='short',
                     pindex=pindex)
        log.info("移仓换月：空头：From {} To {} Amount {}".format(cur_hold, dom, lots_short))



@lru_cache
def get_future_basic_info(dom):
    from jqdata import jy
    import re
    if "9999" in future or "8888" in future:
        match = re.match(r"(?P<underlying_symbol>[A-Z]{1,})", future)
        if not match:
            raise ValueError("未知期货标的：{}".format(future))
        else:
            future = get_dominant_future(match.groupdict()["underlying_symbol"])
        
    q = query(jy.Fut_ContractMain).filter(jy.Fut_ContractMain.ContractCode == future.split(".")[0])
    result = jy.run_query(query_object=q).to_dict("record")
    if result:
        result = result.pop()
        min_point = re.match("(?P<value>^[0-9]+([.]{1}[0-9]+){0,1})", result["LittlestChangeUnit"]).groupdict(nan)["value"]
        return {"ContractUnit": result["CMValue"],
               "PriceScale": float(str(min_point)[:-1] + "1") if float(min_point) < 1 else 1,
               "MinPoint": float(min_point),
                "MinMarginRatio": float(result["InitialMarginRatio"])
               }
    else:
        return None


# 获取交易手数函数
def get_lots(cash, dom):
    df_open_price = attribute_history(security=dom, count=3, unit="1d", fields=['open'])
    if len(df_open_price) == 0:
        raise ValueError('开盘价信息获取失败: {}'.format(dom))
    open_price = df_open_price['open'].values[-1]
    
    contract_size = get_future_basic_info(dom)['ContractUnit']
    if contract_size is None:
        raise ValueError('基础信息获取失败: {}'.format(dom))

    # 返回手数（价格*合约规模=名义价值）
    return cash / (open_price * g.margin_rate * contract_size)



# 获取金融期货合约到期日
def get_CCFX_end_date(fature_code):
    # 获取金融期货合约到期日
    return get_security_info(fature_code).end_date