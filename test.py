
import requests

import pandas as pd

from io import BytesIO

import random



headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-encoding': 'gzip, deflate, br, zstd',
    'accept-language': 'zh,zh-TW;q=0.9,en-US;q=0.8,en;q=0.7,zh-CN;q=0.6',
    'cache-control': 'no-cache',
    'connection': 'keep-alive',
    'host': 'www.szse.cn',
    'pragma': 'no-cache',
    'referer': 'https://www.szse.cn/szhk/hkbussiness/underlylist/',
    'sec-ch-ua': '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': "Windows",
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': 1,
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
}

rand = random.random()


i_content = requests.get(
    'https://www.szse.cn/api/report/'
    'ShowReport?SHOWTYPE=xlsx&CATALOGID=SGT_GGTBDQD'
    f'&TABKEY=tab1&random={rand}'
).content

o_south_sz = pd.read_excel(BytesIO(i_content),  engine="openpyxl")


    
