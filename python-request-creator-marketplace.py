# coding:utf-8

import requests
from lxml import etree
import json
import time
import re
import redis
import log
import argparse
from utils import insertUtils
from utils import redisLock
from concurrent.futures import ThreadPoolExecutor
from config import RedisKeyConstants as RedisKeyConstants
from config import Config
import execjs

# 时间格式化
timeArray = time.localtime(time.time())
otherStyleTime = time.strftime("%Y%m%d", timeArray)
numStyleTime = time.strftime("%H%M%S", timeArray)
time_default_range = str(otherStyleTime)

pool = ThreadPoolExecutor(max_workers=8)

# redis初始化
redis_client = redis.Redis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, db=Config.REDIS_DB,
                           password=Config.REDIS_PASSWORD, decode_responses=True)
# redis异常状态
redis_key_error_num = RedisKeyConstants.creator_marketplace_error_num
redis_key_response_num = RedisKeyConstants.creator_marketplace_response_num
# redis请求状态
redis_key_tiktok_shop_num = RedisKeyConstants.redis_key_tiktok_shop_num

# log初始化
logging = log.Logger("TikTok用户画像-" + str(otherStyleTime) + '.log', level='INFO')

# 全局状态变量
global tiktok_shop_request_enable
global creator_marketplace_pagination


