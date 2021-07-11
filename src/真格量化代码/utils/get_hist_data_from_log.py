# parse the experiment log to get historical prices 
import datetime
import sys
import re
import pandas as pd


if __name__ == '__main__':
	input_path = sys.argv[1]
	output_path = sys.argv[2]

	with open(input_path, 'r') as f:
		log = f.read()
		price_log = re.findall(r"\('\*PRICE.*", log)

	df = pd.DataFrame([eval(i)[1: ] for i in price_log], columns=['code', 'time', 'price'])
	df.to_csv(output_path, index=False)
