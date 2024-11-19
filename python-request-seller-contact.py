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


# 从tiktok shop平台获取unique id列表
def get_tiktok_shop_user_unique_id(data):
    # url = f"""https://api-partner-va.tiktokshop.com/api_sens/v1/affiliate/cmp/contact?creator_oecuid={data['creator_oecuid']}&scene=20&user_language=zh-CN&partner_id=8651580378426936069&aid=360019&app_name=i18n_ecom_alliance&device_id=0&fp=verify_m3mhobk1_fNC2jp8x_ohky_4f5K_9k9y_QAlSi7zXOZRh&device_platform=web&cookie_enabled=true&screen_width=2195&screen_height=1235&browser_language=zh-CN&browser_platform=Win32&browser_name=Mozilla&browser_version=5.0+(Windows+NT+10.0%3B+Win64%3B+x64)+AppleWebKit%2F537.36+(KHTML,+like+Gecko)+Chrome%2F129.0.0.0+Safari%2F537.36&browser_online=true&timezone_name=Etc%2FGMT-8&msToken=Ke_yxrVsd-GlEWMf7HA8j2pOAYId0AVx0Lxf8CaPpOlwZBxP8wy3svH-8Tb3xOXzmfHnjGv-rCEcQKGeQ29Nfp-kDeUzhMDDQarsaMKTifbERkC52PQ2WCxHkLDEZ6JPaR206VOX&X-Bogus=DFSzswVL/RvANHrStKVv909WcBnR&_signature=_02B4Z6wo00001cep8BQAAIDBx6nwFPnmw-3HqfSAABbS54"""
    url = f"""https://api-partner-va.tiktokshop.com/api_sens/v1/affiliate/cmp/contact?creator_oecuid={data['creator_oecuid']}&scene=11&user_language=zh-CN&partner_id=7166543041514505989&aid=360019&app_name=i18n_ecom_alliance&device_id=0&fp=verify_m3ntndwv_tM9oFLSk_Kfv1_498B_9OFY_xMU9YdeFnkrc&device_platform=web&cookie_enabled=true&screen_width=2195&screen_height=1235&browser_language=zh-CN&browser_platform=Win32&browser_name=Mozilla&browser_version=5.0+(Windows+NT+10.0%3B+Win64%3B+x64)+AppleWebKit%2F537.36+(KHTML,+like+Gecko)+Chrome%2F129.0.0.0+Safari%2F537.36&browser_online=true&timezone_name=Etc%2FGMT-8&msToken=S_2OJpgMLhQCIUwCMA2b8dBEZcK9bHObAcc3NgfAV4VcAnH5V-sh7rbM4OgGrIglCgKExz6REjTCK1oQmgRdf_MbyynN4RZAwc25uD2I9Wt2MN53LxkWSzE3L5Ir4q53l-3F0pB-&X-Bogus=DFSzswVuou0ANcSctKSjTsRt4e2m&_signature=_02B4Z6wo00001cb9a7QAAIDA6Hqmniu1AmnG.W8AABaGde"""
    headers = {
        'content-type': 'application/json',
        'Accept': """application/json, text/plain, */*""",
        'Accept-Language': """zh-CN,zh;q=0.9""",
        'Connection': """keep-alive""",
        # 'Cookie': """passport_csrf_token=9507ec650eaebf0d1e0d89ecae043372; passport_csrf_token_default=9507ec650eaebf0d1e0d89ecae043372; TTSPC_Side_Menu_Role=0; csrf_session_id=b40249d4f705250f1bf84f60d824d884; sid_guard=8bea05220b3a7e4fe38fc3f478b9e836%7C1731902126%7C5183996%7CFri%2C+17-Jan-2025+03%3A55%3A22+GMT; uid_tt=54b16ee05548907258d29a8b99997e757637ea8650529881b422f734a2ad543e; uid_tt_ss=54b16ee05548907258d29a8b99997e757637ea8650529881b422f734a2ad543e; sid_tt=8bea05220b3a7e4fe38fc3f478b9e836; sessionid=8bea05220b3a7e4fe38fc3f478b9e836; sessionid_ss=8bea05220b3a7e4fe38fc3f478b9e836; sid_ucp_v1=1.0.0-KDg2ZjQxM2ZiYTg4Yjg4NWE4YjI2ODFiYmUwY2YyOWYyNmNhMmFjYmIKGwi4iMmMj4m8m2cQrvXquQYYofoVIAw4AUDrBxADGgZtYWxpdmEiIDhiZWEwNTIyMGIzYTdlNGZlMzhmYzNmNDc4YjllODM2; ssid_ucp_v1=1.0.0-KDg2ZjQxM2ZiYTg4Yjg4NWE4YjI2ODFiYmUwY2YyOWYyNmNhMmFjYmIKGwi4iMmMj4m8m2cQrvXquQYYofoVIAw4AUDrBxADGgZtYWxpdmEiIDhiZWEwNTIyMGIzYTdlNGZlMzhmYzNmNDc4YjllODM2; msToken=aeCOXCvnEzBXZnG0WiyYs-5vLVOgfObCGN-0YfQNrDP7BbXJj5dK5FVtEEXzz3_eZoI1fXBY_pi45i2gIZ9OJHe6Gs4lTyjtMhIjuuUOl2PaW6u7EJpCiVSEEffkdOP7l8nzibm3; ttwid=1%7CLlkKwPu0MOnroTpQ2LyO9pHZH0Fa_yirNRxljyeVuQg%7C1731902127%7Cf824f755c3d8d3c12f2544ac39a3fb11c793ff4c08738adfdfd0260288c6eec9; odin_tt=dea12ab295c58799dd209a02761fb31058a956ba5efaad302234f755fffc54277316d59332feaaa50106aad4fc9433a9f6be8ea04b1aa9d98caa2f1013cf3284""",
        'Cookie': """_ga=GA1.1.765894570.1731398847; _fbp=fb.1.1731398847274.86887544282356373; _tt_enable_cookie=1; _ttp=wtRR3_WzIVIn6db38_QFhhUJZ3i; passport_csrf_token=17445e4cf3d2c984d0fbe23c1b693275; passport_csrf_token_default=17445e4cf3d2c984d0fbe23c1b693275; sid_guard=9df307a4f25d50d54ac52b24901b3a7d%7C1731399146%7C5183965%7CSat%2C+11-Jan-2025+08%3A11%3A51+GMT; uid_tt=fb6f21e40a654b558225d32ef3a3da24c9055671bc4f07a93077fb2f4e6acc5e; uid_tt_ss=fb6f21e40a654b558225d32ef3a3da24c9055671bc4f07a93077fb2f4e6acc5e; sid_tt=9df307a4f25d50d54ac52b24901b3a7d; sessionid=9df307a4f25d50d54ac52b24901b3a7d; sessionid_ss=9df307a4f25d50d54ac52b24901b3a7d; sid_ucp_v1=1.0.0-KDEyZTQ5MWU2MTZjYTdkMWM3MGJlZmY1MzJkOGUzODE3OGM3MGJkNzUKGwiGiKrEwcj8imcQ6pvMuQYYofoVIAw4AUDrBxADGgZtYWxpdmEiIDlkZjMwN2E0ZjI1ZDUwZDU0YWM1MmIyNDkwMWIzYTdk; ssid_ucp_v1=1.0.0-KDEyZTQ5MWU2MTZjYTdkMWM3MGJlZmY1MzJkOGUzODE3OGM3MGJkNzUKGwiGiKrEwcj8imcQ6pvMuQYYofoVIAw4AUDrBxADGgZtYWxpdmEiIDlkZjMwN2E0ZjI1ZDUwZDU0YWM1MmIyNDkwMWIzYTdk; msToken=p2wiaXACq9wINL8lPgZGvVf6j6N7DSzoEJq2clbwB_HDbz4MIIyc17qrZ7dj5OP8cGFobOuhDm9laTl1DC6UEtVTn2a3LC5nXPqLPrG85hnV3oaNOQ16bGRLolqi1XkhioVxP6CX; odin_tt=4cd25ce26519d942551accf664045a7c9e43213c11de9844d46a4b425700dd4d60c3b1bf51960fafd4278f9770aae91a75b868a47dd10277f3cb24de105249d6; _ga_BZBQ2QHQSP=GS1.1.1731398847.1.0.1731400033.0.0.0; ttwid=1%7CT8ubIZAVDpI73XLgDvfISyIg8aZeCNmaemqnP8SGzxY%7C1731982481%7C4f80ab8ef3ccecb65b6a52c2b8a07cf2bf2a6bc601691e36dc8face6da75f090; TTSPC_Side_Menu_Role=7; csrf_session_id=3fb9ef4b3d84a903bb0362ab9dc68c19""",
        'Origin': 'https://partner.tiktokshop.com',
        'Referer': 'https://partner.tiktokshop.com/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'User-Agent': """Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36""",
        'sec-ch-ua': '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
    # logging.logger.info("请求url：" + url)
    try:
        response_tiktok_shop_user_unique_ids = requests.get(url=url,
                                                            headers=headers, timeout=60)
        res_data = json.loads(response_tiktok_shop_user_unique_ids.text)
        if response_tiktok_shop_user_unique_ids.status_code != 200 or res_data.get("code") != 0:
            raise Exception(str(res_data))
    except Exception as ex:
        logging.logger.error(ex)
        logging.logger.error("\033[31mhttps://partner.tiktokshop.com/平台获取失败，请检查网络!'\033[0m")
        # 失败计数，超过10次失败结束
        getSQLDataUtils.resetErrorData(res_data, data['user_id'])
        if res_data.get('message') == 'too many request':
            raise Exception("too many request")
        redis_client.incr(redis_key_error_num, 1)
        return []
    redis_client.get(redis_key_error_num).decode()
    # 创作者Id列表
    return res_data.get("contact_info")


def start():
    lock_key = "seller_contact_get_id_lock_key"
    while True:
        lock = redisLock.acquire_lock(lock_key)
        user_data_list = []
        try:
            if lock:
                logging.logger.info("正在采集...")
                user_data_list = getSQLDataUtils.get_no_request_seller_contact_id()
        except Exception as ex:
            logging.logger.error(ex)
        finally:
            redisLock.release_lock(lock_key, lock)
        if len(user_data_list) <= 0:
            break
        try:
            for data in user_data_list:
                response_data = get_tiktok_shop_user_unique_id(data)
                getSQLDataUtils.resetData(response_data, data.get('user_id', None))
        except Exception as ex:
            logging.logger.error(ex)
            if str(ex) == 'too many request':
                raise Exception("too many request")
        # break
        # 暂时睡眠10s
        time.sleep(10)


if __name__ == "__main__":
    try:
        start()
    except Exception as ex:
        sendFeiShuMsg.setFeiShuMsg(f"二次爬取达人数据失败:{ex},请及时修复")
