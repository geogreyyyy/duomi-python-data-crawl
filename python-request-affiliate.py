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

# 时间格式化
timeArray = time.localtime(time.time())
otherStyleTime = time.strftime("%Y%m%d", timeArray)
numStyleTime = time.strftime("%H%M%S", timeArray)
time_default_range = str(otherStyleTime)

parser = argparse.ArgumentParser(description='argparse into.')
parser.add_argument('--page', '-p', type=str, default="50", required=True, help="请输入爬取的数量(50倍数抓取)")
parser.add_argument('--categories', '-cate', type=str, default="", required=False, help="请输入爬取类型")
parser.add_argument('--currency', '-cur', type=str, default="", required=False, help="输入地区")
parser.add_argument('--region', '-re', type=str, default="", required=False, help="输入地区")
parser.add_argument('--time-type', '-tt', type=str, default="daily", required=False, help="爬取类型daily:日榜 weekly:周榜 "
                                                                                          "monthly:月榜")
parser.add_argument('--time-range', '-tr', type=str, default=time_default_range, required=False, help="爬取类型daily:日榜 "
                                                                                                      "weekly:周榜 "
                                                                                                      "monthly:月榜")
args = parser.parse_args()
pool = ThreadPoolExecutor(max_workers=8)

# redis初始化
redis_client = redis.Redis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, db=Config.REDIS_DB,
                           password=Config.REDIS_PASSWORD)
# redis异常状态
redis_key_error_num = RedisKeyConstants.redis_key_error_num
redis_key_response_num = RedisKeyConstants.redis_key_response_num
redis_key_tik_tok_request_error_num = RedisKeyConstants.redis_key_tik_tok_request_error_num
# redis请求状态
redis_key_tiktok_shop_num = RedisKeyConstants.redis_key_tiktok_shop_num
# 爬虫服务启动状态
affiliate_center_crawl_status = RedisKeyConstants.affiliate_center_crawl_status + "local"

# log初始化
logging = log.Logger("TikTok用户画像-" + str(otherStyleTime) + '.log', level='INFO')

