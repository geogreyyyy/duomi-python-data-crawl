# coding:utf-8

import json
import time
from concurrent.futures import ThreadPoolExecutor

import redis
import requests

import log
from config import Config
from config import RedisKeyConstants as RedisKeyConstants
from utils import getSQLDataUtils
from utils import redisLock
from utils import sendFeiShuMsg

# 时间格式化
timeArray = time.localtime(time.time())
otherStyleTime = time.strftime("%Y%m%d", timeArray)
numStyleTime = time.strftime("%H%M%S", timeArray)
time_default_range = str(otherStyleTime)

# 线程池初始化
pool = ThreadPoolExecutor(max_workers=8)
thread_num = 2

# redis初始化
redis_client = redis.Redis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, db=Config.REDIS_DB,
                           password=Config.REDIS_PASSWORD)
# redis异常状态
redis_key_error_num = RedisKeyConstants.seller_contact_error_num
redis_key_response_num = RedisKeyConstants.seller_contact_response_num
# redis请求状态

# redis状态初始化
redis_client.set(redis_key_error_num, 0)
redis_client.set(redis_key_response_num, 0)

# log初始化
logging = log.Logger("二次爬取-" + str(otherStyleTime) + '.log', level='INFO')

COOKIE_INDEX = 0


# 从tiktok shop平台获取unique id列表
def get_tiktok_shop_user_unique_id(data):
    global COOKIE_INDEX
    cookie = getSQLDataUtils.tap_user_list(data['creator_oecuid'], COOKIE_INDEX)
    url = cookie["url"]
    headers = {
        'content-type': 'application/json',
        'Accept': """application/json, text/plain, */*""",
        'Accept-Language': """zh-CN,zh;q=0.9""",
        'Connection': """keep-alive""",
        'Cookie': cookie["Cookie"],
        'Origin': 'https://partner.tiktokshop.com',
        'Referer': 'https://partner.tiktokshop.c om/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'User-Agent': """Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36""",
        'sec-ch-ua': '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
    try:

        response_tiktok_shop_user_unique_ids = requests.get(url=url, headers=headers, timeout=60)
        res_data = json.loads(response_tiktok_shop_user_unique_ids.text)
        if response_tiktok_shop_user_unique_ids.status_code != 200 or res_data.get("code") != 0:
            raise Exception(str(res_data))
        response_tiktok_shop_user_unique_ids.close()
    except Exception as ex:
        logging.logger.error(ex)
        if str(ex) == "Expecting value: line 1 column 1 (char 0)":
            print("爬取太快==")
            time.sleep(10)
            return []
        logging.logger.error(response_tiktok_shop_user_unique_ids)
        # 失败计数，超过10次失败结束
        getSQLDataUtils.resetErrorData(res_data, data['user_id'])
        if res_data.get('message') == 'too many request':
            raise Exception("too many request")
        redis_client.incr(redis_key_error_num, 1)
        return []
    redis_client.get(redis_key_error_num).decode()
    # 创作者Id列表
    return res_data.get("contact_info", [])


# 获取成功数量
get_num = "seller_contact_get_num"


def start():
    lock_key = "seller_contact_get_id_lock_key"
    global COOKIE_INDEX
    while True:
        lock = redisLock.acquire_lock(lock_key)
        user_data_list = []
        try:
            if lock:
                user_data_list = getSQLDataUtils.get_no_request_seller_contact_id()
                logging.logger.info(f"正在采集...{len(user_data_list)}")
        except Exception as ex:
            logging.logger.error(ex)
        finally:
            redisLock.release_lock(lock_key, lock)
        if len(user_data_list) <= 0:
            break
        try:
            user_data_list.pop()
            for data in user_data_list:
                response_data = get_tiktok_shop_user_unique_id(data)
                getSQLDataUtils.resetDataPartner(response_data, data.get('user_id', None))
        except Exception as ex:
            logging.logger.error(ex)
            if str(ex) == 'too many request':
                COOKIE_INDEX = COOKIE_INDEX + 1
            if str(ex) == 'cookie for done!':
                raise Exception("Cookie轮询完毕")
        # break
        # 暂时睡眠10s


if __name__ == "__main__":
    try:
        start()
    except Exception as ex:
        sendFeiShuMsg.setFeiShuMsg(f"二次爬取达人数据失败:{ex},请及时修复")
