# coding:utf-8

import requests
from lxml import etree
import json
import time
import re
import redis
from concurrent.futures import ThreadPoolExecutor
import log
import argparse
from utils import insertUtils
from config import RedisKeyConstants as RedisKeyConstants
from config import Config
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
redis_key_error_num = RedisKeyConstants.redis_key_error_num
redis_key_response_num = RedisKeyConstants.redis_key_response_num
redis_key_tik_tok_request_error_num = RedisKeyConstants.redis_key_tik_tok_request_error_num
# redis请求状态

# redis状态初始化
redis_client.set(redis_key_error_num, 0)
redis_client.set(redis_key_response_num, 0)
redis_client.set(redis_key_tik_tok_request_error_num, 0)

# log初始化
logging = log.Logger("TikTok用户画像-" + str(otherStyleTime) + '.log', level='INFO')
log_creator = log.Logger('tiktok-shop-partner.log', level='INFO')
# 全局状态变量
tiktok_shop_request_enable=True
creator_marketplace_pagination={}


# 设置用户属性
def set_user_info(user_data, user_stats, create_user_info):
    resp_data = {}
    if user_data is None:
        return {}
    else:
        resp_data_user_data = {}
        resp_data_user_stats = {}
        resp_data_creator_data = {}
        user_email = re.search(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',
                               user_data.get('signature'), 0)
        if user_email is not None:
            resp_data_user_data["signature"] = user_email.group()
        else:
            resp_data_user_data["signature"] = ""
        try:
            resp_data_user_data["id"] = user_data.get('id')
            resp_data_user_data["unique_id"] = user_data.get('uniqueId')
            resp_data_user_data["nickname"] = user_data.get('nickname')
            resp_data_user_data["avatar_larger"] = user_data.get('avatarLarger')
            resp_data_user_data["avatar_medium"] = user_data.get('avatarMedium')
            resp_data_user_data["avatar_thumb"] = user_data.get('avatarThumb')
            resp_data_user_data["region"] = user_data.get('region')
            resp_data_user_data["sec_uid"] = user_data.get('secUid')
            resp_data_user_data["bio_link"] = json.dumps(user_data.get('bioLink', ''))
            # create_user_info
            resp_data_creator_data["creator_oecuid"] = create_user_info.get('creator_oecuid')["value"]
            resp_data_creator_data["user_id"] = user_data.get('id')
            resp_data_creator_data["handle"] = create_user_info.get('handle')["value"]
            if create_user_info.get('is_authorized') is not None:
                resp_data_creator_data["is_authorized"] = 1 if create_user_info.get('is_authorized')["value"] else 2
            if create_user_info.get('units_sold_range') is not None:
                resp_data_creator_data["units_sold_range"] = create_user_info.get('units_sold_range')["value"]
            if create_user_info.get('selection_region') is not None:
                resp_data_creator_data["selection_region"] = create_user_info.get('selection_region')["value"]
            if create_user_info.get('med_gmv_revenue_range') is not None:
                resp_data_creator_data["med_gmv_revenue_range"] = create_user_info.get('med_gmv_revenue_range')["value"]
            # MCN机构
            resp_data_creator_data["creator_bind_mcn_name"] = ''
            if create_user_info.get('creator_bind_mcn_name') is not None:
                creator_bind_mcn_name = create_user_info.get('creator_bind_mcn_name')
                if creator_bind_mcn_name.get("value") is not None:
                    resp_data_creator_data["creator_bind_mcn_name"] = json.dumps(
                        create_user_info.get('creator_bind_mcn_name')["value"])
            # 达人兴趣标签
            resp_data_creator_data["industry_groups"] = ''
            if create_user_info.get('industry_groups') is not None:
                industry_groups = create_user_info.get('industry_groups')
                if industry_groups.get('value') is not None:
                    resp_data_creator_data["industry_groups"] = json.dumps(
                        create_user_info.get('industry_groups')["value"])
            if create_user_info.get('top_follower_gender') is not None:
                resp_data_creator_data["top_follower_gender"] = json.dumps(
                    create_user_info.get('top_follower_gender')["value"])
            if create_user_info.get('top_follower_ages') is not None:
                resp_data_creator_data["top_follower_ages"] = ",".join(
                    create_user_info.get('top_follower_ages')["value"])
            if create_user_info.get('follower_cnt') is not None:
                resp_data_creator_data["follower_cnt"] = create_user_info.get('follower_cnt')["value"]
            if create_user_info.get('top_follower_age') is not None:
                resp_data_creator_data["top_follower_age"] = json.dumps(
                    create_user_info.get('top_follower_age')["value"])
            if create_user_info.get('video_avg_view_cnt') is not None:
                resp_data_creator_data["video_avg_view_cnt"] = create_user_info.get('video_avg_view_cnt')["value"]
            if user_stats is not None:
                # '粉丝数量', '关注数量', '点赞数', '发布视频数量'
                resp_data_user_stats["follower_count"] = user_stats.get('followerCount')
                resp_data_user_stats["following_count"] = user_stats.get('followingCount')
                resp_data_user_stats["heart"] = user_stats.get('heart')
                resp_data_user_stats["heart_count"] = user_stats.get('heartCount')
                resp_data_user_stats["video_count"] = user_stats.get('videoCount')
                resp_data_user_stats["digg_count"] = user_stats.get('diggCount')
                resp_data_user_stats["friend_count"] = user_stats.get('friendCount')
                resp_data_user_stats["user_id"] = user_data.get('id')
        except Exception as ex:
            logging.logger.error(ex)
        finally:
            resp_data["creator_user"] = resp_data_creator_data
            resp_data["user_data"] = resp_data_user_data
            resp_data["user_stats"] = resp_data_user_stats
            return resp_data


