# coding:utf-8

import json
import time
from concurrent.futures import ThreadPoolExecutor

import redis
import requests
from lxml import etree

import log
from config import Config
from config import RedisKeyConstants as RedisKeyConstants
from config import UserFilter
from utils import insertUtils
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
redis_key_tik_tok_request_error_num = RedisKeyConstants.redis_key_tik_tok_request_error_num
# redis请求状态

# redis状态初始化
redis_client.set(redis_key_tik_tok_request_error_num, 0)

# log初始化
logging = log.Logger("TikTok用户画像PH-" + str(otherStyleTime) + '.log', level='INFO')
log_creator = log.Logger('tiktok-shop-partner-PH.log', level='INFO')
# 全局状态变量
tiktok_shop_request_enable = True
creator_marketplace_pagination = {}


# 爬取tiktok主页
def get_tiktok_user_data(user_unique_id_list):
    warit_excel_data = {}
    for create_user in user_unique_id_list:
        if int(create_user.get("follower_cnt").get("value", 0)) < UserFilter.follower_count:
            # 粉丝数量太少,不爬取
            continue
        unique_id = create_user["handle"]["value"]
        # if redis_client.get(RedisKeyConstants.redis_user_info_key + unique_id) is not None:
        #     continue
        url = 'https://www.tiktok.com/@' + str(unique_id)
        # 请求头必须添加
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_0) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/71.0.3578.98 Safari/537.36',
        }
        global response
        try:
            response = requests.get(url=url, headers=headers, timeout=60)
        except Exception as ex:
            logging.logger.error(ex)
            logging.logger.error("\033[31m用户：" + unique_id + "TK官网无法访问，请检查网络!'\033[0m")
            continue
        # 获取页面原始编码格式
        page_text = response.text
        response.close()
        tree = etree.HTML(page_text)
        li_list = tree.xpath('//*[@id="__UNIVERSAL_DATA_FOR_REHYDRATION__"]/text()')
        try:
            if len(li_list) < 1:
                continue
            response_data = json.loads(li_list[0])
            user_detail = response_data.get('__DEFAULT_SCOPE__').get('webapp.user-detail')
            print("获取TK用户" + str(unique_id) + "主页数据\n")
            user_info = user_detail.get('userInfo')  # 用户基本信息 签名(邮箱) uniqueId 头像
            if user_info is None:
                continue
            user_data = user_info.get("user")
            user_state = user_info.get('stats')

            data = insertUtils.set_user_info_partner(user_data, user_state, create_user)
            warit_excel_data[unique_id] = {}
            warit_excel_data[unique_id]["creator_user"] = data["creator_user"]
            warit_excel_data[unique_id]["user_data"] = data["user_data"]
            warit_excel_data[unique_id]["user_stats"] = data["user_stats"]
        except Exception as ex:
            redis_client.incr(redis_key_tik_tok_request_error_num, 1)
            if int(redis_client.get(redis_key_tik_tok_request_error_num)) >= 5:
                logging.logger.error('TikTok官网失败超过次数，请检查网络!')
                break
            logging.logger.error(ex)
            continue
        redis_client.set(redis_key_tik_tok_request_error_num, 0)
    return warit_excel_data


