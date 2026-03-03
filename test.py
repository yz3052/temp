import pandas as pd
import numpy as np
from datetime import datetime
from urllib import parse
import urllib.parse as urllp

import requests
from ahl.web.proxy import proxy
import json


import sys
sys.path.append('/users/is/tozhang/PycharmProjects/projects/yz')
import yz.util as yz


# this scrapes forward -2 ~ 182 day JP earning calendar
# https://www.tradingview.com/markets/stocks-japan/earnings/


# it is impossible to scrape historical earnings data from this website.

# fields:
# earnings_release_time
# earnings_release_next_time -1: before open 0: unkown 1: after close



##################################################################################
#!- constants
##################################################################################

NOW = pd.to_datetime(datetime.now()).tz_localize('Europe/London').tz_convert('Asia/Tokyo').tz_localize(None)

TODAY = pd.to_datetime(datetime.now()).tz_localize('Europe/London').tz_convert('Asia/Tokyo').tz_localize(None)
TODAY = pd.to_datetime(TODAY.date())

TODAY_int = int(TODAY.timestamp())
TODAY_str = TODAY.strftime('%Y-%m-%d')

TODAY_2d = TODAY - pd.to_timedelta('2 day')
TODAY_2d_int = int(TODAY_2d.timestamp())

TODAY_p182d = TODAY + pd.to_timedelta('182 day')
TODAY_p182d_int = int(TODAY_p182d.timestamp())

##################################################################################
#!- Main
##################################################################################



url = 'https://scanner.tradingview.com/japan/scan'

cols = ["logoid", "name","market_cap_basic","earnings_per_share_forecast_next_fq","earnings_per_share_fq",
        "eps_surprise_fq","eps_surprise_percent_fq","revenue_forecast_next_fq","revenue_fq",
        "earnings_release_next_date","earnings_release_next_calendar_date","earnings_release_next_time",
        "description","type","subtype","update_mode","earnings_per_share_forecast_fq","revenue_forecast_fq",
        "earnings_release_date","earnings_release_calendar_date","earnings_release_time","currency",
        "fundamental_currency_code"]

header = {'Accept': 'text/plain, */*; q=0.01',
          'Accept-Encoding': 'gzip, deflate, br, zstd',
          'Accept-Language': 'en-US,en;q=0.9',
          'Connection': 'keep-alive',
          'Content-Length': '967',
          'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
          'Cookie': 'cookiePrivacyPreferenceBannerProduction=notApplicable; cookiesSettings={"analytics":true,"advertising":true}; _sp_ses.cf1a=*; _sp_id.cf1a=ad4db67a-3c0e-4b5a-a1c8-13ac001c2341.1721121245.3.1721292172.1721177662.f8db6876-df8e-463b-b595-09b900c3c271',
          'Host': 'scanner.tradingview.com',
          'Origin': 'https://www.tradingview.com',
          'Referer': 'https://www.tradingview.com/',
          'Sec-Ch-Ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
          'Sec-Ch-Ua-Mobile': '?0',
          'Sec-Ch-Ua-Platform': "Windows",
          'Sec-Fetch-Dest': 'empty',
          'Sec-Fetch-Mode': 'cors',
          'Sec-Fetch-Site': 'same-site',
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'}

# payload = {"filter":[{"left":"is_primary","operation":"equal","right":True},
#            {"left":"earnings_release_date,earnings_release_next_date","operation":"in_range",
#             "right":[TODAY_2d_int,TODAY_p182d_int]},
#            {"left":"earnings_release_date,earnings_release_next_date","operation":"nequal","right":1722265200}],
#  "options":{"lang":"en"},"markets":["japan"],"symbols":{"query":{"types":[]},"tickers":[]},
#  "columns": cols,
#  "sort":{"sortBy":"market_cap_basic","sortOrder":"desc"},"preset":None,"range":[0,10000]}

payload = {"filter":[
           {"left":"earnings_release_next_date","operation":"in_range",
            "right":[TODAY_2d_int,TODAY_p182d_int]}],
 "options":{"lang":"en"},"markets":["japan"],"symbols":{"query":{"types":[]},"tickers":[]},
 "columns": cols,
 "sort":{"sortBy":"market_cap_basic","sortOrder":"desc"},"preset":None,"range":[0,50000]}


with proxy():

    response = requests.post(url=url, data= json.dumps(payload), headers=header, verify=False)

    i_data = pd.DataFrame(response.json()['data'])
    i_data = i_data.rename(columns = {'s': 'ticker'})
    i_data[cols] = pd.DataFrame(i_data['d'].values.tolist(), columns = cols, index = i_data.index)
    i_data = i_data.drop(columns = ['d'])

    i_data['earnings_release_next_date'] = pd.to_datetime(i_data['earnings_release_next_date'], unit='s')
    i_data['earnings_release_next_calendar_date'] = pd.to_datetime(i_data['earnings_release_next_calendar_date'], unit='s')
    i_data['earnings_release_date'] = pd.to_datetime(i_data['earnings_release_date'], unit='s')
    i_data['earnings_release_calendar_date'] = pd.to_datetime(i_data['earnings_release_calendar_date'], unit='s')

    i_data['scraper_ts_jp'] = NOW
    i_data['scraper_date_jp'] = TODAY
    i_data.to_sql("util_calendar_earn_tv_jp", con=yz.create_sql_engine(), if_exists='append', index=False)
