import requests
from lxml import etree
import json
import time
import re
import redis
import log
import argparse
from utils import insertUtils
from concurrent.futures import ThreadPoolExecutor
from config import RedisKeyConstants as RedisKeyConstants

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
redis_client = redis.Redis(host="localhost", port=6379, db=0)
# redis异常状态
redis_key_error_num = RedisKeyConstants.redis_key_error_num
redis_key_response_num = RedisKeyConstants.redis_key_response_num
redis_key_tik_tok_request_error_num = RedisKeyConstants.redis_key_tik_tok_request_error_num
# redis请求状态
redis_key_tiktok_shop_num = RedisKeyConstants.redis_key_tiktok_shop_num
# 爬虫服务启动状态
affiliate_center_crawl_status = RedisKeyConstants.affiliate_center_crawl_status+"local"

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
            else:
                resp_data_creator_data["follower_cnt"] = "0"
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
           "user_language=en"
           "&aid=4331"
           "&app_name=i18n_ecom_alliance"
           "&device_id=0"
           "&fp=verify_lz7ub78r_uLa0en4t_kHvq_4feV_BISG_Ignl1ptV6EQt"
           "&device_platform=web"
           "&cookie_enabled=true"
           "&screen_width=1920"
           "&screen_height=1080"
           "&browser_language=zh-CN"
           "&browser_platform=Win32"
           "&browser_name=Mozilla"
           "&browser_version=5.0+(Windows+NT+10.0%3B+Win64%3B+x64)+AppleWebKit%2F537.36+(KHTML,+like+Gecko)+Chrome%2F127.0.0.0+Safari%2F537.36+Edg%2F127.0.0.0"
           "&browser_online=true"
           "&timezone_name=Etc%2FGMT-8"
           "&oec_seller_id=7495279362416609893"
           "&shop_region=US"
           )
    headers = {
        'content-type': 'application/json',
        'Cookie': "_m4b_theme_=new; passport_csrf_token=635392b69d95d2951284887128d76446; passport_csrf_token_default=635392b69d95d2951284887128d76446; _ttp=2jwpn2eT1L5yCp8yNilPMDDlxPx; ttwid=1%7CwXqPCsH4mgdnVtPmRW5UT_DkQ8bByEV1DmaL1JRrLyU%7C1722308157%7C929632783a88fbda3443226e8fd7a081e7b41459c05d0e791fa1e0a98096c619; _uetsid=3e4c15204e1f11efb75eab3e89612b20; _uetvid=3e4c4e204e1f11ef86b30ba1b751ff83; _ga=GA1.1.1616180698.1722308157; _fbp=fb.1.1722308157416.764324980187603569; d_ticket_ads=0ab1ca976e6a9ea39e3656de8c482bef5b2b7; sso_auth_status_ads=e564ae9cc9d507b305a80f3f112611ad; sso_auth_status_ss_ads=e564ae9cc9d507b305a80f3f112611ad; sso_uid_tt_ads=992a59863a207c29bfd45e3ca72865b3d9538c71677c3c6b1168501d2f805d88; sso_uid_tt_ss_ads=992a59863a207c29bfd45e3ca72865b3d9538c71677c3c6b1168501d2f805d88; sso_user_ads=40f26e6920c6c1fff86244cef08e5742; sso_user_ss_ads=40f26e6920c6c1fff86244cef08e5742; sid_ucp_sso_v1_ads=1.0.0-KDBlMmM3YzVkNDU4NTU1ZWE0ZWJkNDE3ODVlNzcyNTg3NjA0Mjc4MWQKIAiGiKCu1sy5-WQQlrKhtQYY5B8gDDCBzcunBjgBQOsHEAMaA3NnMSIgNDBmMjZlNjkyMGM2YzFmZmY4NjI0NGNlZjA4ZTU3NDI; ssid_ucp_sso_v1_ads=1.0.0-KDBlMmM3YzVkNDU4NTU1ZWE0ZWJkNDE3ODVlNzcyNTg3NjA0Mjc4MWQKIAiGiKCu1sy5-WQQlrKhtQYY5B8gDDCBzcunBjgBQOsHEAMaA3NnMSIgNDBmMjZlNjkyMGM2YzFmZmY4NjI0NGNlZjA4ZTU3NDI; sid_guard_tiktokseller=fdd02740247e5d247cc5e8c5c517bbeb%7C1722308887%7C863999%7CFri%2C+09-Aug-2024+03%3A08%3A06+GMT; uid_tt_tiktokseller=e1b0c54cf6569bf2f1176a88b75a08effec547331f23785853b936d716e777b7; uid_tt_ss_tiktokseller=e1b0c54cf6569bf2f1176a88b75a08effec547331f23785853b936d716e777b7; sid_tt_tiktokseller=fdd02740247e5d247cc5e8c5c517bbeb; sessionid_tiktokseller=fdd02740247e5d247cc5e8c5c517bbeb; sessionid_ss_tiktokseller=fdd02740247e5d247cc5e8c5c517bbeb; sid_ucp_v1_tiktokseller=1.0.0-KDQzMThjNGI0NjY0N2UxMGQyNDlkYWU5MjIzYzViZTM2OTY1ZGFmZjgKGgiGiKCu1sy5-WQQl7KhtQYY5B8gDDgBQOsHEAMaA3NnMSIgZmRkMDI3NDAyNDdlNWQyNDdjYzVlOGM1YzUxN2JiZWI; ssid_ucp_v1_tiktokseller=1.0.0-KDQzMThjNGI0NjY0N2UxMGQyNDlkYWU5MjIzYzViZTM2OTY1ZGFmZjgKGgiGiKCu1sy5-WQQl7KhtQYY5B8gDDgBQOsHEAMaA3NnMSIgZmRkMDI3NDAyNDdlNWQyNDdjYzVlOGM1YzUxN2JiZWI; msToken=MMfh7Hc3cu9s9XX-cgTOP64ljCpxCz1QvjLUwH1cgMzDgeeHJMiQ0BfH6MFrwC29o5msFPlbM5qait0hZIFPa0Llx_MPaideOr3ICLbcFOs=; _ga_BZBQ2QHQSP=GS1.1.1722308157.1.1.1722308888.0.0.0; SELLER_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJVc2VySWQiOjcyNzQxMjk2NzEzMzA0NjQ3NzQsIk9lY1VpZCI6NzQ5NTI3OTM2MjQxNjYwOTg5MywiT2VjU2hvcElkIjo3NDk1Mjc5MzYyNDE2NjA5ODkzLCJTaG9wUmVnaW9uIjoiIiwiR2xvYmFsU2VsbGVySWQiOjc0OTUyNzkzNjI0MTY2MDk4OTMsIlNlbGxlcklkIjo3NDk1Mjc5MzYyNDE2NjA5ODkzLCJleHAiOjE3MjIzOTUzMDAsIm5iZiI6MTcyMjMwNzkwMH0.e6Pznp-6m3LR73k8ncEpUY0j_co56-96-csAZgTOcmI; SHOP_ID=7274128858490700074; s_v_web_id=verify_lz7ub78r_uLa0en4t_kHvq_4feV_BISG_Ignl1ptV6EQt; user_oec_info=0a5302f3121405d80c52e605a78aac19d564a75e395f0d1470a6260617663f13ad59888e8617734402e1427de24f36e4a73ac8682e57a194913dc1e93461c3d1cbee9d15e3ae2b61e28b41fdbbd7f0fbb2bc6869671a490a3c55f5fde4b4a1103bc71a9e2aa7c62a427a74ad39af762737559b3defbd420bbe44971c5a51de964eb6fb519688b8160b6c54b65ae8f6574bfcffb33110f080d80d1886d2f6f20d220104a66f9ccb; i18next=en; odin_tt=cca347bad6b0d1d78d5840ad1cd6f9164e9c8626bac0c63699259f8d126722bb4c0d9347cc871f5fc01994ee231b2722aa641da8d154858211c19d3e0cd37e7c",
        'Priority': 'u=1, i',
    }
    logging.logger.info("请求url：" + url)
    try:
        response_tiktok_shop_user_unique_ids = requests.post(url=url, json=tiktok_shop_pagination, headers=headers,
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
        tiktok_shop_pagination["pagination"] = pagination
    return [creator_profile_list, next_pagination.get("has_more")]


if __name__ == "__main__":
    enums_request = ["ad", "dd", "dd", "dd", "ed", "fd", "gd", "hd", "id", "jd", "kd", "ld", "nd", "md",
                     "od", "pd",
                     "qd", "rd", "sd", "td",
                     "ud", "vd", "wd", "xd", "yd", "zd"]
    page = args.page
    redis_client.set(affiliate_center_crawl_status, 1)
    for enum in enums_request:
        # redis状态初始化
        redis_client.set(redis_key_error_num, 0)
        redis_client.set(redis_key_response_num, 0)
        redis_client.set(redis_key_tik_tok_request_error_num, 0)
        redis_client.set(redis_key_tiktok_shop_num, 0)
        # 初始化请求
        tiktok_shop_request_enable = True
        tiktok_shop_pagination = {
            "pagination": {
                "size": 12,
                "page": 0
            },
            "algorithm": 1,
            "query": str(enum),
            "query_type": 1
        }
        # 开始计时
        t = time.time()
        # 处理数据爬虫
        user_list = []
        # 轮询分页
        while tiktok_shop_request_enable and int(redis_client.get(redis_key_tiktok_shop_num)) < int(page):
            rsp_data = get_tiktok_shop_user_unique_id()
            tiktok_shop_request_enable = rsp_data[1]
            user_list.extend(rsp_data[0])
            # redis_client.set("test-unused-data", json.dumps(user_list))
        logging.logger.info(tiktok_shop_pagination)
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
        logging.logger.info("爬取数据完成,查找关键词:" + str(enum))
        logging.logger.info(f'耗时:{time.time() - t:.4f}s')
        time.sleep(10)
    pool.shutdown()
    redis_client.set(affiliate_center_crawl_status, 0)