# 全局状态变量
global tiktok_shop_request_enable
global creator_marketplace_pagination


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
            resp_data_user_stats["user_id"] = user_data.get('id')
            resp_data_user_data["id"] = user_data.get('id')
            resp_data_user_data["unique_id"] = user_data.get('uniqueId')
            resp_data_user_data["nickname"] = user_data.get('nickname')
            resp_data_user_data["avatar_larger"] = user_data.get('avatarLarger')
            resp_data_user_data["avatar_medium"] = user_data.get('avatarMedium')
            resp_data_user_data["avatar_thumb"] = user_data.get('avatarThumb')
            resp_data_user_data["region"] = user_data.get('region')
            resp_data_user_data["sec_uid"] = user_data.get('secUid')
            resp_data_user_data["bio_link"] = str(user_data.get('bioLink'))
            # create_user_info
            resp_data_creator_data["creator_oecuid"] = create_user_info.get('creator_oecuid')["value"]
            resp_data_creator_data["user_id"] = user_data.get('id')
            resp_data_creator_data["handle"] = create_user_info.get('handle')["value"]
            if create_user_info.get('is_authorized') is not None:
                resp_data_creator_data["is_authorized"] = 1 if create_user_info.get('is_authorized') else 2
            if create_user_info.get('units_sold_range') is not None:
                resp_data_creator_data["units_sold_range"] = create_user_info.get('units_sold_range')["value"]
            if create_user_info.get('selection_region') is not None:
                resp_data_creator_data["selection_region"] = create_user_info.get('selection_region')["value"]
            if create_user_info.get('med_gmv_revenue_range') is not None:
                resp_data_creator_data["med_gmv_revenue_range"] = create_user_info.get('med_gmv_revenue_range')["value"]
            if create_user_info.get('creator_bind_mcn_name') is not None:
                resp_data_creator_data["creator_bind_mcn_name"] = str(create_user_info.get('creator_bind_mcn_name'))
            if create_user_info.get('category') is not None:
                resp_data_creator_data["industry_groups"] = str(create_user_info.get('category'))
            if create_user_info.get('top_follower_gender') is not None:
                resp_data_creator_data["top_follower_gender"] = str(create_user_info.get('top_follower_gender'))
            if create_user_info.get('top_follower_ages') is not None:
                resp_data_creator_data["top_follower_ages"] = ",".join(create_user_info.get('top_follower_ages'))
            if create_user_info.get('follower_cnt') is not None:
                resp_data_creator_data["follower_cnt"] = create_user_info.get('follower_cnt')["value"]
            else:
                resp_data_creator_data["follower_cnt"] = "0"
            if create_user_info.get('top_follower_age') is not None:
                resp_data_creator_data["top_follower_age"] = str(create_user_info.get('top_follower_age'))
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
    # logging.logger.info(user_unique_id_list)
    for create_user in user_unique_id_list:
        unique_id = create_user["handle"]["value"]
        if redis_client.get("tiktok_user_info:" + unique_id) is not None:
            logging.logger.info(str(unique_id) + "已存在")
            continue
        url = 'https://www.tiktok.com/@' + str(unique_id)
        # 请求头必须添加
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_0) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/71.0.3578.98 Safari/537.36',
        }
        global response
        try:
            response = requests.get(url=url, headers=headers, timeout=20)
        except Exception as ex:
            logging.logger.error(ex)
            logging.logger.error("\033[31m用户：" + unique_id + "TK官网无法访问，请检查网络!'\033[0m")
            continue
        # 获取页面原始编码格式
        page_text = response.text
        tree = etree.HTML(page_text)
        li_list = tree.xpath('//*[@id="__UNIVERSAL_DATA_FOR_REHYDRATION__"]/text()')
        try:
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
            if int(redis_client.get(redis_key_tik_tok_request_error_num)) >= 20:
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
    url = ("https://affiliate-us.tiktok.com/api/v1/oec/affiliate/creator/marketplace/find?"
           "user_language=zh-CN"
           "&aid=4331"
           "&app_name=i18n_ecom_alliance"
           "&device_id=0"
           "&fp=verify_m023xkv5_dqlk3jVd_d2YM_4ICJ_9fOd_esDgfPNshxuL"
           "&device_platform=web"
           "&cookie_enabled=true"
           "&screen_width=1920"
           "&screen_height=1080"
           "&browser_language=zh-CN"
           "&browser_platform=Win32"
           "&browser_name=Mozilla"
           "&browser_version=5.0+(Windows+NT+10.0%3B+Win64%3B+x64)+AppleWebKit%2F537.36+(KHTML,+like+Gecko)+Chrome%2F127.0.0.0+Safari%2F537.36"
           "&browser_online=true"
           "&timezone_name=Asia%2FShanghai"
           "&oec_seller_id=7495851717600643812"
           "&shop_region=US"
           )
    headers = {
        'content-type': 'application/json',
        'accept': 'application/json, text/plain, */*',
        'cookie': "_ga=GA1.1.2017787004.1717412342; _ttp=2hMmVGp5N733yHWxjeeEOwQvZqh; _fbp=fb.1.1717412348927.2076271040; _ga_W44EJN0C49=GS1.1.1718354830.1.1.1718357356.0.0.0; tt_chain_token=swi2RjUX93vD8yJ8sqLVbg==; _m4b_theme_=new; ttwid=1%7CL4i8Yytq2XhFaLGR_1-A65pLMcOqB5PVrFdPlZ75Lx8%7C1724138813%7C19ade38df32b1caca73f5ee123b82f49e1a7adc19332a4572f173a90315e1908; passport_csrf_token=c2d5057396a9614e8871b87208d01789; passport_csrf_token_default=c2d5057396a9614e8871b87208d01789; _uetsid=90a6b4a05ec511efaf9ef9c26c973e3f; _uetvid=4b7f65103f3111ef961529bc3bbaad27; d_ticket_ads=9d4ae23f006c0ed094c960eaf6acc5ce9e302; passport_auth_status_ads=63d4745e72f120a54773776904934584%2C; passport_auth_status_ss_ads=63d4745e72f120a54773776904934584%2C; sso_auth_status_ads=e85fcac1c3d4bfc9e77c03a1105e1b29; sso_auth_status_ss_ads=e85fcac1c3d4bfc9e77c03a1105e1b29; sso_uid_tt_ads=8cb55a362804f934ce4e2672f0f66ea848dbb2ab11c03d2abf8af2f4acee88d4; sso_uid_tt_ss_ads=8cb55a362804f934ce4e2672f0f66ea848dbb2ab11c03d2abf8af2f4acee88d4; sso_user_ads=6ddfb62e76668c83358c6b348d4689d6; sso_user_ss_ads=6ddfb62e76668c83358c6b348d4689d6; sid_ucp_sso_v1_ads=1.0.0-KGMxOTJlNjkyMjgxYWY1MjdiZjJkMDMwZjJiZmE2Mzc5NTE0YzQ2Y2EKIAiBiJqMyNz1zmYQ4IyRtgYY5B8gDDCfrve0BjgCQPEHEAMaA3NnMSIgNmRkZmI2MmU3NjY2OGM4MzM1OGM2YjM0OGQ0Njg5ZDY; ssid_ucp_sso_v1_ads=1.0.0-KGMxOTJlNjkyMjgxYWY1MjdiZjJkMDMwZjJiZmE2Mzc5NTE0YzQ2Y2EKIAiBiJqMyNz1zmYQ4IyRtgYY5B8gDDCfrve0BjgCQPEHEAMaA3NnMSIgNmRkZmI2MmU3NjY2OGM4MzM1OGM2YjM0OGQ0Njg5ZDY; sid_guard_tiktokseller=ca98c20ab85f60f5fae290c5283d2f61%7C1724139105%7C863999%7CFri%2C+30-Aug-2024+07%3A31%3A44+GMT; uid_tt_tiktokseller=7006d75cdcce5c328c62e101acfdf31d18a425430e298994d74fc232c6268d9e; uid_tt_ss_tiktokseller=7006d75cdcce5c328c62e101acfdf31d18a425430e298994d74fc232c6268d9e; sid_tt_tiktokseller=ca98c20ab85f60f5fae290c5283d2f61; sessionid_tiktokseller=ca98c20ab85f60f5fae290c5283d2f61; sessionid_ss_tiktokseller=ca98c20ab85f60f5fae290c5283d2f61; sid_ucp_v1_tiktokseller=1.0.0-KDdhMzNjMzMxYTQxNmY1NjM5NjhkMzNlOTVmZjEwMGNjZGQ3OTYwOTcKGgiBiJqMyNz1zmYQ4YyRtgYY5B8gDDgCQPEHEAMaA3NnMSIgY2E5OGMyMGFiODVmNjBmNWZhZTI5MGM1MjgzZDJmNjE; ssid_ucp_v1_tiktokseller=1.0.0-KDdhMzNjMzMxYTQxNmY1NjM5NjhkMzNlOTVmZjEwMGNjZGQ3OTYwOTcKGgiBiJqMyNz1zmYQ4YyRtgYY5B8gDDgCQPEHEAMaA3NnMSIgY2E5OGMyMGFiODVmNjBmNWZhZTI5MGM1MjgzZDJmNjE; msToken=vdTUTFpB3sAnn2tAjuMrwznebgZLqNCXs-Qmrsy32_H7ANrV0iRzt59_94iovO4PF1gCgR7D5bCpfBrEb_ZArjdLF2WeXZP-KAYBGPm8jryxiYG5QNPeg66ZOg_jkH0o2elb7AyLHuOIbmRy9sIZD0c=; _ga_BZBQ2QHQSP=GS1.1.1724138806.19.1.1724139107.0.0.105043562; SELLER_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJVc2VySWQiOjczOTQzMDI0NDAxMjYxODY0OTcsIk9lY1VpZCI6NzQ5NTg1MTcxNzYwMDY0MzgxMiwiT2VjU2hvcElkIjo3NDk1ODUxNzE3NjAwNjQzODEyLCJTaG9wUmVnaW9uIjoiIiwiR2xvYmFsU2VsbGVySWQiOjc0OTU4NTE3MTc2MDA2NDM4MTIsIlNlbGxlcklkIjo3NDk1ODUxNzE3NjAwNjQzODEyLCJleHAiOjE3MjQyMjU1MTksIm5iZiI6MTcyNDEzODExOX0.kXSmTpWnePVR2oXc1WUO9AnQzyaFlgmz_hRoGlLsnXw; SHOP_ID=7394332989255386923; s_v_web_id=verify_m023xkv5_dqlk3jVd_d2YM_4ICJ_9fOd_esDgfPNshxuL; i18next=en; user_oec_info=0a53537ba17a2acbc5bebd5b5ed4dbaade86c4e1d3fb651c5947828ede8975a951cd3d341064e34019a966e81aa89456cdd190fa632b8be47609e6a40505553c1120413e0f011ee922d3aa5327fd174037121290581a490a3c9b7bf2b05d84b71bef0b857be27cb4a4a418f0dcc178b61920219680a6a2eb629baf5a3156acad8e562c3bc5cf64bb4f7593fb2757c55a5f7cf4e14610eaeed90d1886d2f6f20d2201048387b6ba; odin_tt=186e8aaad422377015bde73d6251afab1b1d7ff2884c41d176516ce445da53a5fa87e6a953ba37fd2275cce2f10cb8c1be4af167f2fd7650f7292a50748f8a56",
        'priority': 'u=1, i',
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "origin": "https://affiliate-us.tiktok.com",
        "referer": "https://affiliate-us.tiktok.com/connection/creator?shop_region=US",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "Windows",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin"
    }
    logging.logger.info("请求url：" + url)
    try:
        response_tiktok_shop_user_unique_ids = requests.post(url=url, json=creator_marketplace_pagination, headers=headers,
                                                             timeout=20)
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
    redis_client.incr(redis_key_tiktok_shop_num,
                      len(creator_profile_list) if creator_profile_list is not None else 0)  # 测试为一次12条
    if next_pagination.get("has_more"):
        pagination = {
            "size": 12,
            "page": next_pagination.get('next_page'),
            "next_item_cursor": next_pagination.get("next_item_cursor"),
            "search_key": next_pagination.get("search_key")
        }
        creator_marketplace_pagination["pagination"] = pagination
    return [creator_profile_list, next_pagination.get("has_more")]


