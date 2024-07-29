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
                resp_data_creator_data["is_authorized"] = 1 if create_user_info.get('is_authorized')["value"] else 2
            if create_user_info.get('units_sold_range') is not None:
                resp_data_creator_data["units_sold_range"] = create_user_info.get('units_sold_range')["value"]
            if create_user_info.get('selection_region') is not None:
                resp_data_creator_data["selection_region"] = create_user_info.get('selection_region')["value"]
            if create_user_info.get('med_gmv_revenue_range') is not None:
                resp_data_creator_data["med_gmv_revenue_range"] = create_user_info.get('med_gmv_revenue_range')["value"]
            if create_user_info.get('creator_bind_mcn_name') is not None:
                resp_data_creator_data["creator_bind_mcn_name"] = create_user_info.get('creator_bind_mcn_name')
            if create_user_info.get('industry_groups') is not None:
                resp_data_creator_data["industry_groups"] = create_user_info.get('industry_groups')
            if create_user_info.get('top_follower_gender') is not None:
                resp_data_creator_data["top_follower_gender"] = create_user_info.get('top_follower_gender')["value"]
            if create_user_info.get('top_follower_ages') is not None:
                resp_data_creator_data["top_follower_ages"] = ",".join(create_user_info.get('top_follower_ages')["value"])
            if create_user_info.get('follower_cnt') is not None:
                resp_data_creator_data["follower_cnt"] = create_user_info.get('follower_cnt')["value"]
            if create_user_info.get('top_follower_age') is not None:
                resp_data_creator_data["top_follower_age"] = create_user_info.get('top_follower_age')["value"]
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
    user_data_list = []
    user_stats_list = []
    creator_user_list = []
    # logging.logger.info(user_unique_id_list)
    for create_user in user_unique_id_list:
        unique_id = create_user["handle"]["value"]
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
            user_data_list.extend([data["user_data"]])
            user_stats_list.extend([data["user_stats"]])
            creator_user_list.extend([data["creator_user"]])
        except Exception as ex:
            redis_client.incr(redis_key_tik_tok_request_error_num, 1)
            if int(redis_client.get(redis_key_tik_tok_request_error_num)) >= 20:
                logging.logger.error('TikTok官网失败超过次数，请检查网络!')
                break
            logging.logger.error(ex)
            continue
        redis_client.set(redis_key_tik_tok_request_error_num, 0)
    warit_excel_data["user_data"] = user_data_list
    warit_excel_data["user_stats"] = user_stats_list
    warit_excel_data["creator_user"] = creator_user_list
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
    url = ("https://partner.us.tiktokshop.com/api/v1/oec/affiliate/creator/marketplace/4partner/find?"
           + "user_language=en"
           + "&partner_id=8648655559104498438"
           + "&aid=359713&app_name=i18n_ecom_alliance"
           + "&device_id=0&device_platform=web&cookie_enabled=true"
           + "&screen_width=2195"
           + "&screen_height=1235"
           + "&browser_language=zh-CN"
           + "&browser_platform=Win32"
           + "&browser_name=Mozilla"
           + "&browser_version=5.0+(Windows+NT+10.0%3B+Win64%3B+x64)+AppleWebKit%2F537.36+(KHTML,+like+Gecko)+Chrome%2F126.0.0.0+Safari%2F537.36"
           + "&browser_online=true"
           + "&timezone_name=Etc%2FGMT-8"
           )
    headers = {
        'content-type': 'application/json',
        'cookie': "passport_csrf_token=dba075294ddfc9d03b686b602be19940; passport_csrf_token_default=dba075294ddfc9d03b686b602be19940; csrf_session_id=ca5b61eff8b0af80707c95cf876e5ebc; shop_tiktok_lang=en; msToken=kAX3rEncCGYSowgOyR66LVC8ZQYPk_cvlQWI4u4l4HGmzE48Wf6F-LwSks9ekeThN4kGp_CUkUeQHhz08eLWcq4I1l-ZdLLjwb6iZq21kjeTlHo4hUUKMnPAvHX7aStgNR4QV0NDDQ==; _ga_BZBQ2QHQSP=GS1.1.1721987355.1.0.1721987355.0.0.0; _ga=GA1.1.598775795.1721987355; _fbp=fb.1.1721987355283.707109687568995495; _tt_enable_cookie=1; _ttp=r0MDjfAUEIGnxr3PhAbIsX8Pk2s; sid_guard=31636608f9291e0ba23d638a00485f04%7C1721987390%7C5183998%7CTue%2C+24-Sep-2024+09%3A49%3A48+GMT; uid_tt=b13d929cc8d1850bd6c5a39ee78ad3b0a25556c5f9f188c98f98deb9907e1015; uid_tt_ss=b13d929cc8d1850bd6c5a39ee78ad3b0a25556c5f9f188c98f98deb9907e1015; sid_tt=31636608f9291e0ba23d638a00485f04; sessionid=31636608f9291e0ba23d638a00485f04; sessionid_ss=31636608f9291e0ba23d638a00485f04; sid_ucp_v1=1.0.0-KDE5NmM0Mzk3OGQ1OTc0ZDNjNmY4MDZlMzc4MzU4ZWY3ZjQ0YmFhYjMKGwiRiIPI0O7jy2YQvuKNtQYYofoVIAw4AUDrBxADGgZtYWxpdmEiIDMxNjM2NjA4ZjkyOTFlMGJhMjNkNjM4YTAwNDg1ZjA0; ssid_ucp_v1=1.0.0-KDE5NmM0Mzk3OGQ1OTc0ZDNjNmY4MDZlMzc4MzU4ZWY3ZjQ0YmFhYjMKGwiRiIPI0O7jy2YQvuKNtQYYofoVIAw4AUDrBxADGgZtYWxpdmEiIDMxNjM2NjA4ZjkyOTFlMGJhMjNkNjM4YTAwNDg1ZjA0; msToken=3omLiou1AmfbIROjHaR_izADrwZ87DBvJxnutbc9cC4bbuOKMsyX69DNbo9WQiFCe3l7qR0b9jG_kteSu6KLvHB3QaxYgLGzdtWzCuj-1tI-aZCITw-mqvDY62owuCxA95HbOjLI; ttwid=1%7CPnQs3CWVGgyhErzY4hk9AcR7sI31mmkbg688TspbBB8%7C1721987391%7C281c598c8dd820e0d6da2774b5d28d22ac7ec73f98de362eb25e57901a610e03; i18next=en; odin_tt=a09235cfb7319aa80c882f8d0eb7470e16aab745fbba928f8d1fab090f893f2542469be3e0855db7766c7f5bf43b4fa13e4e540b5e1c6a0f261246e6aa4b3d4b",
        'priority': 'u=1, i',
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
    while tiktok_shop_request_enable and int(redis_client.get(redis_key_tiktok_shop_num)) < int(page):
        rsp_data = get_tiktok_shop_user_unique_id()
        tiktok_shop_request_enable = rsp_data[1]
        user_list.extend(rsp_data[0])
    # 固定8个线程
    ranges = paginate_user_id_list(len(user_list), 2)
    user_data_list = []
    user_stats_list = []
    creator_user_list = []
    thread1 = pool.submit(get_tiktok_user_data, user_list[ranges[0][0]:ranges[0][1]])
    user_data_list.extend(thread1.result()["user_data"])
    user_stats_list.extend(thread1.result()["user_stats"])
    creator_user_list.extend(thread1.result()["creator_user"])
    thread2 = pool.submit(get_tiktok_user_data, user_list[ranges[1][0]:ranges[1][1]])
    user_data_list.extend(thread2.result()["user_data"])
    user_stats_list.extend(thread2.result()["user_stats"])
    creator_user_list.extend(thread2.result()["creator_user"])
    # thread3 = pool.submit(get_tiktok_user_data, user_list[ranges[2][0]:ranges[2][1]])

    # result_data.extend(thread2.result())
    # result_data.extend(thread3.result())
    pool.shutdown()
    if len(user_data_list) == 0:
        logging.logger.error("爬取数据为空！不存储Excel")
    else:
        # excel.save_data_excel(result_data,
        #                       "TikTok用户画像-" + str(otherStyleTime) + "-" + str(numStyleTime) + "-" + str(len(
        #                           result_data)) + "条-(" + args.currency + ")")
        insertUtils.insert_user_stats(user_stats_list)
        insertUtils.insert_user_info(user_data_list)
        insertUtils.insert_creator_user(creator_user_list)

    logging.logger.info("爬取数据完成.")
    logging.logger.info(f'耗时:{time.time() - t:.4f}s')
