import pandas as pd
from pathlib import Path
import os

data_dir = Path(__file__).parent.parent / 'data'


def get_future_code_df():
    return pd.read_excel(data_dir / 'future_contract_code.xlsx')


_future_df = get_future_code_df()
_name_to_code = dict(zip(_future_df.display_name, _future_df.code))
_code_to_name = dict(zip(_future_df.code, _future_df.display_name))

def find_code_by_name(name):
    for k, v in _name_to_code.items():
        if name in k:
            return v

def find_name_by_code(code):
    for k, v in _code_to_name.items():
        if code in k:
            return v

def get_price_by_code(code):
    path = data_dir / f"{code}.csv"
    df = pd.read_csv(path).rename(columns={'Unnamed: 0': 'time'})
    df['time'] = pd.to_datetime(df['time'])
    return df.set_index('time')

