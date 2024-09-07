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
from cookie import UserCookies
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

# log初始化
logging = log.Logger("TikTok用户画像-" + str(otherStyleTime) + '.log', level='INFO')
log_creator = log.Logger('轮询多个TCM账号.log', level='INFO')
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
def get_tiktok_shop_user_unique_id(request_params, cookie):
    url = "https://creatormarketplace.tiktok.com/h/api/gateway/handler_get/"
    headers = {
        'content-type': 'application/json',
        'accept': 'application/json, text/plain, */*',
        'cookie': cookie.get("cookie"),
        'priority': 'u=1, i',
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0",
        "accept-language": "zh-CN,zh;q=0.9",
        "referer": "https://creatormarketplace.tiktok.com/ad/market?audienceFrom=US",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "Windows",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "tcm-adv-id": cookie.get("tcm-adv-id"),
        "x-csrftoken": cookie.get("x-csrftoken"),
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
        print(f"失次数{redis_client.get(redis_key_error_num)}")
        return [[], False]
    # User id 列表
    # user_id_list = res_data.get("data").get("all_creators")
    # 所有数据列表
    creators_msg = res_data.get("data").get("creators")
    # 下一页数据列表
    next_pagination = res_data.get("data").get("pagination")

    redis_client.set(redis_key_error_num, 0)
    return [creators_msg, next_pagination.get("has_more")]


def start(cookie):
    # redis状态初始化
    redis_client.set(redis_key_error_num, 0)
    log_creator.logger.info(f"开始爬取账号:{cookie.get("user")}")
    # 当前账号总爬取数据
    user_data_length = 0
    # 最终存储几条
    user_data_save_length = 0
    while True:
        if int(redis_client.get(redis_key_error_num)) >= 5:
            log_creator.logger.info(f"开始爬取账号:{cookie.get("user")}")
            redis_client.set(redis_key_error_num, 0)
            break
        lock = redisLock.acquire_lock(RedisKeyConstants.lock_creator_marketplace_search_key)
        enum = None
        if lock:
            enum = redis_client.blpop(RedisKeyConstants.creator_marketplace_search_key)
        redisLock.release_lock(RedisKeyConstants.lock_creator_marketplace_search_key, lock)
        if enum is None:
            time.sleep(10)
            continue
        try:
            # 初始化请求
            tiktok_shop_request_enable = True
            # 开始计时
            t = time.time()
            # 处理数据爬虫
            # 轮询分页
            page = 1
            while tiktok_shop_request_enable:
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
                    rsp_data = get_tiktok_shop_user_unique_id(request_params, cookie)
                    # 是否有下一页
                    tiktok_shop_request_enable = rsp_data[1]
                    print(f"has_more:{tiktok_shop_request_enable}")
                    # 用户列表，24条
                    user_list.extend(rsp_data[0])
                    insert_num = insertUtils.insert_data_creator_marketplace(data=user_list)
                    # 页数增加
                    page = page + 1
                    # 记录LOG条数
                    user_data_length = len(rsp_data[0]) + user_data_length
                    user_data_save_length = user_data_save_length + insert_num
                except Exception as ex:
                    logging.logger.error(ex)
        except Exception as ex:
            logging.logger.error(ex)
    log_creator.logger.info(f"总共爬取数据{user_data_length}条,存储{user_data_save_length}")
    pool.shutdown()


if __name__ == "__main__":
    for user in UserCookies.user_cookie_list:
        start(user)