# 爬取tiktok主页
def get_tiktok_user_data(user_unique_id_list):
    warit_excel_data = {}
    for create_user in user_unique_id_list:

        unique_id = create_user["handle"]["value"]
        if redis_client.get(RedisKeyConstants.redis_user_info_key + unique_id) is not None:
            continue
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
            data = set_user_info(user_data, user_state, create_user)
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
def get_tiktok_shop_user_unique_id():
    global creator_marketplace_pagination
    url = ("https://partner.us.tiktokshop.com/api/v1/oec/affiliate/creator/marketplace/4partner/find?"
           + "user_language=en-US"
           + "&partner_id=8648655559104498438"
           + "&aid=359713"
           + "&app_name=i18n_ecom_alliance"
           + "&device_id=0"
           + "&device_platform=web"
           + "&cookie_enabled=true"
           + "&screen_width=2195"
           + "&screen_height=1235"
           + "&browser_language=zh-CN"
           + "&browser_platform=Win32"
           + "&browser_name=Mozilla"
           + "&browser_version=5.0+(Windows+NT+10.0%3B+Win64%3B+x64)+AppleWebKit%2F537.36+(KHTML,+like+Gecko)+Chrome%2F128.0.0.0+Safari%2F537.36"
           + "&browser_online=true"
           + "&timezone_name=Etc%2FGMT-8"
           )
    headers = {
        'content-type': 'application/json',
        'accept': """application/json, text/plain, */*""",
        'accept-language': """application/json""",
        'cookie': """d_ticket=009415b8e8bb942a46bc33ad58afeafc6dc0a; user_oec_info=0a55eb297991b807b31335b31d1c3e59f2dfbc2a5a853bdf80ede57980066bd2bb1047e1a6a5934a90d135ac7279d1c6a07356176fc39276f2d3716a9f875669b57d08834c87e4c8c5f98f1517d74e0f82ef31ad83c8201a490a3cba2364180e8d2cfc1d2aeeea0f6dc09a852439463be98e705e44880bec512e2dd1d45c7e67060025147a4f551805a2c088a0193b317efb13e380d96210e4a4db0d1886d2f6f20d2201041280fca0; _tea_utm_cache_7670={%22campaign_id%22:7368932484958783000}; passport_csrf_token=d87b2f02b1f69c555a48d852471f462e; passport_csrf_token_default=d87b2f02b1f69c555a48d852471f462e; csrf_session_id=537c5b3208e14f20945ccbd128743366; sid_guard=bbc2571ad5ec9d81e3acc6df4cdba604%7C1729146872%7C4508781%7CSun%2C+08-Dec-2024+11%3A00%3A53+GMT; uid_tt=4b6e8ba46dbb49a72c9811635275778c5aaa1576da6ec07860c955ee5ca8f79b; uid_tt_ss=4b6e8ba46dbb49a72c9811635275778c5aaa1576da6ec07860c955ee5ca8f79b; sid_tt=bbc2571ad5ec9d81e3acc6df4cdba604; sessionid=bbc2571ad5ec9d81e3acc6df4cdba604; sessionid_ss=bbc2571ad5ec9d81e3acc6df4cdba604; sid_ucp_v1=1.0.0-KDg1NmQ2NGNjZjAzMGEzNjU1NWNkNmFkMmY1OGY0YjU4MGE3OTZkYTQKGwiGiLTkgsq2mGUQ-N_CuAYYofoVIAw4AUDrBxADGgZtYWxpdmEiIGJiYzI1NzFhZDVlYzlkODFlM2FjYzZkZjRjZGJhNjA0; ssid_ucp_v1=1.0.0-KDg1NmQ2NGNjZjAzMGEzNjU1NWNkNmFkMmY1OGY0YjU4MGE3OTZkYTQKGwiGiLTkgsq2mGUQ-N_CuAYYofoVIAw4AUDrBxADGgZtYWxpdmEiIGJiYzI1NzFhZDVlYzlkODFlM2FjYzZkZjRjZGJhNjA0; msToken=WR4k4Z3iI9DNap6v4kfq92gDawUU89Ww-09i4zOXjSnsNNsW2nS46kHYMD6PcJjRHtE7jRjhQjOZ0kx-U6bGO2l5aSIFYfrMwEdiVEQtRSdo1qDMo96uwAuT9KD34s2PiAVrMg==; TTSPC_Side_Menu_Role=7; _tea_utm_cache_614171={%22campaign_id%22:7426612135993674000}; ttwid=1%7CSVSU3BY9n4Kktj7_hEp3uL1gAv7jCJKVxHdqos7pKOM%7C1729234708%7Ccbfffda436497628cdc77fc178611d0eb7eb0e057341facd5e8b7f6cf52c88f0; odin_tt=c180caff2f755c4c20c99b65e9021962bca103b01c0661ac1a68cfacc1b14c69d494421963ddd9a8e76fd500baa270b278906a80757387c16b90768c4c96f199; i18next=en; msToken=YWClbJxZOWklkb58PeolU_ClHRlI85KjfyVW_pVxHd1Rz6HUjqbzgq6C86fWcVLlPnCEj8MpQZjjkpKlBLYggMetjVeJwXVs2IRBaxxPQx2WRAlDi8yboyHAV35R7KkudX_6gA==""",
        'priority': 'u=1, i',
        'origin': 'https://partner.us.tiktokshop.com',
        'referer': 'https://partner.us.tiktokshop.com/affiliate-cmp/creator?market=100',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': """Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36""",
    }
    # logging.logger.info("请求url：" + url)
    try:
        response_tiktok_shop_user_unique_ids = requests.post(url=url, json=creator_marketplace_pagination,
                                                             headers=headers, timeout=60)
        res_data = json.loads(response_tiktok_shop_user_unique_ids.text)
        if response_tiktok_shop_user_unique_ids.status_code != 200 or res_data.get("code") != 0:
            raise Exception("TikTok Shop平台获取失败，请检查网络!")
    except Exception as ex:
        logging.logger.error(ex)
        logging.logger.error("\033[31mTikTok Shop平台获取失败，请检查网络!'\033[0m")
        # 失败计数，超过10次失败结束
        redis_client.incr(redis_key_error_num, 1)
        return [[], False]
    redis_client.get(redis_key_error_num).decode()
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
    lock_key = "tiktok_shop_partner_center_lock_search_key"
    search_key = "tiktok_shop_partner_center_search_key"
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
            # 开始计时
            t = time.time()
            # 处理数据爬虫
            user_list = []
            while tiktok_shop_request_enable:
                rsp_data = get_tiktok_shop_user_unique_id()
                tiktok_shop_request_enable = rsp_data[1]
                user_list.extend(rsp_data[0])
            if user_list is None:
                continue
            # 固定8个线程
            insert_num = 0
            ranges = paginate_user_id_list(len(user_list), 2)
            thread1 = pool.submit(get_tiktok_user_data, user_list[ranges[0][0]:ranges[0][1]])
            insert_num = insert_num + insertUtils.insert_data(thread1.result(), user_list[ranges[0][0]:ranges[0][1]])
            thread2 = pool.submit(get_tiktok_user_data, user_list[ranges[1][0]:ranges[1][1]])
            insert_num = insert_num + insertUtils.insert_data(thread2.result(), user_list[ranges[1][0]:ranges[1][1]])
            log_creator.logger.info(
                f"关键字{str(enum[1], encoding='utf-8')}爬取数据总共{len(user_list)}条，其中存储{insert_num}条。")
        except Exception as ex:
            log_creator.logger.error(ex)


if __name__ == "__main__":
    try:
        start()
    except Exception as ex:
        sendFeiShuMsg.setFeiShuMsg(f"美区数据爬取失败:{ex},请及时修复")