# 从tiktok shop平台获取unique id列表
def get_tiktok_shop_user_unique_id():
    global creator_marketplace_pagination
    url = """https://api-partner-sg.tiktokshop.com/api/v1/oec/affiliate/creator/marketplace/4partner/find?user_language=zh-CN&partner_id=8651580378426936069&aid=360019&app_name=i18n_ecom_alliance&device_id=0&fp=verify_m3wsnw07_pkwQAiVL_SfIW_4eR5_9DOq_i6wtXllefUky&device_platform=web&cookie_enabled=true&screen_width=2195&screen_height=1235&browser_language=zh-CN&browser_platform=Win32&browser_name=Mozilla&browser_version=5.0+(Windows+NT+10.0%3B+Win64%3B+x64)+AppleWebKit%2F537.36+(KHTML,+like+Gecko)+Chrome%2F129.0.0.0+Safari%2F537.36&browser_online=true&timezone_name=Etc%2FGMT-8"""
    headers = {
        'accept': """application/json, text/plain, */*""",
        'accept-language': """en,zh-CN;q=0.9,zh;q=0.8""",
        'content-type': 'application/json',
        'cookie': """_ga=GA1.1.785161422.1732175154; _fbp=fb.1.1732175154686.851785016117250198; _tt_enable_cookie=1; _ttp=mTjpMGo3tkazKxhSeqvIiXy0uFC.tt.1; passport_csrf_token=c240a37432dcb7272d60836f5adfa2cf; passport_csrf_token_default=c240a37432dcb7272d60836f5adfa2cf; sid_guard=e463704005c7b7a3127e891e930cc61a%7C1732175527%7C5183996%7CMon%2C+20-Jan-2025+07%3A52%3A03+GMT; uid_tt=6e550bdcbeaf9b29441dcb484f54a85b6eba27084dfee4ce8f8d00e288c83ec9; uid_tt_ss=6e550bdcbeaf9b29441dcb484f54a85b6eba27084dfee4ce8f8d00e288c83ec9; sid_tt=e463704005c7b7a3127e891e930cc61a; sessionid=e463704005c7b7a3127e891e930cc61a; sessionid_ss=e463704005c7b7a3127e891e930cc61a; sid_ucp_v1=1.0.0-KDQ4ZjEyMDA3MWZjYzA3MzM1OWUxMGNlNzFmZmE1ODU2NzQyYmM4MGYKGwi3iI7i1Mi5n2cQp837uQYYofoVIAw4AUDrBxADGgZtYWxpdmEiIGU0NjM3MDQwMDVjN2I3YTMxMjdlODkxZTkzMGNjNjFh; ssid_ucp_v1=1.0.0-KDQ4ZjEyMDA3MWZjYzA3MzM1OWUxMGNlNzFmZmE1ODU2NzQyYmM4MGYKGwi3iI7i1Mi5n2cQp837uQYYofoVIAw4AUDrBxADGgZtYWxpdmEiIGU0NjM3MDQwMDVjN2I3YTMxMjdlODkxZTkzMGNjNjFh; msToken=uVbfePlBdQL3e3mfiUWfWfvZIf2oYWj4x63YHLXwy76HRFUrL30x8Jpy6rcWXx0cmsi2ux29T9q20PjsCFce1g-JEw7x_WRP97n3AlFrXudZQfeWDTso4fQ5QEfcwfE_27hwuNYA; odin_tt=5d038aca1e80a243323367dde70caa2303023b7c223826f3ee6334c8cba228130ab2bb91ffba97fd95323016ca58f852f0d2d13278e490de5695bd0274923c4a; _ga_BZBQ2QHQSP=GS1.1.1732525017.5.0.1732525017.0.0.0; TTSPC_Side_Menu_Role=0; ttwid=1%7C5pjKQSmC_JtrZB6_CQ41OG8qwOj2ZeJ1_v6TiTgpLbc%7C1732583709%7C6720ab3cdc4a454e59c22d020d7b66e1814db1740e9e17ea48742c30e8fb267c""",
        'priority': 'u=1, i',
        'origin': 'https://partner.tiktokshop.com',
        'referer': 'https://partner.tiktokshop.com/',
        'sec-ch-ua': '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': """Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36""",
    }
    # logging.logger.info("请求url：" + url)
    try:
        response_tiktok_shop_user_unique_ids = requests.post(url=url, json=creator_marketplace_pagination,
                                                             headers=headers, timeout=60)
        res_data = json.loads(response_tiktok_shop_user_unique_ids.text)
        if response_tiktok_shop_user_unique_ids.status_code != 200 or res_data.get("code") != 0:
            raise Exception("TikTok Shop平台获取失败，请检查网络!")
        response_tiktok_shop_user_unique_ids.close()
    except Exception as ex:
        logging.logger.error(ex)
        return [[], False]
    # 创作者Id列表
    creator_profile_list = res_data.get("creator_profile_list")
    # 分页数据
    next_pagination = res_data.get("next_pagination")
    if next_pagination.get("has_more"):
        pagination = {
            "size": 12,
            "page": next_pagination.get('next_page'),
            "next_item_cursor": next_pagination.get("next_item_cursor"),
            "search_key": next_pagination.get("search_key")
        }
        creator_marketplace_pagination["pagination"] = pagination
    return [creator_profile_list, next_pagination.get("has_more")]


def start():
    lock_key = "tiktok_shop_partner_center_PH_lock_search_key"
    search_key = "tiktok_shop_partner_center_PH_search_key"
    while True:
        lock = redisLock.acquire_lock(lock_key)
        enum = None
        try:
            if lock:
                enum = redis_client.blpop(search_key)
        except Exception as ex:
            logging.logger.error(ex)
        finally:
            redisLock.release_lock(lock_key, lock)
        if enum is None:
            break
        state = 2
        try:
            global tiktok_shop_request_enable
            global creator_marketplace_pagination
            # 初始化请求
            tiktok_shop_request_enable = True
            creator_marketplace_pagination = {
                "algorithm": 1,
                "filter_params": {},

                "pagination": {
                    "size": 12,
                    "page": 0
                },
                "query": str(enum[1], encoding='utf-8'),
                "query_type": 1
            }
            log_creator.logger.info(f"查询字段:{creator_marketplace_pagination}")
            # 处理数据爬虫
            user_list = []
            while tiktok_shop_request_enable:
                rsp_data = get_tiktok_shop_user_unique_id()
                tiktok_shop_request_enable = rsp_data[1]
                user_list.extend(rsp_data[0])
            if user_list is None:
                continue
            thread1 = pool.submit(get_tiktok_user_data, user_list)
            insert_num = insertUtils.insert_data(thread1.result(), user_list)
            log_creator.logger.info(
                f"关键字{str(enum[1], encoding='utf-8')}爬取数据总共{len(user_list)}条，其中存储{insert_num[0]}条,更新{insert_num[1]}。")
        except Exception as ex:
            log_creator.logger.error(ex)


if __name__ == "__main__":
    try:
        start()
    except Exception as ex:
        sendFeiShuMsg.setFeiShuMsg(f"越南数据爬取失败:{ex},请及时修复")