if __name__ == "__main__":
    page = args.page
    while True:
        redis_client.set(affiliate_center_crawl_status, 1)
        lock = redisLock.acquire_lock(RedisKeyConstants.lock_search_key)
        enum = None
        if lock:
            enum = redis_client.blpop(RedisKeyConstants.data_crawl_search_key)
        redisLock.release_lock(RedisKeyConstants.lock_search_key, lock)
        if enum is None:
            redis_client.set(affiliate_center_crawl_status, 0)
            time.sleep(10)
            continue
        state = 2
        try:
            # redis状态初始化
            redis_client.set(redis_key_error_num, 0)
            redis_client.set(redis_key_response_num, 0)
            redis_client.set(redis_key_tik_tok_request_error_num, 0)
            redis_client.set(redis_key_tiktok_shop_num, 0)
            # 初始化请求
            tiktok_shop_request_enable = True
            creator_marketplace_pagination = {
                "pagination": {
                    "size": 12,
                    "page": 0
                },
                "filter_params": {},
                "algorithm": 1,
                "query": str(enum[1], encoding='utf-8'),
                "query_type": 1
            }
            # 开始计时
            t = time.time()
            # 处理数据爬虫
            user_list = []
            # 轮询分页
            while tiktok_shop_request_enable and int(redis_client.get(redis_key_tiktok_shop_num)) < int(page):
                try:
                    rsp_data = get_tiktok_shop_user_unique_id()
                    tiktok_shop_request_enable = rsp_data[1]
                    user_list.extend(rsp_data[0])
                except Exception as ex:
                    logging.logger.error(ex)
                # redis_client.set("test-unused-data", json.dumps(user_list))
            logging.logger.info(creator_marketplace_pagination)
            # 分批次爬取和写入
            thread_num = 8
            ranges = paginate_user_id_list(len(user_list), thread_num)
            for num in range(thread_num):
                result_data = user_list[ranges[num][0]:ranges[num][1]]
                ranges_for = paginate_user_id_list(len(result_data), 2)  # 再次细分线程2个
                thread1 = pool.submit(get_tiktok_user_data, result_data[ranges_for[0][0]:ranges_for[0][1]])
                thread2 = pool.submit(get_tiktok_user_data, result_data[ranges_for[1][0]:ranges_for[1][1]])
                insertUtils.insert_data(thread1.result(), result_data[ranges_for[0][0]:ranges_for[0][1]])
                insertUtils.insert_data(thread2.result(), result_data[ranges_for[1][0]:ranges_for[1][1]])
            logging.logger.info("爬取数据完成,查找关键词:" + str(enum[1], encoding='utf-8'))
            time.sleep(1)
            state = 3
        except Exception as ex:
            logging.logger.error(ex)
            state = 4
        finally:
            insertUtils.updateSearchKey(str(enum[1], encoding='utf-8'), state)
    pool.shutdown()
    redis_client.set(affiliate_center_crawl_status, 0)
