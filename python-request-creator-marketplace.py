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
redis_key_response_num = RedisKeyConstants.creator_marketplace_response_num
# redis请求状态
redis_key_tiktok_shop_num = RedisKeyConstants.redis_key_tiktok_shop_num

# log初始化
logging = log.Logger("TikTok用户画像-" + str(otherStyleTime) + '.log', level='INFO')

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
def get_tiktok_shop_user_unique_id(request_params):
    url = "https://creatormarketplace.tiktok.com/h/api/gateway/handler_get/"
    headers = {
        'content-type': 'application/json',
        'accept': 'application/json, text/plain, */*',
        'cookie': """passport_csrf_token=79c0238d91a14e415c99f41e911ea1c1; passport_csrf_token_default=79c0238d91a14e415c99f41e911ea1c1; _m4b_theme_=new; _ga=GA1.1.2119822309.1721724000; _ttp=2jdjlkdhuiqpZbdLT0ZDriIsIii; _fbp=fb.1.1721724001066.849388382549850786; csrftoken=rlyADXxfMCMZbQBZRXcVndL4rjT6Y0T8; lang=zh-Hans; locale=zh; star_language=zh; passport_auth_status_ads=df8247fe26e5122d14f0b2a6eea101cf%2Cc970ac1b00b939dd013b8e16b5efea25; passport_auth_status_ss_ads=df8247fe26e5122d14f0b2a6eea101cf%2Cc970ac1b00b939dd013b8e16b5efea25; sso_auth_status_ads=ffd6ff4f39adb261e6876a4358c7cbb6%2Caeb76bd77d681974d8c81db7e571d0c9%2Ca0097ff9a91d974d88643f6de8c9c833; sso_auth_status_ss_ads=ffd6ff4f39adb261e6876a4358c7cbb6%2Caeb76bd77d681974d8c81db7e571d0c9%2Ca0097ff9a91d974d88643f6de8c9c833; reauth_token=1.0.0-KDMyMTUzZGUzMGZkNzg5Nzc1NjRjOTA2YmUwZmNiNzI2MmJmMWY3ZjIIrwwQgYiN4pOHya9kSgVlbWFpbFCRxKG1BliQxKG1BmCAmp4BaARyB3VzZWFzdDU; reauth_token_ss=1.0.0-KDMyMTUzZGUzMGZkNzg5Nzc1NjRjOTA2YmUwZmNiNzI2MmJmMWY3ZjIIrwwQgYiN4pOHya9kSgVlbWFpbFCRxKG1BliQxKG1BmCAmp4BaARyB3VzZWFzdDU; _ga_QQM0HPKD40=GS1.1.1722321809.2.0.1722321809.60.0.0; tt_chain_token=APDkpkmjuhQjmkLvtvSUmQ==; FPID=FPID2.2.T3fy47VLKLzQEdb0hI%2FuWPMsbB5Hc%2B4c8Mb38o1oYw4%3D.1721724000; _gtmeec=e30%3D; _ga_LVN0C1THGC=GS1.1.1722938987.6.0.1722938987.0.0.0; FPAU=1.2.170226212.1723175001; msToken=SPEUHKKF40n2ssffYa3zoZY2dKJ_503pO8jnJcO15tX9l-G4ECzBkDy3wY1n27uCs3Km4SHpGorU-OogIk_Kcqs8iAgqGYG9Ty8-LwJu1wL9FvV6H5TDW5ajsMLz-sgkJtZE; _uetvid=2658938048cf11ef9cf767b0782f7319; _ga_BZBQ2QHQSP=GS1.1.1724039861.14.0.1724039863.0.0.1396643895; d_ticket_ads=a051596a45b0446be210dc83cf7a4d5ccda6a; sso_uid_tt_ads=e7a9705288b0dbe90734532bb2903a7104781c9357f3f34bb91d4b2c602f0bbb; sso_uid_tt_ss_ads=e7a9705288b0dbe90734532bb2903a7104781c9357f3f34bb91d4b2c602f0bbb; sso_user_ads=7555862dfffeb2ca171a597fa9dc0f1e; sso_user_ss_ads=7555862dfffeb2ca171a597fa9dc0f1e; sid_ucp_sso_v1_ads=1.0.0-KGRjZTFlOGUxMTliYjFjZjAxYzU1OTIwYzE5MDdhZmMzNTE1ZTc0MDEKIAiBiI3ik4fJr2QQ27abtgYY-w8gDDDPyPyiBjgBQOsHEAMaA3NnMSIgNzU1NTg2MmRmZmZlYjJjYTE3MWE1OTdmYTlkYzBmMWU; ssid_ucp_sso_v1_ads=1.0.0-KGRjZTFlOGUxMTliYjFjZjAxYzU1OTIwYzE5MDdhZmMzNTE1ZTc0MDEKIAiBiI3ik4fJr2QQ27abtgYY-w8gDDDPyPyiBjgBQOsHEAMaA3NnMSIgNzU1NTg2MmRmZmZlYjJjYTE3MWE1OTdmYTlkYzBmMWU; odin_tt=2fdbc67c83d19deeb8475ef54727d8434ec0c210efc2f327140cbaf902e9fe0ef2c856ba8a490f8ab9bb5223ee4056c07de6ebef59ee4488915da9bf9a9ff6f4; sid_guard_ads=295922743b27a4948bff1a59a2e1a933%7C1724308315%7C5183999%7CMon%2C+21-Oct-2024+06%3A31%3A54+GMT; uid_tt_ads=dcd98f35b3b16c520315722a4f110fc08fedde4932ed0557fd7b8d97ed2667c1; uid_tt_ss_ads=dcd98f35b3b16c520315722a4f110fc08fedde4932ed0557fd7b8d97ed2667c1; sid_tt_ads=295922743b27a4948bff1a59a2e1a933; sessionid_ads=295922743b27a4948bff1a59a2e1a933; sessionid_ss_ads=295922743b27a4948bff1a59a2e1a933; sid_ucp_v1_ads=1.0.0-KDA3NGUzZGFjYjg3YmI4NjllZDI5ZmRiYzI3YTZhMjQ5MWVhZDY5YWYKGgiBiI3ik4fJr2QQ27abtgYY-w8gDDgBQOsHEAMaA3NnMSIgMjk1OTIyNzQzYjI3YTQ5NDhiZmYxYTU5YTJlMWE5MzM; ssid_ucp_v1_ads=1.0.0-KDA3NGUzZGFjYjg3YmI4NjllZDI5ZmRiYzI3YTZhMjQ5MWVhZDY5YWYKGgiBiI3ik4fJr2QQ27abtgYY-w8gDDgBQOsHEAMaA3NnMSIgMjk1OTIyNzQzYjI3YTQ5NDhiZmYxYTU5YTJlMWE5MzM; tcm_customize_cookie=1724465226a3c376ed-eaef-4b47-b2d2-6ce8f6a431d4; tt_csrf_token=QWDUnBDc-zjuyu5EkhWi3UuOF26Z8TIzsck8; s_v_web_id=verify_m07yd596_EqGupJkz_rO4L_4hiq_8jt3_0TlZ2aUm5dG2; ttwid=1%7CPnQs3CWVGgyhErzY4hk9AcR7sI31mmkbg688TspbBB8%7C1724637162%7Ceaf8a75ba9c9a11527be683463c937bc1e7e360394689552f2952bd1dff144fc; qualification_verification_cookie="@D4DO7tS2BOD2DI03oqCdPBc8//HS3XWByQfuC1Ihnlg5BsUnHlv+qovC+4iEqYB+"; msToken=4tPti6d-XgQk-MIgZ6FzJ01vI_ydDMyPkPIfkMtbdYwqlBN73cLuvSWoDP9dvu4OCpB_SMua2wllhjHhLDTpIAXrqANuOZitipKp4IcZA5M1SDvbC_QLzJiqXn6Qx8xOFvEG""",
        'priority': 'u=1, i',
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0",
        "accept-language": "zh-CN,zh;q=0.9",
        "origin": "https://affiliate-us.tiktok.com",
        "referer": "https://creatormarketplace.tiktok.com/ad/market?audienceFrom=US",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "Windows",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "tcm-adv-id": "7397258496527532048",
        "x-csrftoken": "rlyADXxfMCMZbQBZRXcVndL4rjT6Y0T8",
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
        return [[], False]
    # User id 列表
    # user_id_list = res_data.get("data").get("all_creators")
    # 所有数据列表
    creators_msg = res_data.get("data").get("creators")
    # 下一页数据列表
    next_pagination = res_data.get("data").get("pagination")
    redis_client.get(redis_key_error_num).decode()
    return [creators_msg, next_pagination.get("has_more")]


if __name__ == "__main__":
    try:
        # redis状态初始化
        redis_client.set(redis_key_error_num, 0)
        redis_client.set(redis_key_response_num, 0)
        redis_client.set(redis_key_tiktok_shop_num, 0)
        # 初始化请求
        tiktok_shop_request_enable = True
        # 开始计时
        t = time.time()
        # 处理数据爬虫
        user_list = []
        # 轮询分页
        while tiktok_shop_request_enable:
            try:
                # 初始化页面
                page = redis_client.get(RedisKeyConstants.creator_marketplace_page_num)
                if page is None:
                    page = 1
                    redis_client.set(RedisKeyConstants.creator_marketplace_page_num, 1)
                else:
                    page = int(page)
                creator_marketplace_pagination = {
                    "page": page,
                    "limit": 24,
                    "sort_type": 2,
                    "audience_max_distri_region": "US",
                    "query": "",
                    "sort_field": "comp_rank",
                    "use_creator_v2": True,
                    "service_name": "search.AdTcmSearchService",
                    "service_method": "AuthorPlazaSearch"
                }
                request_params = creator_marketplace_pagination
                request_params["sign"] = execjs.compile(open('./utils/MD5.js', 'r', encoding='utf-8').read()).call('l',
                                                                                                                   creator_marketplace_pagination)
                request_params["aid"] = 2043
                rsp_data = get_tiktok_shop_user_unique_id(request_params)
                # 是否有下一页
                tiktok_shop_request_enable = rsp_data[1]
                # 用户列表，24条
                user_list.extend(rsp_data[0])
                if page >= 10:
                    break
                insertUtils.insert_data_creator_marketplace(data=user_list)
                redis_client.incr(RedisKeyConstants.creator_marketplace_page_num)

            except Exception as ex:
                logging.logger.error(ex)
        # redis_client.set("test-unused-data", json.dumps(user_list))
        # logging.logger.info(tiktok_shop_pagination)
        # 分批次爬取和写入
        # thread_num = 8
        # time.sleep(1)
    except Exception as ex:
        logging.logger.error(ex)
    pool.shutdown()
