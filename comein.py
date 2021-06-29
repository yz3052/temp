# -*- coding: utf-8 -*-
"""
Created on Mon Jun 28 14:02:04 2021

@author: tomyi
"""

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

import time

import requests
import os
import pickle

import pandas as pd

### scrape events

headers = {'accept': 'application/json, text/plain, */*',
           'accept-encoding': 'gzip, deflate, br',
           'accept-language': 'zh,zh-TW;q=0.9,en-US;q=0.8,en;q=0.7,zh-CN;q=0.6',
           'act': 'search',
           'app': 'json',
           'b': '3.7.3',
           'browse': 'Netscape',
           'c': 'pc',
           'content-length': '109',
           'content-type': 'application/json;charset=UTF-8',
           'mod': 'roadshow',
           'origin': 'http://comein.cn',
           'os': 'web',
           'sec-ch-ua': '" Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91"',
           'sec-ch-ua-mobile': '?0',
           'sec-fetch-dest': 'empty',
           'sec-fetch-mode': 'cors',
           'sec-fetch-site': 'cross-site',
           'ua': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
           'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
           'webenv': 'comein'}


for i in range(21):
    
    print(i, end=',')
    time.sleep(5)
    
    data = {"industryTagIds":"","marketTagIds":"","roadshowTypeIds":"","openStatusCodes":"",
            "pagestart":i,"pagenum":20}
    
    r_data = requests.post('https://server.comein.cn/comein/index.php', json = data, headers = headers)
    i_data = r_data.json()
    
    with open(os.path.join(r'C:\Users\tomyi\Desktop\Sync\1. Trading\Market Data\test', str(i)+'.pickle'), 'wb') as handle:
        pickle.dump(i_data, handle, protocol=pickle.HIGHEST_PROTOCOL)
    
    if i_data['extra']['hasMore'] != True:
        break



# combine pickles
o_data = pd.DataFrame()

i_files = os.listdir(r'C:\Users\tomyi\Desktop\Sync\1. Trading\Market Data\test')
for f in i_files:
    with open(os.path.join(r'C:\Users\tomyi\Desktop\Sync\1. Trading\Market Data\test', f), 'rb') as handle:
        t_json = pickle.load(handle)
    o_data = o_data.append(pd.DataFrame(t_json['data']), ignore_index = True)
    

### get details
    

# prepare webdriver

CHROMEOPTIONS = webdriver.ChromeOptions()
# CHROMEOPTIONS.add_experimental_option("prefs", 
#             {"download.default_directory" : r'C:\Users\tomyi\.spyder-py3\chrome_driver\TEMP',
#                "download.prompt_for_download": False,
#                "download.directory_upgrade": True,
#                "safebrowsing.enabled": True})
#CHROMEOPTIONS.add_argument("--headless")
CHROME_PATH=r'C:\Users\tomyi\.spyder-py3\DRIVER\chromedriver.exe'
CAPABILITIES={'chromeOptions':{'useAutomationExtension':False}}

driver=webdriver.Chrome(CHROME_PATH,desired_capabilities = CAPABILITIES,options=CHROMEOPTIONS)


for i, r in o_data.iterrows():
    if i<52: 
        continue
    print (i, end=',')

    driver.get(r'https://comein.cn/roadshow/home/'+str(r['id']))
    
    
    if '<p class="login-method">进门财经 · 验证码登录</p>' in driver.page_source:
        #elem = driver.find_element_by_xpath('//span[@class="el-link--inner"]')
        #elem.click()
    
        elem = driver.find_element_by_xpath('//div/p[contains(text(), "邮箱登录")]')
        elem.click()
        elem = driver.find_element_by_xpath('//div/input[@type="text"][@class="form-control cn-form-control"]')
        elem.send_keys('boteins.summit@gmail.com')
        elem = driver.find_element_by_xpath('//div/input[@type="password"]')
        elem.send_keys('Summit2021!')
        elem = driver.find_element_by_xpath('//div/button[@class="btn cn-btn-default cn-login-btn"]')
        elem.click()
    
    element = WebDriverWait(driver, 90).until(
        EC.presence_of_element_located((By.XPATH , '//div[@class="roadShow_previewDivEdit"]'))
    )
    elem = driver.find_elements_by_xpath('//div[@class="roadShow_previewDivEdit"]')
    texts = [i.text for i in elem]
    
    if texts == []:
        raise Exception()
    
    o_text = '|@|'.join(texts)
    
    with open(os.path.join(r'C:\Users\tomyi\Desktop\Sync\1. Trading\Market Data\test', r['id']+'.txt'),'w') as h:
        h.write(o_text)
    
    

driver.quit()
