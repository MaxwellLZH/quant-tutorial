"""
新浪期货价格数据
"""
import pandas as pd
import requests
from tqdm import tqdm


# 期货合约对应code
dict_code = {
	'上期所': [("螺纹钢连续","RB0")
				,("线材连续","WR0")
				,("沪铜连续","CU0")
				,("沪铝连续","AL0")
				,("橡胶连续","RU0")
				,("燃油连续","FU0")
				,("沪锌连续","ZN0")
				,("黄金连续","AU0")
				,("白银连续","AG0")
				,("沥青连续","BU0")
				,("热轧卷板连续","HC0")
				,("沪镍连续","NI0")
				,("沪铅连续","PB0")
				,("原油连续","SC0")
				,("沪锡连续","SN0")
				,("纸浆连续","SP0")],

	'大商所': [("豆一连续","A0")
				,("豆二连续","B0")
				,("玉米连续","C0")
				,("玉米淀粉连续","CS0")
				,("乙二醇连续","EG0")
				,("纤维板连续","FB0")
				,("铁矿石连续","I0")
				,("焦炭连续","J0")
				,("鸡蛋连续","JD0")
				,("焦煤连续","JM0")
				,("塑料连续","L0")
				,("豆粕连续","M0")
				,("棕榈连续","P0")
				,("PP连续","PP0")
				,("PVC连续","V0")
				,("豆油连续","Y0")],

	'郑商所': [("鲜苹果连续","AP0")
				,("棉花连续","CF0")
				,("红枣连续","CJ0")
				,("棉纱连续","CY0")
				,("玻璃连续","FG0")
				,("粳稻连续","JR0")
				,("晚籼稻连续","LR0")
				,("郑醇连续","MA0")
				,("菜油连续","OI0")
				,("早籼稻连续","RI0")
				,("菜粕连续","RM0")
				,("菜籽连续","RS0")
				,("硅铁连续","SF0")
				,("锰硅连续","SM0")
				,("白糖连续","SR0")
				,("PTA连续","TA0")
				,("强麦连续","WH0")
				,("动力煤连续","ZC0")
					],

	'中金所': [("沪深300指数期货0","IF0")
			,("5年期国债期货0","TF0")
			,("10年期国债期货0","T0")
			,("上证50指数期货0","IH0")
			,("中证500指数期货0","IC0")
				]
}


URL = 'http://stock2.finance.sina.com.cn/futures/api/json.php/IndexService.getInnerFuturesDailyKLine?symbol={}'


result = []
for jys, lst_code in dict_code.items():
	print('working on', jys)

	for (name, code) in tqdm(lst_code):
		url = URL.format(code)
		resp = requests.get(url)
		try:
			df_price = pd.DataFrame(eval(resp.text))
		except:
			print(resp.text)
			continue

		df_price.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
		df_price['code'] = code
		df_price['name'] = name.replace('连续', '')
		df_price[['open', 'high', 'low', 'close']] = df_price[['open', 'high', 'low', 'close']].astype(float)
		result.append(df_price)

result = pd.concat(result, axis=0)
result.to_csv('./future_price.csv', index=False)
