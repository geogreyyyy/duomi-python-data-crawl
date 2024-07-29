import requests
from lxml import etree
import json
import time
import re
import redis
from concurrent.futures import ThreadPoolExecutor
import log
import argparse
import insertUtils

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
# 线程池初始化
pool = ThreadPoolExecutor(max_workers=8)
thread_num = 2

# redis初始化
redis_client = redis.Redis(host="localhost", port=6379, db=0)
redis_key_name = "python_data_crawl"
# redis异常状态
redis_key_error_num = redis_key_name + "_error_num"
redis_key_response_num = redis_key_name + "_response_num"
redis_key_tik_tok_request_error_num = redis_key_name + "_tik_tok_request_error_num"
# redis请求状态
redis_key_tiktok_shop_num = redis_key_name + "_tiktok_num"

# redis状态初始化
redis_client.set(redis_key_error_num, 0)
redis_client.set(redis_key_response_num, 0)
redis_client.set(redis_key_tik_tok_request_error_num, 0)
redis_client.set(redis_key_tiktok_shop_num, 0)

# log初始化
logging = log.Logger("TikTok用户画像-" + str(otherStyleTime) + '.log', level='INFO')

# 全局状态变量
global tiktok_shop_request_enable
global tiktok_shop_pagination


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
            resp_data_user_data["bio_link"] = user_data.get('bioLink')
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
                resp_data_creator_data["creator_bind_mcn_name"] = create_user_info.get('creator_bind_mcn_name')
            if create_user_info.get('category') is not None:
                resp_data_creator_data["industry_groups"] = create_user_info.get('category')
            if create_user_info.get('top_follower_gender') is not None:
                resp_data_creator_data["top_follower_gender"] = create_user_info.get('top_follower_gender')
            if create_user_info.get('top_follower_ages') is not None:
                resp_data_creator_data["top_follower_ages"] = ",".join(create_user_info.get('top_follower_ages'))
            if create_user_info.get('follower_cnt') is not None:
                resp_data_creator_data["follower_cnt"] = create_user_info.get('follower_cnt')["value"]
            if create_user_info.get('top_follower_age') is not None:
                resp_data_creator_data["top_follower_age"] = create_user_info.get('top_follower_age')
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
        if redis_client.get("tiktok_user_info:"+unique_id) is not None:
            continue
        url = 'https://www.tiktok.com/@' + str(unique_id)
        # 请求头必须添加
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_0) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/71.0.3578.98 Safari/537.36',
        }
        global response
        try:
            response = requests.get(url=url, headers=headers)
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
           "user_language=en"
           "&aid=4331"
           "&app_name=i18n_ecom_alliance"
           "&device_id=0"
           "&fp=verify_lyznqsz1_lfJCqLd2_2ujl_4eOy_BJHr_BV54Cjh6pMVr"
           "&device_platform=web"
           "&cookie_enabled=true"
           "&screen_width=2195"
           "&screen_height=1235"
           "&browser_language=zh-CN"
           "&browser_platform=Win32"
           "&browser_name=Mozilla"
           "&browser_version=5.0+(Windows+NT+10.0%3B+Win64%3B+x64)+AppleWebKit%2F537.36+(KHTML,+like+Gecko)+Chrome%2F126.0.0.0+Safari%2F537.36"
           "&browser_online=true"
           "&timezone_name=Etc%2FGMT-8"
           "&oec_seller_id=7495279362416609893"
           "&shop_region=US"
           )
    headers = {
        'content-type': 'application/json',
        'Cookie': "tt_chain_token=G4b1XFlsj2CRSfsarq78Sw==; passport_csrf_token=79c0238d91a14e415c99f41e911ea1c1; passport_csrf_token_default=79c0238d91a14e415c99f41e911ea1c1; _m4b_theme_=new; _ga=GA1.1.2119822309.1721724000; _ttp=2jdjlkdhuiqpZbdLT0ZDriIsIii; _fbp=fb.1.1721724001066.849388382549850786; passport_auth_status_ads=c970ac1b00b939dd013b8e16b5efea25%2C; passport_auth_status_ss_ads=c970ac1b00b939dd013b8e16b5efea25%2C; tt_csrf_token=tWXKEOUx-OyZkmPsq1SEenXC5YQZbxj3pdmw; s_v_web_id=verify_lyznqsz1_lfJCqLd2_2ujl_4eOy_BJHr_BV54Cjh6pMVr; sid_guard_ads=5a594394e1d6cf3b277dc31890fb4d2e%7C1721978189%7C5183999%7CTue%2C+24-Sep-2024+07%3A16%3A28+GMT; uid_tt_ads=9dddf659e029146d70876c9afa2bbc022937bac09ae925b2d112326c8bc0d72d; uid_tt_ss_ads=9dddf659e029146d70876c9afa2bbc022937bac09ae925b2d112326c8bc0d72d; sid_tt_ads=5a594394e1d6cf3b277dc31890fb4d2e; sessionid_ads=5a594394e1d6cf3b277dc31890fb4d2e; sessionid_ss_ads=5a594394e1d6cf3b277dc31890fb4d2e; ttwid=1%7C7PuXBYZ-PXnxeqQL22ylNS3i61w4rPxPXFVYAqKt91c%7C1722221606%7C4ce914feb52611bea4ba85e790ea12abf632ae1afe3bcdbd67b113f916bc6a84; _uetsid=c5112d004d5511ef86616f939ab30f0a; _uetvid=2658938048cf11ef9cf767b0782f7319; d_ticket_ads=2e9619e21b4615b7bf84fddf041362170f90b; sso_auth_status_ads=ffd6ff4f39adb261e6876a4358c7cbb6%2Caeb76bd77d681974d8c81db7e571d0c9; sso_auth_status_ss_ads=ffd6ff4f39adb261e6876a4358c7cbb6%2Caeb76bd77d681974d8c81db7e571d0c9; sso_uid_tt_ads=a084c6dd43a7b50ddc90ed8219d28f96d17b83b0a169fa2c693c9b1d340c5c45; sso_uid_tt_ss_ads=a084c6dd43a7b50ddc90ed8219d28f96d17b83b0a169fa2c693c9b1d340c5c45; sso_user_ads=f8de99290bcd2676c994633fd4413d02; sso_user_ss_ads=f8de99290bcd2676c994633fd4413d02; sid_ucp_sso_v1_ads=1.0.0-KDAwY2QxNzk1M2RkM2EwNmNiNjVlZTYwMjgyMzk4Mzk0NTAyMjlhYTAKIAiGiKCu1sy5-WQQzouctQYY5B8gDDCBzcunBjgBQOsHEAMaA3NnMSIgZjhkZTk5MjkwYmNkMjY3NmM5OTQ2MzNmZDQ0MTNkMDI; ssid_ucp_sso_v1_ads=1.0.0-KDAwY2QxNzk1M2RkM2EwNmNiNjVlZTYwMjgyMzk4Mzk0NTAyMjlhYTAKIAiGiKCu1sy5-WQQzouctQYY5B8gDDCBzcunBjgBQOsHEAMaA3NnMSIgZjhkZTk5MjkwYmNkMjY3NmM5OTQ2MzNmZDQ0MTNkMDI; sid_guard_tiktokseller=614b81eb8fafe34e6739faa3dc0da78e%7C1722222031%7C863999%7CThu%2C+08-Aug-2024+03%3A00%3A30+GMT; uid_tt_tiktokseller=92011a3f319704069c4998e13444a636f164791e5b9113acb298798d9e3b2905; uid_tt_ss_tiktokseller=92011a3f319704069c4998e13444a636f164791e5b9113acb298798d9e3b2905; sid_tt_tiktokseller=614b81eb8fafe34e6739faa3dc0da78e; sessionid_tiktokseller=614b81eb8fafe34e6739faa3dc0da78e; sessionid_ss_tiktokseller=614b81eb8fafe34e6739faa3dc0da78e; sid_ucp_v1_tiktokseller=1.0.0-KDg5ZjI2ZWM4NjRmM2I4ZWNhZjg5ZTkyM2UyMWYyNGIwNzM5NTcyNTEKGgiGiKCu1sy5-WQQz4uctQYY5B8gDDgBQOsHEAMaA3NnMSIgNjE0YjgxZWI4ZmFmZTM0ZTY3MzlmYWEzZGMwZGE3OGU; ssid_ucp_v1_tiktokseller=1.0.0-KDg5ZjI2ZWM4NjRmM2I4ZWNhZjg5ZTkyM2UyMWYyNGIwNzM5NTcyNTEKGgiGiKCu1sy5-WQQz4uctQYY5B8gDDgBQOsHEAMaA3NnMSIgNjE0YjgxZWI4ZmFmZTM0ZTY3MzlmYWEzZGMwZGE3OGU; msToken=pdZQskIm5SX5e-gPkal_9bl1VNWKEN1wn7LJIBjlzDZcdQufJ1Tl29XkgHD2ISm8gzv7jNX8FRW9jlreqTiXxGS6WNDaUvZ-C7PdmjR1NiRgYIa-f9k-Mu1MnbXUyTAlMdzSMpiDt9dNEPz3MAg=; _ga_BZBQ2QHQSP=GS1.1.1722221627.3.1.1722222031.0.0.0; odin_tt=0de2eeaf04476421e9ccc09f5451edea0dc8dfe72f539b80a1a153aabef4e2af2788ab220e8b6204837072a4438821ab66badd754e533b713b0b98bb9222bac8; user_oec_info=0a53172b1e28cbb23daa84a876a6d78ecd903ef3a21208c7a0d8d99f4be2180e02547a0e6b9f9b2a0a80596d4cde7de793f9e3eb4760b42a5fc8dd6d28d4eedf81b57c4bd5ef81075815627072d8861eecb4c0d1a01a490a3c22fb8d4bad8c0e9eb1c6319648da92da3da2138e07e0b76334931f4d336c2506dc76d9b218247e592f4c55312aa88754a7abb001fa37dba904fb634310fcf4d70d1886d2f6f20d220104eeeb08bd; i18next=en",
        'Priority': 'u=1, i',
    }
    logging.logger.info("请求url：" + url)
    try:
        response_tiktok_shop_user_unique_ids = requests.post(url=url, json=tiktok_shop_pagination, headers=headers)
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
    redis_client.incr(redis_key_tiktok_shop_num, len(creator_profile_list))  # 测试为一次12条
    if next_pagination.get("has_more"):
        pagination = {
            "size": 12,
            "page": next_pagination.get('next_page'),
            "next_item_cursor": next_pagination.get("next_item_cursor"),
            "search_key": next_pagination.get("search_key")
        }
        tiktok_shop_pagination["pagination"] = pagination
    return [creator_profile_list, next_pagination.get("has_more")]


