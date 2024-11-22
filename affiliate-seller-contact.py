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
    url = f"""https://affiliate.tiktok.com/api_sens/v1/affiliate/cmp/contact?creator_oecuid={data['creator_oecuid']}&shop_id=7495052999137724712&shop_region=MY&scene=10&user_language=en&aid=4331&app_name=i18n_ecom_alliance&device_id=0&fp=verify_m3mgk6zq_QVDoKXkp_qb6K_4yBV_902C_kiPrtzbYQ8kb&device_platform=web&cookie_enabled=true&screen_width=2195&screen_height=1235&browser_language=en&browser_platform=Win32&browser_name=Mozilla&browser_version=5.0+(Windows+NT+10.0%3B+Win64%3B+x64)+AppleWebKit%2F537.36+(KHTML,+like+Gecko)+Chrome%2F129.0.0.0+Safari%2F537.36&browser_online=true&timezone_name=Etc%2FGMT-8&oec_seller_id=7495052999137724712&shop_region=MY&msToken=32zHIyJLbxNzEfHXj6Lpl7dEAMTHqplkmX8oGMVyo-2pLWVhhJ5WSXKf9hyL_RkFgXO_JQJqXJ9n7eKc-DI2dMLU2jdQcjWtDJURwyxi1GF4Pj6r9Ac_shr0EBVHHRrczJIlwdQ5&X-Bogus=DFSzswVugQGANcSctKSGm2Rt4e5U&_signature=_02B4Z6wo00001wk6wWQAAIDCJ70MTUfv9YsJOsXAAKV.90"""
    # url = f"""https://affiliate.tiktok.com/api_sens/v1/affiliate/cmp/contact?creator_oecuid={data['creator_oecuid']}&shop_id=7495052999137724712&shop_region=MY&scene=11&shop_region=MY&oec_region=MY&oec_seller_id=7495052999137724712&user_language=en&aid=4068&app_name=i18n_ecom_alliance&device_id=0&fp=verify_m3o3rtwa_lVNlt83S_6zIC_4Gyy_8Een_jZtMpGsHuYdb&device_platform=web&cookie_enabled=true&screen_width=2195&screen_height=1235&browser_language=en&browser_platform=Win32&browser_name=Mozilla&browser_version=5.0+(Windows+NT+10.0%3B+Win64%3B+x64)+AppleWebKit%2F537.36+(KHTML,+like+Gecko)+Chrome%2F129.0.0.0+Safari%2F537.36&browser_online=true&timezone_name=Etc%2FGMT-8"""
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en,zh-CN;q=0.9,zh;q=0.8',
        'cookie': """_ga=GA1.1.2119822309.1721724000; _ga_QQM0HPKD40=GS1.1.1722321809.2.0.1722321809.60.0.0; FPID=FPID2.2.T3fy47VLKLzQEdb0hI%2FuWPMsbB5Hc%2B4c8Mb38o1oYw4%3D.1721724000; _ga_LVN0C1THGC=GS1.1.1722938987.6.0.1722938987.0.0.0; sid_guard_ads=2cfbc6d63c7baa4ff9ddd55e3d79dd57%7C1726040561%7C5183999%7CSun%2C+10-Nov-2024+07%3A42%3A40+GMT; passport_csrf_token=30b74988631f9038b3beb11ae1f7d5e6; passport_csrf_token_default=30b74988631f9038b3beb11ae1f7d5e6; i18next=en; tt_chain_token=IRLRGWE9a7UG1wXMbiTH7Q==; d_ticket_ads=b60a996f4218226c9cf695c963845d7bcf729; cookie-consent={%22ga%22:true%2C%22af%22:true%2C%22fbp%22:true%2C%22lip%22:true%2C%22bing%22:true%2C%22ttads%22:true%2C%22reddit%22:true%2C%22hubspot%22:true%2C%22version%22:%22v10%22}; user_oec_info=0a53e0becf9fc404ba68d5503da937be2e2f8daee8f5000da96286e62a4311a432abcd4b280c3324e19d7cb0ee44eee09b54602e98395dc7418224209c8e1eb72ca706a92ab11b98734f8951c1f30ca7c58fded8701a490a3c7f837b9a110a7b12d6de9b3600db8262e7663e6f7fbe931ad4630c066f05521958fb4defbdc9ffa77febe5e74c02aa338eb126aad0b49b1a3d0cfac010cca2e10d1886d2f6f20d2201041dd59a4b; s_v_web_id=verify_m3mgk6zq_QVDoKXkp_qb6K_4yBV_902C_kiPrtzbYQ8kb; _m4b_theme_=new; ttwid=1%7CXN50JUETBwDIB_MoX62xWQPfRX1tK29RsxB0zhaiTRA%7C1731900042%7Cd8fcb1af38f23a3d9cb7378e292b78dcaa3f8c3cb860b7b83f86bda22b21b310; _uetsid=180027a0a55c11efaf29e13b7d27a300; _uetvid=2658938048cf11ef9cf767b0782f7319; _tt_enable_cookie=1; FPAU=1.2.1732508012.1731900044; _ttp=2jdjlkdhuiqpZbdLT0ZDriIsIii.tt.1; passport_auth_status_ads=784b8b22c578f48bc5fbfc97a380895c%2C822551db8eac07d26c7f65f5cd537f88; passport_auth_status_ss_ads=784b8b22c578f48bc5fbfc97a380895c%2C822551db8eac07d26c7f65f5cd537f88; sso_auth_status_ads=8980733fe0712286a5f24a8eb75a5b4e; sso_auth_status_ss_ads=8980733fe0712286a5f24a8eb75a5b4e; sso_uid_tt_ads=f8e82efca3d003fccfcb994d61e1e0960bac4b30ef5110ac31658389079e21df; sso_uid_tt_ss_ads=f8e82efca3d003fccfcb994d61e1e0960bac4b30ef5110ac31658389079e21df; sso_user_ads=faa6d094f4ab3aa445074e00cd39438c; sso_user_ss_ads=faa6d094f4ab3aa445074e00cd39438c; sid_ucp_sso_v1_ads=1.0.0-KDIzYmQ0ZjZhOWVkYjllYjdjYmEwMTNjNTlhNjg4NDAyYTExZGE2ZWMKIAiCiJqUh6XTrWQQq-bquQYY5B8gDDDHmu2iBjgCQPEHEAMaA215MiIgZmFhNmQwOTRmNGFiM2FhNDQ1MDc0ZTAwY2QzOTQzOGM; ssid_ucp_sso_v1_ads=1.0.0-KDIzYmQ0ZjZhOWVkYjllYjdjYmEwMTNjNTlhNjg4NDAyYTExZGE2ZWMKIAiCiJqUh6XTrWQQq-bquQYY5B8gDDDHmu2iBjgCQPEHEAMaA215MiIgZmFhNmQwOTRmNGFiM2FhNDQ1MDc0ZTAwY2QzOTQzOGM; sid_guard_tiktokseller=2a05d79d167106fb326973f56492517a%7C1731900204%7C863999%7CThu%2C+28-Nov-2024+03%3A23%3A23+GMT; uid_tt_tiktokseller=4a0b7d1d73383106c7ab97ddd438b748317e768ec216ee90ae856a565b087e43; uid_tt_ss_tiktokseller=4a0b7d1d73383106c7ab97ddd438b748317e768ec216ee90ae856a565b087e43; sid_tt_tiktokseller=2a05d79d167106fb326973f56492517a; sessionid_tiktokseller=2a05d79d167106fb326973f56492517a; sessionid_ss_tiktokseller=2a05d79d167106fb326973f56492517a; sid_ucp_v1_tiktokseller=1.0.0-KDQ3YjRlMzM3NTIzNTA5NjliMTUzMTVmYzFmNjA5MjA1NjQ1NzgwOGUKGgiCiJqUh6XTrWQQrObquQYY5B8gDDgCQPEHEAMaA3NnMSIgMmEwNWQ3OWQxNjcxMDZmYjMyNjk3M2Y1NjQ5MjUxN2E; ssid_ucp_v1_tiktokseller=1.0.0-KDQ3YjRlMzM3NTIzNTA5NjliMTUzMTVmYzFmNjA5MjA1NjQ1NzgwOGUKGgiCiJqUh6XTrWQQrObquQYY5B8gDDgCQPEHEAMaA3NnMSIgMmEwNWQ3OWQxNjcxMDZmYjMyNjk3M2Y1NjQ5MjUxN2E; msToken=ZhS8J7STAihMS9WJW1dAVlhBipeNVHNoSFCDwchrjb_iReU3lSmu0cWUR_KAM3NrKIphvsATeKI1wRksK0TsAzVjfOJrDMshLIGftXWCKtANcjgbl8G8ALJexfQsZBs4VjGmUg==; _ga_BZBQ2QHQSP=GS1.1.1731900043.19.1.1731900205.0.0.1656875294; odin_tt=da23be223eaa88b135bd8f3786191a673d6c90af3f9ae047d2ec121e0b70aa36627793ce7439e526f9c5ee955ba1cf23c951f0fd5b54174ccf2673864cc09e5a; msToken=32zHIyJLbxNzEfHXj6Lpl7dEAMTHqplkmX8oGMVyo-2pLWVhhJ5WSXKf9hyL_RkFgXO_JQJqXJ9n7eKc-DI2dMLU2jdQcjWtDJURwyxi1GF4Pj6r9Ac_shr0EBVHHRrczJIlwdQ5""",
        # 'cookie': """_ga=GA1.1.2119822309.1721724000; _ga_QQM0HPKD40=GS1.1.1722321809.2.0.1722321809.60.0.0; FPID=FPID2.2.T3fy47VLKLzQEdb0hI%2FuWPMsbB5Hc%2B4c8Mb38o1oYw4%3D.1721724000; _ga_LVN0C1THGC=GS1.1.1722938987.6.0.1722938987.0.0.0; sid_guard_ads=2cfbc6d63c7baa4ff9ddd55e3d79dd57%7C1726040561%7C5183999%7CSun%2C+10-Nov-2024+07%3A42%3A40+GMT; passport_csrf_token=30b74988631f9038b3beb11ae1f7d5e6; passport_csrf_token_default=30b74988631f9038b3beb11ae1f7d5e6; i18next=en; tt_chain_token=IRLRGWE9a7UG1wXMbiTH7Q==; d_ticket_ads=b60a996f4218226c9cf695c963845d7bcf729; cookie-consent={%22ga%22:true%2C%22af%22:true%2C%22fbp%22:true%2C%22lip%22:true%2C%22bing%22:true%2C%22ttads%22:true%2C%22reddit%22:true%2C%22hubspot%22:true%2C%22version%22:%22v10%22}; user_oec_info=0a53e0becf9fc404ba68d5503da937be2e2f8daee8f5000da96286e62a4311a432abcd4b280c3324e19d7cb0ee44eee09b54602e98395dc7418224209c8e1eb72ca706a92ab11b98734f8951c1f30ca7c58fded8701a490a3c7f837b9a110a7b12d6de9b3600db8262e7663e6f7fbe931ad4630c066f05521958fb4defbdc9ffa77febe5e74c02aa338eb126aad0b49b1a3d0cfac010cca2e10d1886d2f6f20d2201041dd59a4b; s_v_web_id=verify_m3mgk6zq_QVDoKXkp_qb6K_4yBV_902C_kiPrtzbYQ8kb; _m4b_theme_=new; _uetvid=2658938048cf11ef9cf767b0782f7319; _tt_enable_cookie=1; FPAU=1.2.1732508012.1731900044; _ttp=2jdjlkdhuiqpZbdLT0ZDriIsIii.tt.1; passport_auth_status_ads=784b8b22c578f48bc5fbfc97a380895c%2C822551db8eac07d26c7f65f5cd537f88; passport_auth_status_ss_ads=784b8b22c578f48bc5fbfc97a380895c%2C822551db8eac07d26c7f65f5cd537f88; sso_auth_status_ads=8980733fe0712286a5f24a8eb75a5b4e; sso_auth_status_ss_ads=8980733fe0712286a5f24a8eb75a5b4e; sso_uid_tt_ads=f8e82efca3d003fccfcb994d61e1e0960bac4b30ef5110ac31658389079e21df; sso_uid_tt_ss_ads=f8e82efca3d003fccfcb994d61e1e0960bac4b30ef5110ac31658389079e21df; sso_user_ads=faa6d094f4ab3aa445074e00cd39438c; sso_user_ss_ads=faa6d094f4ab3aa445074e00cd39438c; sid_ucp_sso_v1_ads=1.0.0-KDIzYmQ0ZjZhOWVkYjllYjdjYmEwMTNjNTlhNjg4NDAyYTExZGE2ZWMKIAiCiJqUh6XTrWQQq-bquQYY5B8gDDDHmu2iBjgCQPEHEAMaA215MiIgZmFhNmQwOTRmNGFiM2FhNDQ1MDc0ZTAwY2QzOTQzOGM; ssid_ucp_sso_v1_ads=1.0.0-KDIzYmQ0ZjZhOWVkYjllYjdjYmEwMTNjNTlhNjg4NDAyYTExZGE2ZWMKIAiCiJqUh6XTrWQQq-bquQYY5B8gDDDHmu2iBjgCQPEHEAMaA215MiIgZmFhNmQwOTRmNGFiM2FhNDQ1MDc0ZTAwY2QzOTQzOGM; sid_guard_tiktokseller=2a05d79d167106fb326973f56492517a%7C1731900204%7C863999%7CThu%2C+28-Nov-2024+03%3A23%3A23+GMT; uid_tt_tiktokseller=4a0b7d1d73383106c7ab97ddd438b748317e768ec216ee90ae856a565b087e43; uid_tt_ss_tiktokseller=4a0b7d1d73383106c7ab97ddd438b748317e768ec216ee90ae856a565b087e43; sid_tt_tiktokseller=2a05d79d167106fb326973f56492517a; sessionid_tiktokseller=2a05d79d167106fb326973f56492517a; sessionid_ss_tiktokseller=2a05d79d167106fb326973f56492517a; sid_ucp_v1_tiktokseller=1.0.0-KDQ3YjRlMzM3NTIzNTA5NjliMTUzMTVmYzFmNjA5MjA1NjQ1NzgwOGUKGgiCiJqUh6XTrWQQrObquQYY5B8gDDgCQPEHEAMaA3NnMSIgMmEwNWQ3OWQxNjcxMDZmYjMyNjk3M2Y1NjQ5MjUxN2E; ssid_ucp_v1_tiktokseller=1.0.0-KDQ3YjRlMzM3NTIzNTA5NjliMTUzMTVmYzFmNjA5MjA1NjQ1NzgwOGUKGgiCiJqUh6XTrWQQrObquQYY5B8gDDgCQPEHEAMaA3NnMSIgMmEwNWQ3OWQxNjcxMDZmYjMyNjk3M2Y1NjQ5MjUxN2E; _ga_BZBQ2QHQSP=GS1.1.1731900043.19.1.1731900205.0.0.1656875294; tt_csrf_token=dW4Xxchs-h2rmdFjHv47qxCXX8-6sc2UvL64; s_v_web_id=verify_m3o3rtwa_lVNlt83S_6zIC_4Gyy_8Een_jZtMpGsHuYdb; msToken=gibHpyRNJJj5f9jcRLxf1Z8DU1dqihCzcswGVFK-yY0TrM1fxuxyWdra13GfdM-8UWEVIEpBju_UgoX4drTPFn9lDt_3gj6H0jdTFWODTolRbR6OPtqCKzKRxeEiCPAwtiZmyQSaTBY6-icYDBy_OcDGKw==; ttwid=1%7CXN50JUETBwDIB_MoX62xWQPfRX1tK29RsxB0zhaiTRA%7C1732003392%7C2994db52b5ff176571fd2b57722b01721bddc6198d744e706a8a39fb507dcee9; msToken=iCVo-jpP5Vddu_09B3WI9t05Dfg4kh6U9hOO4bfNDEVj8Mq-ezwOQYdZTBc6FUue9OKSx6kiZKRKYMsgUB1I6rJqHcftdT8KqBjM0r_TaktlrgahCZf8mD-pPpJ8daiiP2GwQpu8Rw==; odin_tt=318e67a24b79164e28356a25a284638d772b4cb175f358bd9053cacb14a1a4ceca5a6035b33fa7ee05a9f95fefd57e1d9a98be8f2fd26ef4282deff85f7de041""",
        'priority': """u=1, i""",
        'referer': """https://affiliate.tiktok.com/connection/creator/detail?cid=7494811913849309704&pair_source=author_recommend&enter_from=affiliate_find_creators&search_key=EwgV7culZf5KdtW28J+NEVK89qTn42RZHDXtT1ufNgw=&req_id=20241118060345E07C5C8B38E55F0198C8&query=&shop_region=MY""",
        'sec-ch-ua': '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
        'sec-ch-ua-mobile': """?0""",
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
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
        # 失败计数，超过10次失败结束
        getSQLDataUtils.resetErrorData(res_data, data['user_id'])
        if res_data.get('message') == 'too many request':
            raise Exception("too many request")
        redis_client.incr(redis_key_error_num, 1)
        return []
    redis_client.get(redis_key_error_num).decode()
    # 创作者Id列表
    return res_data.get("contact_info",[])


def start():
    lock_key = "seller_contact_get_id_lock_key"
    while True:
        lock = redisLock.acquire_lock(lock_key)
        user_data_list = []
        try:
            if lock:
                logging.logger.info("正在采集...")
                user_data_list = getSQLDataUtils.get_no_request_seller_contact_id_region("MY")
        except Exception as ex:
            logging.logger.error(ex)
        finally:
            redisLock.release_lock(lock_key, lock)
        if len(user_data_list) <= 0:
            break
        try:
            for data in user_data_list:
                response_data = get_tiktok_shop_user_unique_id(data)
                getSQLDataUtils.resetDataPartner(response_data, data.get('user_id', None))
        except Exception as ex:
            logging.logger.error(ex)
            if str(ex) == 'too many request':
                raise Exception("too many request")
        # break
        # 暂时睡眠10s
        # time.sleep(10)


if __name__ == "__main__":
    try:
        start()
    except Exception as ex:
        sendFeiShuMsg.setFeiShuMsg(f"二次爬取达人数据失败:{ex},请及时修复")
