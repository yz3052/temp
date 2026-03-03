

def md5_hex(string: str):
    md5_str = hashlib.md5(string.encode('utf-8')).hexdigest()
    return md5_str

def hmac_md5(content, key_text):
    try:
        key_bytes = key_text.encode('utf-8')
        content_bytes = content.encode('utf-8') if isinstance(content, str) else content
        mac = hmac.new(key_bytes, content_bytes, hashlib.md5)
        return mac.digest()
    except Exception as e:
        print(f"Error occurred while calculating HMAC-MD5: {e}")
        return b''

def hmac_md5_hex(content, key_text):
    return hmac_md5(content, key_text).hex()

def signature(appid, secret_key, params):
    params['appid'] = appid
    sorted_dict = dict(sorted(params.items(), key=lambda x: x[0]))
    query_list = [f"{k}={v}" for k, v in sorted_dict.items()]
    uri_query = '&'.join(query_list)
    sign = hmac_md5_hex(uri_query, secret_key)
    return sign

def prepare_body(
    beginTime: int, endTime: int,  pageStart: int
):
    return {"beginTime": beginTime, "endTime": endTime, "pageSize": 500, "pageStart": pageStart}

def prepare_header(
    body: dict
):
    appid = "b9df795f-eee2-4c36-8c0a-d22948926c25"
    secret_key = "e16ecfe6df26403581f4509f6258a44c"
    header = {
        "body": md5_hex(json.dumps(body)),
        "act": "ahl-list", # market
        "app": "open-brm",
        "mod": "roadshow",
        "timestamp": str(int(time.time() * 1000))
    }
    res_sign = signature(appid, secret_key, header)
    header["signature"] = res_sign
    header["appid"] = appid

    return header





if __name__ == '__main__':

    # to be scheduled once every 30 minutes on each calendar day between 5am to 0am  (Asia/Shanghai timezone)


    # get timestamps

    NOWUTC = pd.to_datetime(datetime.datetime.utcnow())
    NOW = NOWUTC.tz_localize('UTC').tz_convert('Asia/Shanghai').tz_localize(None)
    TODAY = NOW.normalize()
    TODAY_m1w = TODAY - pd.to_timedelta('7 days')
    TODAY_p2m = TODAY + pd.to_timedelta('63 days')


    # scrape

    body = prepare_body(
        beginTime = int(datetime.datetime.timestamp(TODAY_m1w)*1000),
        endTime = int(datetime.datetime.timestamp(TODAY_p2m)*1000),
        pageStart = 1
    )

    NEXT = True
    o_data = []
    while NEXT:
        print(body['pageStart'], end= ',')

        # API query

        header = prepare_header(body)
        session = ScrapingSession()
        response = session.post(
            url='https://server.comein.cn/comein/index.php'
            , headers=header
            , json=body
        )
        i_json = response.json()


        # if not success

        if i_json['msg'] != '成功':
            raise Exception(i_json['errordesc'])


        # get data

        t_data = pd.DataFrame(i_json['data'])
        o_data.append(t_data)


        # next for loop

        if i_json['extra']['hasMore']:
            body['pageStart'] = body['pageStart'] + 1
        else:
            NEXT = False


    # output

    o_data_s2 = pd.concat(o_data, axis = 0)
    o_data_s2['scraper_ts_cn'] = NOW
    o_data_s2['scraper_ts_utc'] = NOWUTC
    o_data_s2 = o_data_s2.sort_values('stime')

    if not os.path.exists('/data/user/tozhang/comein/'+ NOW.strftime('%Y%m%d')):
        os.mkdir('/data/user/tozhang/comein/'+ NOW.strftime('%Y%m%d'))
    o_data_s2.to_parquet('/data/user/tozhang/comein/'+ NOW.strftime('%Y%m%d/%H%M%S.parquet'))