if __name__ == "__main__":
    # 初始化请求
    tiktok_shop_request_enable = True
    tiktok_shop_pagination = {
        "pagination": {
            "size": 12,
            "page": 0
        },
        "algorithm": 1
    }
    page = args.page
    # 开始计时
    t = time.time()
    # 处理数据爬虫
    user_list = []
    aa = redis_client.get("data")
    if aa is not None:
        user_list = json.loads(aa)
    else:
        while tiktok_shop_request_enable and int(redis_client.get(redis_key_tiktok_shop_num)) < int(page):
            rsp_data = get_tiktok_shop_user_unique_id()
            tiktok_shop_request_enable = rsp_data[1]
            user_list.extend(rsp_data[0])
        redis_client.set("data", json.dumps(user_list))
    # 固定8个线程
    print(tiktok_shop_pagination)
    ranges = paginate_user_id_list(len(user_list), 2)
    user_data_list = []
    user_stats_list = []
    creator_user_list = []
    thread1 = pool.submit(get_tiktok_user_data, user_list[ranges[0][0]:ranges[0][1]])
    insertUtils.insert_data(thread1.result(), user_list[ranges[0][0]:ranges[0][1]])
    thread2 = pool.submit(get_tiktok_user_data, user_list[ranges[1][0]:ranges[1][1]])
    insertUtils.insert_data(thread2.result(), user_list[ranges[1][0]:ranges[1][1]])
    # thread3 = pool.submit(get_tiktok_user_data, user_list[ranges[2][0]:ranges[2][1]])

    # result_data.extend(thread2.result())
    # result_data.extend(thread3.result())
    pool.shutdown()
    logging.logger.info("爬取数据完成.")
    logging.logger.info(f'耗时:{time.time() - t:.4f}s')
