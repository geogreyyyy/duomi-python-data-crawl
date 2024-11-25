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
logging = log.Logger("TikTok用户画像VN-" + str(otherStyleTime) + '.log', level='INFO')
log_creator = log.Logger('tiktok-shop-partner-VN.log', level='INFO')
# 全局状态变量
tiktok_shop_request_enable = True
creator_marketplace_pagination = {}


# 爬取tiktok主页
def get_tiktok_user_data(user_unique_id_list):
    warit_excel_data = {}
    for create_user in user_unique_id_list:

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
            if user_state.get("followerCount", 0) < UserFilter.follower_count:
                # 粉丝数量太少,不爬取
                continue
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
    url = (
        """https://api-partner-va.tiktokshop.com/api/v1/oec/affiliate/creator/marketplace/4partner/find?user_language=zh-CN&partner_id=8649608119911877382&aid=360019&app_name=i18n_ecom_alliance&device_id=0&fp=verify_m3r4yplb_1JWV1ETO_7FpA_4Br4_At4m_ByQqkwCMsuIK&device_platform=web&cookie_enabled=true&screen_width=1680&screen_height=1050&browser_language=zh-CN&browser_platform=MacIntel&browser_name=Mozilla&browser_version=5.0+(Macintosh%3B+Intel+Mac+OS+X+10_15_7)+AppleWebKit%2F537.36+(KHTML,+like+Gecko)+Chrome%2F120.0.0.0+Safari%2F537.36&browser_online=true&timezone_name=Asia%2FShanghai"""
    )
    headers = {
        'accept': """application/json, text/plain, */*""",
        'accept-language': """en,zh-CN;q=0.9,zh;q=0.8""",
        'content-type': 'application/json',
        'cookie': """_fbp=fb.1.1732179723303.409822655388522637; _tt_enable_cookie=1; _ttp=HyQlz4Q4bw_2y0TM69SaraHexbD.tt.1; _ga=GA1.1.107995720.1732179724; passport_csrf_token=4e0a1d01f3b196b3924231d28d48e854; passport_csrf_token_default=4e0a1d01f3b196b3924231d28d48e854; sid_guard=73c09abce126f65d00c139dfa9a1a3bc%7C1732179926%7C5183994%7CMon%2C+20-Jan-2025+09%3A05%3A20+GMT; uid_tt=fa2d04a8aa2f9babc50ddfb2c86f64fe0e3267c427126c6805e101b94112f352; uid_tt_ss=fa2d04a8aa2f9babc50ddfb2c86f64fe0e3267c427126c6805e101b94112f352; sid_tt=73c09abce126f65d00c139dfa9a1a3bc; sessionid=73c09abce126f65d00c139dfa9a1a3bc; sessionid_ss=73c09abce126f65d00c139dfa9a1a3bc; sid_ucp_v1=1.0.0-KGM2M2FiNDUzM2Y5MTg5MmFlYWU3NThjN2NiYzQ2YThiNWU3M2RhOGMKGQiGiIr8zezj8GUQ1u_7uQYYofoVOAFA6wcQAxoGbWFsaXZhIiA3M2MwOWFiY2UxMjZmNjVkMDBjMTM5ZGZhOWExYTNiYw; ssid_ucp_v1=1.0.0-KGM2M2FiNDUzM2Y5MTg5MmFlYWU3NThjN2NiYzQ2YThiNWU3M2RhOGMKGQiGiIr8zezj8GUQ1u_7uQYYofoVOAFA6wcQAxoGbWFsaXZhIiA3M2MwOWFiY2UxMjZmNjVkMDBjMTM5ZGZhOWExYTNiYw; msToken=p0fgJAW-VAgkCBmwuTVcgbrF8hoju4UbplavAwwT89RTMrLW6uSISsFHEqsxQOiUtAeE_ZLqMj4Phz-15PXjslTrZb2-ylUuxWXyvMsZV2FOWvDYK2GlZCb2TLjTFdLVI7j5_rM=; ttwid=1%7CV9cwEnH7MZpH1qBWAb4J36Bhh1chjFtQXmScMISv8Pk%7C1732182882%7C32a980acf70712ab55255046b7ead8f206ecb3124278b49bf6353a97a56f1cc4; TTSPC_Side_Menu_Role=7; csrf_session_id=3c3972a9c8917aeee544d514bb4ae674; _ga_BZBQ2QHQSP=GS1.1.1732179723.1.1.1732182884.0.0.0""",
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
    lock_key = "tiktok_shop_partner_center_VN_lock_search_key"
    search_key = "tiktok_shop_partner_center_VN_search_key"
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
