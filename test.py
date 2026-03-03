import requests

import pandas as pd
import numpy as np
import datetime
import time
import os

from ahl.web.proxy import proxy

import sys
sys.path.append('/users/is/tozhang/PycharmProjects/projects/yz')
import yz.util as yz

import io

import tqdm


# this is scrape all CFFEX eod quotes



########################################################################################################
#!- constants
########################################################################################################

NOW = datetime.datetime.utcnow()
TODAY_str = NOW.strftime('%Y%m%d')
root_o = '/data/user/tozhang/mktdata/cffex/eod_mktdata/'



########################################################################################################
#!- months to query
########################################################################################################


yyyymm_existing = [f[:6] for f in os.listdir(root_o)]
yyyymm_2_query = list(set(pd.date_range('2019-01-01', TODAY_str).strftime('%Y%m')))
yyyymm_2_query = [i for i in yyyymm_2_query if i not in yyyymm_existing]



with proxy():

    for yyyymm in tqdm.tqdm(yyyymm_2_query):


        url = f"http://www.cffex.com.cn/sj/historysj/{yyyymm}/zip/{yyyymm}.zip"
        response = requests.get(url)

        # Load zip file into memory
        zip_file = zipfile.ZipFile(io.BytesIO(response.content))

        # Get list of all CSV files
        csv_files = [f for f in zip_file.namelist() if f.endswith('.csv')]

        # Read each CSV file one by one
        for csv_file in csv_files:
            with zip_file.open(csv_file) as csv_f:
                t_data = pd.read_csv(csv_f, encoding='gbk')
                t_data = t_data.rename(columns={
                    '合约代码': 'code',
                    '今开盘': 'o', '最高价': 'h', '最低价': 'l', '成交量': 'v', '成交金额': 'amt',
                    '持仓量': 'oi', '持仓变化': 'oi_delta', '今收盘': 'c', '今结算': 'settle_px',
                    '前结算': 'prev_settle_px',
                    '涨跌1': 'chg1', '涨跌2': 'chg2', '隐含波动率(%)': 'iv_pvt',
                })
                t_data['t1d'] = pd.to_datetime(csv_file[:8], format='%Y%m%d')
                t_data = t_data.dropna(subset=['o', 'c'])
                t_data.to_parquet(os.path.join(root_o, csv_file[:8] + '.parquet'))