# 把总数据量拆分成50每页的数据
def paginate(total_pages, pages_per_range):
    ranges = []
    for i in range(1, int(total_pages) // pages_per_range + 1):
        # 计算当前范围的起始和结束页码
        start_page = i
        ranges.append((start_page, 50))
    if len(ranges) * 50 < int(total_pages):
        ranges.append([str(len(ranges) + 1), '50'])
    return ranges


# 分割用户id列表给多线程
def paginate_user_id_list(total, N):
    if N <= 0:
        raise ValueError("N必须大于0")
    pages_per_range = total // N
    remainder = total % N
    ranges = []
    start = 1
    for i in range(N):
        if i == N - 1:
            end = start + pages_per_range + remainder - 1
        else:
            end = start + pages_per_range - 1
        ranges.append((start - 1, end - 1))
        start = end + 1
    return ranges


# 从tiktok shop平台获取unique id列表
def get_tiktok_shop_user_unique_id(request_params):
    url = "https://creatormarketplace.tiktok.com/h/api/gateway/handler_get/"
    headers = {
        'content-type': 'application/json',
        'accept': 'application/json, text/plain, */*',
        'cookie': """csrftoken=fbNfteG8z7a32X1zTaxFx4ZszAKKOrNl; passport_csrf_token=9aa37d9813b07fda980578ef36298d78; passport_csrf_token_default=9aa37d9813b07fda980578ef36298d78; lang=zh-Hans; locale=zh; star_language=zh; msToken=rObrgyunEG1MX-wbRnvimRYp5E6p0VnI_zcYCgLXEbfKLDD6Z--vfYmdWXVGIuuhUp6dZx-fKLg_DypMTLM1BTZlQcPB2NbikQrcJihsXNgbueJutv7Zl_F9Yj1QJh12Rwt8gg==; sso_auth_status_ads=fbc702edf3d283bef2ad9b76c61965c9%2C171a6ba38594190f8d0fd0e9b604ab95; sso_auth_status_ss_ads=fbc702edf3d283bef2ad9b76c61965c9%2C171a6ba38594190f8d0fd0e9b604ab95; sso_uid_tt_ads=b78539f67ba2378032af84a8efff612965653a69b8c96d04dd75943be8024113; sso_uid_tt_ss_ads=b78539f67ba2378032af84a8efff612965653a69b8c96d04dd75943be8024113; sso_user_ads=14ccceb8b6f006edc2ac7007b1b8f39d; sso_user_ss_ads=14ccceb8b6f006edc2ac7007b1b8f39d; sid_ucp_sso_v1_ads=1.0.0-KDlhNDk1YWE5NDlhZWZlYTE4Y2IwOTNkYjRjMDVhZGI4MWJiN2Y5NTEKIAiBiNH6pI2k52YQpqG6tgYY-w8gDDCmobq2BjgBQOwHEAMaA3NnMSIgMTRjY2NlYjhiNmYwMDZlZGMyYWM3MDA3YjFiOGYzOWQ; ssid_ucp_sso_v1_ads=1.0.0-KDlhNDk1YWE5NDlhZWZlYTE4Y2IwOTNkYjRjMDVhZGI4MWJiN2Y5NTEKIAiBiNH6pI2k52YQpqG6tgYY-w8gDDCmobq2BjgBQOwHEAMaA3NnMSIgMTRjY2NlYjhiNmYwMDZlZGMyYWM3MDA3YjFiOGYzOWQ; odin_tt=b992de3ad8ed82bac2caad48df3a6fe6668856da74bdd34a026af3e45e9b5c75191a445bccd3900992a309b3988c20dc4c59868d7d8f5bd794245a6452ab289e; sid_guard_ads=b1aa60d57686a60509e02478d8c68dea%7C1724813479%7C5183999%7CSun%2C+27-Oct-2024+02%3A51%3A18+GMT; uid_tt_ads=fd5bda4bc7892b40c8c67dbd7ded8a05d0849919b21129741ae7e952c6a018e1; uid_tt_ss_ads=fd5bda4bc7892b40c8c67dbd7ded8a05d0849919b21129741ae7e952c6a018e1; sid_tt_ads=b1aa60d57686a60509e02478d8c68dea; sessionid_ads=b1aa60d57686a60509e02478d8c68dea; sessionid_ss_ads=b1aa60d57686a60509e02478d8c68dea; sid_ucp_v1_ads=1.0.0-KDE4YmExZjhmZjg1ZmE5NzFkMjFhZDQxMjk5M2FmNjk1MDAxNjIzNjgKGgiBiNH6pI2k52YQp6G6tgYY-w8gDDgBQOwHEAMaA3NnMSIgYjFhYTYwZDU3Njg2YTYwNTA5ZTAyNDc4ZDhjNjhkZWE; ssid_ucp_v1_ads=1.0.0-KDE4YmExZjhmZjg1ZmE5NzFkMjFhZDQxMjk5M2FmNjk1MDAxNjIzNjgKGgiBiNH6pI2k52YQp6G6tgYY-w8gDDgBQOwHEAMaA3NnMSIgYjFhYTYwZDU3Njg2YTYwNTA5ZTAyNDc4ZDhjNjhkZWE; d_ticket_ads=27e9cb94dfaf9f3471c839b8505db4f6b9527; reauth_token=1.0.0-KGZiMGY4OTU0NjBhMTUzNTM2YjcxOTBkN2JlY2NmNWNjNmU1Njk1OGUIrwwQgYjR-qSNpOdmSgVlbWFpbFDiorq2Bljhorq2BmCAmp4BaARyB3VzZWFzdDU; reauth_token_ss=1.0.0-KGZiMGY4OTU0NjBhMTUzNTM2YjcxOTBkN2JlY2NmNWNjNmU1Njk1OGUIrwwQgYjR-qSNpOdmSgVlbWFpbFDiorq2Bljhorq2BmCAmp4BaARyB3VzZWFzdDU; ttwid=1%7CbmJIbY5mz3KS9cag0y32ORhLtlaipM6403ojmODO01Y%7C1724989853%7C728d6b8221971bfd01f1642a4794c19b308be51973f5a2dfcbc53cebc0a1e4ff; qualification_verification_cookie="@D4DO7tu9Cun1Co03pamSPhMz8vHW3nCBxATtAl4snlhx2Ju21mG7TDuc53yeJbHk"; tcm_customize_cookie=1724989853d2682eba-cc75-4973-a585-0aca0ac8305f; msToken=OZKlLmbSQd1SJzJibiogVtT-uE0ecfNGIoz8m-kdUuV2RR3hBmmvsCO3cJzCfzoZ9B1XkjdC7ra2eEw16gQSVtQCQe6OcjZAU9EIkYlt0ofRdYIX_jLi1NO63kdGO6PW8ciAwg==""",
        'priority': 'u=1, i',
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0",
        "accept-language": "zh-CN,zh;q=0.9",
        "referer": "https://creatormarketplace.tiktok.com/ad/market?audienceFrom=US",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "Windows",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "tcm-adv-id": "7408017992677801985",
        "x-csrftoken": "fbNfteG8z7a32X1zTaxFx4ZszAKKOrNl",
        "x-star-service-method": "AuthorPlazaSearch",
        "x-star-service-name": "search.AdTcmSearchService",
    }
    logging.logger.info("请求url：" + url)
    try:
        response_tiktok_shop_user_unique_ids = requests.get(url=url, headers=headers, params=request_params,
                                                            timeout=20)
        res_data = json.loads(response_tiktok_shop_user_unique_ids.text)
        if response_tiktok_shop_user_unique_ids.status_code != 200 or res_data.get("code") != 0:
            raise Exception("Creator Marketplace平台获取失败，请检查网络!")
    except Exception as ex:
        logging.logger.error(ex)
        logging.logger.error("\033[31mCreator Marketplace平台获取失败，请检查网络!'\033[0m")
        # 失败计数，超过10次失败结束
        redis_client.incr(redis_key_error_num, 1)
        return [[], False]
    # User id 列表
    # user_id_list = res_data.get("data").get("all_creators")
    # 所有数据列表
    creators_msg = res_data.get("data").get("creators")
    # 下一页数据列表
    next_pagination = res_data.get("data").get("pagination")
    redis_client.set(redis_key_error_num, 0)
    return [creators_msg, next_pagination.get("has_more")]


if __name__ == "__main__":
    while True:
        if int(redis_client.get(redis_key_error_num)) >= 10:
           raise Exception("网络请求失败")
        lock = redisLock.acquire_lock(RedisKeyConstants.lock_creator_marketplace_search_key)
        enum = None
        if lock:
            enum = redis_client.blpop(RedisKeyConstants.creator_marketplace_search_key)
        redisLock.release_lock(RedisKeyConstants.lock_creator_marketplace_search_key, lock)
        if enum is None:
            time.sleep(10)
            continue
        try:
            # redis状态初始化
            redis_client.set(redis_key_error_num, 0)
            redis_client.set(redis_key_response_num, 0)
            redis_client.set(redis_key_tiktok_shop_num, 0)
            # 初始化请求
            tiktok_shop_request_enable = True
            # 开始计时
            t = time.time()
            # 处理数据爬虫
            # 轮询分页
            page = 1
            while tiktok_shop_request_enable:
                if int(redis_client.get(redis_key_error_num)) >= 10:
                    raise Exception("网络请求失败，请重试。。")
                user_list = []
                try:
                    # 初始化页面
                    creator_marketplace_pagination = {
                        "page": page,
                        "limit": 24,
                        "sort_type": 2,
                        "audience_max_distri_region": "US",
                        "query": enum[1],
                        "sort_field": "comp_rank",
                        "use_creator_v2": True,
                        "service_name": "search.AdTcmSearchService",
                        "service_method": "AuthorPlazaSearch"
                    }
                    request_params = creator_marketplace_pagination
                    request_params["sign"] = execjs.compile(open('./utils/MD5.js', 'r', encoding='utf-8').read()).call(
                        'l',
                        creator_marketplace_pagination)
                    request_params["aid"] = 2043
                    print(request_params)
                    rsp_data = get_tiktok_shop_user_unique_id(request_params)
                    # 是否有下一页
                    tiktok_shop_request_enable = rsp_data[1]
                    print(f"has_more:{tiktok_shop_request_enable}")
                    # 用户列表，24条
                    user_list.extend(rsp_data[0])
                    insertUtils.insert_data_creator_marketplace(data=user_list)
                    page = page + 1
                except Exception as ex:
                    logging.logger.error(ex)
            # redis_client.set("test-unused-data", json.dumps(user_list))
            # logging.logger.info(tiktok_shop_pagination)
            # 分批次爬取和写入
            # thread_num = 8
            # time.sleep(1)
        except Exception as ex:
            logging.logger.error(ex)
    pool.shutdown()
