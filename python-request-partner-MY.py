# coding:utf-8

import requests
from lxml import etree
import json
import time
import re
import redis
from concurrent.futures import ThreadPoolExecutor
import log
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
            resp_data_creator_data["creator_oecuid"] = create_user_info.get('creator_oecuid').get("value", "")
            resp_data_creator_data["user_id"] = user_data.get('id')
            resp_data_creator_data["handle"] = create_user_info.get('handle').get("value", "")
            if create_user_info.get('is_authorized') is not None:
                resp_data_creator_data["is_authorized"] = 1 if create_user_info.get('is_authorized').get("value",
                                                                                                         "") else 2
            if create_user_info.get('units_sold_range') is not None:
                resp_data_creator_data["units_sold_range"] = create_user_info.get('units_sold_range').get("value", "")
            if create_user_info.get('selection_region') is not None:
                resp_data_creator_data["selection_region"] = create_user_info.get('selection_region').get("value", "")
            if create_user_info.get('med_gmv_revenue_range') is not None:
                resp_data_creator_data["med_gmv_revenue_range"] = create_user_info.get('med_gmv_revenue_range').get(
                    "value",
                    "")
            # MCN机构
            resp_data_creator_data["creator_bind_mcn_name"] = ''
            if create_user_info.get('creator_bind_mcn_name') is not None:
                creator_bind_mcn_name = create_user_info.get('creator_bind_mcn_name')
                if creator_bind_mcn_name.get("value") is not None:
                    resp_data_creator_data["creator_bind_mcn_name"] = json.dumps(
                        create_user_info.get('creator_bind_mcn_name').get("value", ""))
            # 达人兴趣标签
            resp_data_creator_data["industry_groups"] = ''
            if create_user_info.get('industry_groups') is not None:
                industry_groups = create_user_info.get('industry_groups')
                if industry_groups.get('value') is not None:
                    resp_data_creator_data["industry_groups"] = json.dumps(
                        create_user_info.get('industry_groups').get("value", ""))
            if create_user_info.get('top_follower_gender') is not None:
                resp_data_creator_data["top_follower_gender"] = json.dumps(
                    create_user_info.get('top_follower_gender').get("value", ""))
            if create_user_info.get('top_follower_ages') is not None:
                resp_data_creator_data["top_follower_ages"] = ",".join(
                    create_user_info.get('top_follower_ages').get("value", ""))
            if create_user_info.get('follower_cnt') is not None:
                resp_data_creator_data["follower_cnt"] = create_user_info.get('follower_cnt').get("value", "")
            if create_user_info.get('top_follower_age') is not None:
                resp_data_creator_data["top_follower_age"] = json.dumps(
                    create_user_info.get('top_follower_age').get("value", ""))
            if create_user_info.get('video_avg_view_cnt') is not None:
                resp_data_creator_data["video_avg_view_cnt"] = create_user_info.get('video_avg_view_cnt').get("value",
                                                                                                              "")
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
    url = (
        """https://affiliate.tiktok.com/api/v1/oec/affiliate/creator/marketplace/find?user_language=en&aid=4331&app_name=i18n_ecom_alliance&device_id=0&fp=verify_m2eg07yc_UD0cGROh_rVmD_4obr_8X5q_rOfrNhCQ8wZe&device_platform=web&cookie_enabled=true&screen_width=2195&screen_height=1235&browser_language=en&browser_platform=Win32&browser_name=Mozilla&browser_version=5.0+(Windows+NT+10.0%3B+Win64%3B+x64)+AppleWebKit%2F537.36+(KHTML,+like+Gecko)+Chrome%2F129.0.0.0+Safari%2F537.36&browser_online=true&timezone_name=Etc%2FGMT-8&oec_seller_id=7495052999137724712&shop_region=MY&msToken=mu2ftbKUVY8FF4_xGnCl9H0UFWuzRbCbR0a3xxl6AT31b6ynA4rimelf0R2gs9R05GHKt9ax7ybQdf_Rx48FkTWuQpNXOkVw6Xqtkf-3kZY0DIlg5fiObUnKoRa7kWFhxF-VHQ==&X-Bogus=DFSzswVLB7D70ZrStQ-UU2Rt4e-9&_signature=_02B4Z6wo00001RrIemAAAIDANE-3SpDLruUayH7AACGi5a"""
    )
    headers = {
        'accept': """application/json, text/plain, */*""",
        'accept-language': """en,zh-CN;q=0.9,zh;q=0.8""",
        'content-type': 'application/json',
        'cookie': """_ga=GA1.1.2119822309.1721724000; _ttp=2jdjlkdhuiqpZbdLT0ZDriIsIii; _fbp=fb.1.1721724001066.849388382549850786; _ga_QQM0HPKD40=GS1.1.1722321809.2.0.1722321809.60.0.0; FPID=FPID2.2.T3fy47VLKLzQEdb0hI%2FuWPMsbB5Hc%2B4c8Mb38o1oYw4%3D.1721724000; _gtmeec=e30%3D; _ga_LVN0C1THGC=GS1.1.1722938987.6.0.1722938987.0.0.0; FPAU=1.2.170226212.1723175001; sid_ucp_v1_ads=1.0.0-KDcyZDMyYTIzZTExOWIyZTRmNDEwNzdlZjJjNjg2ZjM4YzMxMGZmNzYKGgiBiI3ik4fJr2QQr-fEtgYY-w8gDDgBQOsHEAMaA3NnMSIgOWFmNGYyNDM0NzIyMjY2Mjc0ZGNkYzg1NGIyOTI1MWU; ssid_ucp_v1_ads=1.0.0-KDcyZDMyYTIzZTExOWIyZTRmNDEwNzdlZjJjNjg2ZjM4YzMxMGZmNzYKGgiBiI3ik4fJr2QQr-fEtgYY-w8gDDgBQOsHEAMaA3NnMSIgOWFmNGYyNDM0NzIyMjY2Mjc0ZGNkYzg1NGIyOTI1MWU; sid_guard_ads=2cfbc6d63c7baa4ff9ddd55e3d79dd57%7C1726040561%7C5183999%7CSun%2C+10-Nov-2024+07%3A42%3A40+GMT; uid_tt_ads=08e098d8f19d07e5a67e26c347b8822480554264c5005280ead0c2a31d3c8a4a; uid_tt_ss_ads=08e098d8f19d07e5a67e26c347b8822480554264c5005280ead0c2a31d3c8a4a; sid_tt_ads=2cfbc6d63c7baa4ff9ddd55e3d79dd57; sessionid_ads=2cfbc6d63c7baa4ff9ddd55e3d79dd57; sessionid_ss_ads=2cfbc6d63c7baa4ff9ddd55e3d79dd57; passport_csrf_token=30b74988631f9038b3beb11ae1f7d5e6; passport_csrf_token_default=30b74988631f9038b3beb11ae1f7d5e6; user_oec_info=0a53f2c6d8be4c116cd054b354b640b3c5744ed8caa9fda61637ffaf1f42890242d20538d2de501a2dcd6874cf94ce9d37ba103b696fe4f7acd192ce69ece588491652cc6d06a185351378281078ae7c5416dbf78a1a490a3c313bdff644833bf649ecdd4020c046a99b17983003edd0ef0f5fa0d30612ca9e82b5b32d29f6823128af854af181da070da3e7b01d0cbb3b2d297d8e10d69add0d1886d2f6f20d220104fe69b54f; _m4b_theme_=new; _uetvid=2658938048cf11ef9cf767b0782f7319; d_ticket_ads=98c1fe1af694cc06f5cc41664db4cc66cda6a; passport_auth_status_ads=790eaadf1bbfbab082c9b50e0640499f%2C; passport_auth_status_ss_ads=790eaadf1bbfbab082c9b50e0640499f%2C; sso_auth_status_ads=96e5cb9721d7576d24c350b2bb18ace0; sso_auth_status_ss_ads=96e5cb9721d7576d24c350b2bb18ace0; sso_uid_tt_ads=2fb8d1b6139168b3a7c7f80a9c3f1419d78e1497a17a5634094dd1d90a93b97d; sso_uid_tt_ss_ads=2fb8d1b6139168b3a7c7f80a9c3f1419d78e1497a17a5634094dd1d90a93b97d; sso_user_ads=c62cb78ec9de3141e9d534f3a2798a63; sso_user_ss_ads=c62cb78ec9de3141e9d534f3a2798a63; sid_ucp_sso_v1_ads=1.0.0-KGFlYzA0YTQ2MmNmMjc1YmZhYzdmZGYxZmViMDU4YjU0N2Q2ZGZiMTgKIAiCiJqUh6XTrWQQho6yuAYY5B8gDDDHmu2iBjgCQPEHEAMaA215MiIgYzYyY2I3OGVjOWRlMzE0MWU5ZDUzNGYzYTI3OThhNjM; ssid_ucp_sso_v1_ads=1.0.0-KGFlYzA0YTQ2MmNmMjc1YmZhYzdmZGYxZmViMDU4YjU0N2Q2ZGZiMTgKIAiCiJqUh6XTrWQQho6yuAYY5B8gDDDHmu2iBjgCQPEHEAMaA215MiIgYzYyY2I3OGVjOWRlMzE0MWU5ZDUzNGYzYTI3OThhNjM; sid_guard_tiktokseller=51bcbb92e363de75208d1a21586f3a4a%7C1728874249%7C863997%7CThu%2C+24-Oct-2024+02%3A50%3A46+GMT; uid_tt_tiktokseller=3f136c0a5bc709e13f433cc3d95ec97b3682529a676e8cbf0215a4485b6f1090; uid_tt_ss_tiktokseller=3f136c0a5bc709e13f433cc3d95ec97b3682529a676e8cbf0215a4485b6f1090; sid_tt_tiktokseller=51bcbb92e363de75208d1a21586f3a4a; sessionid_tiktokseller=51bcbb92e363de75208d1a21586f3a4a; sessionid_ss_tiktokseller=51bcbb92e363de75208d1a21586f3a4a; sid_ucp_v1_tiktokseller=1.0.0-KGVmNDNmNjkxMTRjNmM1NDk3Y2ZjMGZiZTkxOWVkOGQ4ZjcwYTc5ODIKGgiCiJqUh6XTrWQQiY6yuAYY5B8gDDgCQPEHEAMaA3NnMSIgNTFiY2JiOTJlMzYzZGU3NTIwOGQxYTIxNTg2ZjNhNGE; ssid_ucp_v1_tiktokseller=1.0.0-KGVmNDNmNjkxMTRjNmM1NDk3Y2ZjMGZiZTkxOWVkOGQ4ZjcwYTc5ODIKGgiCiJqUh6XTrWQQiY6yuAYY5B8gDDgCQPEHEAMaA3NnMSIgNTFiY2JiOTJlMzYzZGU3NTIwOGQxYTIxNTg2ZjNhNGE; _ga_BZBQ2QHQSP=GS1.1.1728874189.16.1.1728874249.0.0.770461763; i18next=en; __partner_i18n_lang=en-US; tt_csrf_token=sc0KrbNN-oNb1xWlFkHOsOxQE5Oa13_7sClU; tt_chain_token=JC1NBn71HlnAwaZsbG7z9A==; ak_bmsc=C382E5471BB2BF5BCAFB409CA2AF5E0F~000000000000000000000000000000~YAAQD+wBF7nUUZSSAQAABa1/nhkzBAZI5PdS/8vSyH/wukjRwl5j6wc/M5NdR+pVMyvSa7eXrywA7P3dc59Ns3T04znxlI+AqFiAaR3HalZcLo+ePbBTSsObEqRH4Y9/6IUA/H2pQi/kajBbQ1PKuuxWM113zYuFgYnL9o0AAdhI0+EGRSuNw2P6iw9paMwuUSE3zLzvV1TUJDMkwL78ImpoXRBj+j1nsfoUDropZTHVKiCIlzbXzYP/CbKuTi7LaMYOuKniGIZ4Uk987WdytMylVIwAxU6pnbV2xmIBiHl1SIeY1ML0uS2WgzDInVd190J85eDYld3VZ0CmWhHwDAU9xD9SPndBz2ljq2XJw2E4icwpo6u//+nkL/1Fsk4Unt36NlwOCB1TIm7F; s_v_web_id=verify_m2eg07yc_UD0cGROh_rVmD_4obr_8X5q_rOfrNhCQ8wZe; bm_sv=7A2623C20177C5BC7801C8FB256B2BD4~YAAQTaXcF8dP552SAQAAHvetnhlF8lt3BO30hmUgNfkYf3vbvxe/TxyXvwHo2GjHn0mV0dTMdqnXJoIKb3l8An2FMwtQAYMMygLAbI28v+QbkbSURcknoWaBcKkgwHMBFiSKh08tgnHs1R++khsrvFOmzTGLLtSqivvcFv6PHUOnHRZAhNPYopBKFzXx4ran/8nSeEFpmHRIApE+aXPWCPWw+w0T3y6NjAwvWumFV0W/TuYZcabxzPQqf/JhyqCF~1; ttwid=1%7CysRSXQfxnW_XfByHyJ2tT6v74ecB8fTEhlxg_rYxcpo%7C1729239104%7C48a98d75cf92c54bc869618bffbda488d8c79ae4eb5502bc7ba23c4eeb3f8641; msToken=0-8bn_9YqhfIu8dATXDQ3v_JdL8G_Z07zh337FLu-4Cjuce5OhTG2xFVEXkzq2iSdKexbWuBwLNJdR9LVJEfNAgZTdQxmDHoTzrIV6zS6eVjmi2aRtF9o8qu7bS1CudUQPbGutzbKiutBKRYctpKxCqm; msToken=tu7RtCC1HPFg4KJdciyywnjKcOV4OmG4m5bzb6cCKk5Dnwx1CkZTD5GVC-OcrZlzc4BiIOrIztZq3_JFRAm3eC72Eoe8RnTniM4P6-R40hfUnlSyuNlI31ry9PMMKpup0RvytA==; odin_tt=e6fd9473a4f95b06ae2affed9c3441375c56a2b3293f20b704ea03be05012cb92b4eb3b715ca8d629599e4a552ecd2bd975536b1cf0c3fade3e6fd82f746f183""",
        'priority': 'u=1, i',
        'origin': 'https://affiliate.tiktok.com',
        'referer': 'https://affiliate.tiktok.com/connection/creator?is_new_connect=0&is_new_user=0&shop_region=MY',
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


if __name__ == "__main__":
    lock_key = "tiktok_shop_partner_center_MY_lock_search_key"
    search_key = "tiktok_shop_partner_center_MY_search_key"
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
            sendFeiShuMsg.setFeiShuMsg(f"马来数据爬取失败:{ex},请及时修复")
