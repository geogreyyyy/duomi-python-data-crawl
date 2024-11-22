import json
import sys
import time

sys.path.append("..")
from MySqlCon import Mysql
from utils import replaceContactType


# 获取店铺Cookie
def get_cookie(shop_id):
    mysql = Mysql()
    sql = "select cookie from tiktok_shop_info where id = %(shop_id)s"
    result = mysql.getOne(sql, {"shop_id": shop_id})

    return result


# ----------------------------------------------以下为二次爬取使用SQL-----------------------------------------------
# 爬取成功状态
REQUEST_TRUE = 1
# 爬取中状态
REQUEST_ING = 2
# 爬取失败状态
REQUEST_ERROR = 3


# 获取没有邮箱信息的创作者达人
def get_not_info_create_user():
    mysql = Mysql()
    sql = """SELECT * FROM tiktok_creator_user_info WHERE user_id not in (select id from tiktok_user_info)"""


# 更新userId的状态为采集中
def setIdUpdateIng(userIdList):
    if len(userIdList) > 0:
        mysql = Mysql()
        sql = f"""UPDATE tiktok_user_info SET is_request = {REQUEST_ING} WHERE id in ({','.join(userIdList)})"""
        # print(sql)
        mysql.update(sql)
        mysql.dispose()


# 获取没有二次采集联系方式的达人创造者Id列表
def get_no_request_seller_contact_id():
    mysql = Mysql()
    sql = f"""SELECT user_id,creator_oecuid FROM tiktok_creator_user_info WHERE user_id IN ( SELECT id FROM tiktok_user_info WHERE is_request IS NULL AND region !='US' ORDER BY create_time DESC)   LIMIT 20"""
    request_data_list = mysql.getAll(sql)
    userIdList = []
    for data in request_data_list:
        userIdList.append("\"" + str(data['user_id']) + "\"")
    mysql.dispose()
    setIdUpdateIng(userIdList)
    # print(request_data_list)
    return request_data_list


# 获取没有二次采集联系方式的达人创造者Id列表 附带国家
def get_no_request_seller_contact_id_region(region):
    mysql = Mysql()
    sql = f"""SELECT user_id,creator_oecuid FROM tiktok_creator_user_info WHERE user_id IN ( SELECT id FROM tiktok_user_info WHERE is_request IS NULL AND region ='{region}' ORDER BY create_time DESC) LIMIT 20"""
    request_data_list = mysql.getAll(sql)
    userIdList = []
    for data in request_data_list:
        userIdList.append("\"" + str(data['user_id']) + "\"")
    setIdUpdateIng(userIdList)
    mysql.dispose()
    # print(request_data_list)
    return request_data_list


# 更新爬取联系方式
def update_user_contact(data, request_state):
    mysql = Mysql()
    whatsapp_exists = f"whatsapp= '{data.get('whatsapp')}'," if data.get('whatsapp') is not None else ""
    viber_exists = f"viber_number= '{data.get('viber_number')}'," if data.get('viber_number') is not None else ""
    facebook_exists = f"facebook_number= '{data.get('facebook_number')}'," if data.get(
        'facebook_number') is not None else ""
    zalo_exists = f"zalo_number= '{data.get('zalo_number')}'," if data.get('zalo_number') is not None else ""
    line_exists = f"line_number= '{data.get('line_number')}'," if data.get('line_number') is not None else ""
    email_exists = f"email= '{data.get('email')}'," if data.get('email') is not None else ""

    sql = f"""UPDATE tiktok_user_info SET 
    {whatsapp_exists} {viber_exists} {facebook_exists} {zalo_exists} {line_exists} {email_exists}
    other_contact='{data.get('other_contact', '')}',
    is_request = {request_state} ,
    update_by = 'python-tiktok-shop-partner',
    update_time = '{time.strftime('%Y-%m-%d %H:%M:%S')}'
    WHERE id = '{data.get('user_id', '')}' """
    mysql.update(sql)
    mysql.dispose()


# 格式化爬取数据 TAP后台
def resetDataPartner(response_data, user_id):
    save_data = {}
    if len(response_data) > 0 & user_id is not None:
        save_data['user_id'] = user_id
        save_data['other_contact'] = json.dumps(response_data)
        for field_data in response_data:
            field_value = replaceContactType.sellerContactMap.get(field_data['field'], None)
            if field_value is not None:
                save_data[field_value] = field_data['value']
        update_user_contact(save_data, REQUEST_TRUE)
        print(save_data)


# 格式化爬取数据 小店后台
def resetDataAffiliate(response_data, user_id):
    save_data = {}
    if len(response_data) > 0 & user_id is not None:
        save_data['user_id'] = user_id
        save_data['other_contact'] = json.dumps(response_data)
        for field_data in response_data:
            field_value = replaceContactType.affiliateContactMap.get(field_data['field'], None)
            if field_value is not None:
                save_data[field_value] = field_data['value']
        update_user_contact(save_data, REQUEST_TRUE)
        print(save_data)


# 格式化失败的爬取数据
def resetErrorData(response_data, user_id):
    save_data = {}
    if user_id is not None:
        save_data['user_id'] = user_id
        save_data['other_contact'] = json.dumps(response_data)
        update_user_contact(save_data, REQUEST_ERROR)
    print(save_data)


def tap_user_list(creator_oecuid, index=0):
    cookie_list = [
        {
            "url": f"""https://api-partner-va.tiktokshop.com/api_sens/v1/affiliate/cmp/contact?creator_oecuid={creator_oecuid}&scene=20&user_language=zh-CN&partner_id=8651580378426936069&aid=360019&app_name=i18n_ecom_alliance&device_id=0&fp=verify_m3mhobk1_fNC2jp8x_ohky_4f5K_9k9y_QAlSi7zXOZRh&device_platform=web&cookie_enabled=true&screen_width=2195&screen_height=1235&browser_language=zh-CN&browser_platform=Win32&browser_name=Mozilla&browser_version=5.0+(Windows+NT+10.0%3B+Win64%3B+x64)+AppleWebKit%2F537.36+(KHTML,+like+Gecko)+Chrome%2F129.0.0.0+Safari%2F537.36&browser_online=true&timezone_name=Etc%2FGMT-8&msToken=Ke_yxrVsd-GlEWMf7HA8j2pOAYId0AVx0Lxf8CaPpOlwZBxP8wy3svH-8Tb3xOXzmfHnjGv-rCEcQKGeQ29Nfp-kDeUzhMDDQarsaMKTifbERkC52PQ2WCxHkLDEZ6JPaR206VOX&X-Bogus=DFSzswVL/RvANHrStKVv909WcBnR&_signature=_02B4Z6wo00001cep8BQAAIDBx6nwFPnmw-3HqfSAABbS54""",
            "Cookie": """passport_csrf_token=9507ec650eaebf0d1e0d89ecae043372; passport_csrf_token_default=9507ec650eaebf0d1e0d89ecae043372; TTSPC_Side_Menu_Role=0; csrf_session_id=b40249d4f705250f1bf84f60d824d884; sid_guard=8bea05220b3a7e4fe38fc3f478b9e836%7C1731902126%7C5183996%7CFri%2C+17-Jan-2025+03%3A55%3A22+GMT; uid_tt=54b16ee05548907258d29a8b99997e757637ea8650529881b422f734a2ad543e; uid_tt_ss=54b16ee05548907258d29a8b99997e757637ea8650529881b422f734a2ad543e; sid_tt=8bea05220b3a7e4fe38fc3f478b9e836; sessionid=8bea05220b3a7e4fe38fc3f478b9e836; sessionid_ss=8bea05220b3a7e4fe38fc3f478b9e836; sid_ucp_v1=1.0.0-KDg2ZjQxM2ZiYTg4Yjg4NWE4YjI2ODFiYmUwY2YyOWYyNmNhMmFjYmIKGwi4iMmMj4m8m2cQrvXquQYYofoVIAw4AUDrBxADGgZtYWxpdmEiIDhiZWEwNTIyMGIzYTdlNGZlMzhmYzNmNDc4YjllODM2; ssid_ucp_v1=1.0.0-KDg2ZjQxM2ZiYTg4Yjg4NWE4YjI2ODFiYmUwY2YyOWYyNmNhMmFjYmIKGwi4iMmMj4m8m2cQrvXquQYYofoVIAw4AUDrBxADGgZtYWxpdmEiIDhiZWEwNTIyMGIzYTdlNGZlMzhmYzNmNDc4YjllODM2; msToken=aeCOXCvnEzBXZnG0WiyYs-5vLVOgfObCGN-0YfQNrDP7BbXJj5dK5FVtEEXzz3_eZoI1fXBY_pi45i2gIZ9OJHe6Gs4lTyjtMhIjuuUOl2PaW6u7EJpCiVSEEffkdOP7l8nzibm3; ttwid=1%7CLlkKwPu0MOnroTpQ2LyO9pHZH0Fa_yirNRxljyeVuQg%7C1731902127%7Cf824f755c3d8d3c12f2544ac39a3fb11c793ff4c08738adfdfd0260288c6eec9; odin_tt=dea12ab295c58799dd209a02761fb31058a956ba5efaad302234f755fffc54277316d59332feaaa50106aad4fc9433a9f6be8ea04b1aa9d98caa2f1013cf3284"""
        },
        {
            "url": f"""https://api-partner-va.tiktokshop.com/api_sens/v1/affiliate/cmp/contact?creator_oecuid={creator_oecuid}&scene=11&user_language=zh-CN&partner_id=7166543041514505989&aid=360019&app_name=i18n_ecom_alliance&device_id=0&fp=verify_m3ntndwv_tM9oFLSk_Kfv1_498B_9OFY_xMU9YdeFnkrc&device_platform=web&cookie_enabled=true&screen_width=2195&screen_height=1235&browser_language=zh-CN&browser_platform=Win32&browser_name=Mozilla&browser_version=5.0+(Windows+NT+10.0%3B+Win64%3B+x64)+AppleWebKit%2F537.36+(KHTML,+like+Gecko)+Chrome%2F129.0.0.0+Safari%2F537.36&browser_online=true&timezone_name=Etc%2FGMT-8&msToken=S_2OJpgMLhQCIUwCMA2b8dBEZcK9bHObAcc3NgfAV4VcAnH5V-sh7rbM4OgGrIglCgKExz6REjTCK1oQmgRdf_MbyynN4RZAwc25uD2I9Wt2MN53LxkWSzE3L5Ir4q53l-3F0pB-&X-Bogus=DFSzswVuou0ANcSctKSjTsRt4e2m&_signature=_02B4Z6wo00001cb9a7QAAIDA6Hqmniu1AmnG.W8AABaGde""",
            "Cookie": """_ga=GA1.1.765894570.1731398847; _fbp=fb.1.1731398847274.86887544282356373; _tt_enable_cookie=1; _ttp=wtRR3_WzIVIn6db38_QFhhUJZ3i; passport_csrf_token=17445e4cf3d2c984d0fbe23c1b693275; passport_csrf_token_default=17445e4cf3d2c984d0fbe23c1b693275; sid_guard=9df307a4f25d50d54ac52b24901b3a7d%7C1731399146%7C5183965%7CSat%2C+11-Jan-2025+08%3A11%3A51+GMT; uid_tt=fb6f21e40a654b558225d32ef3a3da24c9055671bc4f07a93077fb2f4e6acc5e; uid_tt_ss=fb6f21e40a654b558225d32ef3a3da24c9055671bc4f07a93077fb2f4e6acc5e; sid_tt=9df307a4f25d50d54ac52b24901b3a7d; sessionid=9df307a4f25d50d54ac52b24901b3a7d; sessionid_ss=9df307a4f25d50d54ac52b24901b3a7d; sid_ucp_v1=1.0.0-KDEyZTQ5MWU2MTZjYTdkMWM3MGJlZmY1MzJkOGUzODE3OGM3MGJkNzUKGwiGiKrEwcj8imcQ6pvMuQYYofoVIAw4AUDrBxADGgZtYWxpdmEiIDlkZjMwN2E0ZjI1ZDUwZDU0YWM1MmIyNDkwMWIzYTdk; ssid_ucp_v1=1.0.0-KDEyZTQ5MWU2MTZjYTdkMWM3MGJlZmY1MzJkOGUzODE3OGM3MGJkNzUKGwiGiKrEwcj8imcQ6pvMuQYYofoVIAw4AUDrBxADGgZtYWxpdmEiIDlkZjMwN2E0ZjI1ZDUwZDU0YWM1MmIyNDkwMWIzYTdk; msToken=p2wiaXACq9wINL8lPgZGvVf6j6N7DSzoEJq2clbwB_HDbz4MIIyc17qrZ7dj5OP8cGFobOuhDm9laTl1DC6UEtVTn2a3LC5nXPqLPrG85hnV3oaNOQ16bGRLolqi1XkhioVxP6CX; odin_tt=4cd25ce26519d942551accf664045a7c9e43213c11de9844d46a4b425700dd4d60c3b1bf51960fafd4278f9770aae91a75b868a47dd10277f3cb24de105249d6; _ga_BZBQ2QHQSP=GS1.1.1731398847.1.0.1731400033.0.0.0; ttwid=1%7CT8ubIZAVDpI73XLgDvfISyIg8aZeCNmaemqnP8SGzxY%7C1731982481%7C4f80ab8ef3ccecb65b6a52c2b8a07cf2bf2a6bc601691e36dc8face6da75f090; TTSPC_Side_Menu_Role=7; csrf_session_id=3fb9ef4b3d84a903bb0362ab9dc68c19"""
        },
        {
            "url": f"""https://api-partner-va.tiktokshop.com/api_sens/v1/affiliate/cmp/contact?creator_oecuid={creator_oecuid}&scene=11&user_language=zh-CN&partner_id=8651542679725968133&aid=360019&app_name=i18n_ecom_alliance&device_id=0&fp=verify_m3nt28da_VGvfSgw3_XrrG_4Cqv_AdjC_scQ7x7m9ruSD&device_platform=web&cookie_enabled=true&screen_width=2560&screen_height=1440&browser_language=zh-CN&browser_platform=Win32&browser_name=Mozilla&browser_version=5.0+(Windows+NT+10.0%3B+Win64%3B+x64)+AppleWebKit%2F537.36+(KHTML,+like+Gecko)+Chrome%2F130.0.0.0+Safari%2F537.36&browser_online=true&timezone_name=Asia%2FShanghai&msToken=k15XnU2PXFEUT6pehJ964zdfw52N9y5D4zZLcouZeSDaRBzcmZtITxSW8JczLzMOiN42NiIzEeDkcWpecGoGLQhb6NyJlCRxH43yvfyWefAgLBBa3XY1UKhtjStDkjWUjFsDwKkadg==&X-Bogus=DFSzswSuB7hANnBEtKNkvUkX95FK&_signature=_02B4Z6wo00001c7TOwAAAIDB-ff.XrDgSlXO0z-AABSK89""",
            "Cookie": """d_ticket=6939bdfd06624adbc4f189521525c71fd15ea; uid_tt=27085b5f9e6a677a34a77eb107ea2499b2d602d29e6b0c50e5f55a611d36bfb2; uid_tt_ss=27085b5f9e6a677a34a77eb107ea2499b2d602d29e6b0c50e5f55a611d36bfb2; sid_tt=cd23fbbb2ec0db815fe4a4c644728c83; sessionid=cd23fbbb2ec0db815fe4a4c644728c83; sessionid_ss=cd23fbbb2ec0db815fe4a4c644728c83; _ga=GA1.1.89193227.1719977808; _tt_enable_cookie=1; _ttp=xNdfrMdQ7VvKgDcWt4XLT3SP1LW; _ga_BZBQ2QHQSP=GS1.1.1719977807.1.1.1719977970.0.0.0; sid_guard=cd23fbbb2ec0db815fe4a4c644728c83%7C1730080728%7C5184000%7CFri%2C+27-Dec-2024+01%3A58%3A48+GMT; sid_ucp_v1=1.0.0-KDIyMTFkMzdmNjNhY2QwYTA3ZGMxMzcyOWZjNzAxMWZlOTc3NGJlZWQKIQiFiIfc6ve53GMQ2N_7uAYYofoVIAww5c_jnQY4AUDrBxADGgZtYWxpdmEiIGNkMjNmYmJiMmVjMGRiODE1ZmU0YTRjNjQ0NzI4Yzgz; ssid_ucp_v1=1.0.0-KDIyMTFkMzdmNjNhY2QwYTA3ZGMxMzcyOWZjNzAxMWZlOTc3NGJlZWQKIQiFiIfc6ve53GMQ2N_7uAYYofoVIAww5c_jnQY4AUDrBxADGgZtYWxpdmEiIGNkMjNmYmJiMmVjMGRiODE1ZmU0YTRjNjQ0NzI4Yzgz; odin_tt=7f74da236b6ebe641a6a65b92b2c7d387427d542d787e29e0c8ba6982899c71aab8f9c6c45fd5714a6b64d41df45118077c82d141e7e0e50d057f4409fb36dcd; TTSPC_Side_Menu_Role=0; csrf_session_id=36b313d06bf9f818ec25322277b0fc9c; ttwid=1%7CSM-i1GAmTqBe1MJw2PWqUOf5EHVtXYheRElnaQAhYX8%7C1731983076%7Ce0c3a8a838d1079efb1591fcde0869fead2fafcbb7f3552ec511449d15063f17; user_oec_info=0a55fbf1e20bb6a4113f911defb453a1dbe0336180f23a37c7edb2120fa63f963fded1d80ff2ce72ac1965dee4d34fb1569fb0ed6cb9ca2d7fc8d26373eb27650399fa17a6b5c1e29f0c8ecb91a79c87634e849173ae841a490a3c5ccdc83e3fcb0d1a5486d4f1f7d1428c772b78a2758c0340ff71f1e553d8029ddb51e37e786c75ecd5b92f83affcf33311be7ac0005b4bc035a9983e10f1eee10d1886d2f6f20d2201042db3e36e"""
        },
        {
            "url": f"""https://api-partner-sg.tiktokshop.com/api_sens/v1/affiliate/cmp/contact?creator_oecuid={creator_oecuid}&scene=20&user_language=zh-CN&partner_id=8651580378426936069&aid=360019&app_name=i18n_ecom_alliance&device_id=0&fp=verify_m3qyzysc_VO8uaL3b_EFE7_4sCp_9NMl_b0bNCSUJDGrK&device_platform=web&cookie_enabled=true&screen_width=2195&screen_height=1235&browser_language=zh-CN&browser_platform=Win32&browser_name=Mozilla&browser_version=5.0+(Windows+NT+10.0%3B+Win64%3B+x64)+AppleWebKit%2F537.36+(KHTML,+like+Gecko)+Chrome%2F129.0.0.0+Safari%2F537.36&browser_online=true&timezone_name=Etc%2FGMT-8&msToken=ChNONKAOs7qWOy0Jl7ZnTjyfgY653RvF6CpZzUvuvNCBHNyAscWk1sneBzIyHFlZJZ2L3nqP4fa6-JNM4ZrC3nA9AUQoCQneF4U8Qow_Rkz13Xt_O1CbL2fQCqUgwVoOWGdDlwByAw==&X-Bogus=DFSzswVuYOUANcSctKY5rz9WcBjL&_signature=_02B4Z6wo00001c4IWfwAAIDBzghZ.uhnrZXOCF1AABS-06""",
            "Cookie": """_fbp=fb.1.1732172735424.534481450963814615; _tt_enable_cookie=1; _ttp=htjFetfCB54xFtApXQs03DlpQED.tt.1; _ga_BZBQ2QHQSP=GS1.1.1732172742.1.0.1732172742.0.0.0; _ga=GA1.1.1113009093.1732172743; passport_csrf_token=4f52e595255011a16f8c0e70b9110678; passport_csrf_token_default=4f52e595255011a16f8c0e70b9110678; TTSPC_Side_Menu_Role=0; sid_guard=55d81ca382cb2ba833cdde0e79c015a2%7C1732173360%7C5183947%7CMon%2C+20-Jan-2025+07%3A15%3A07+GMT; uid_tt=6a30e1e7fdd74262db1421e4050f4148ab4e09c016c6329525af2c1b349a488a; uid_tt_ss=6a30e1e7fdd74262db1421e4050f4148ab4e09c016c6329525af2c1b349a488a; sid_tt=55d81ca382cb2ba833cdde0e79c015a2; sessionid=55d81ca382cb2ba833cdde0e79c015a2; sessionid_ss=55d81ca382cb2ba833cdde0e79c015a2; sid_ucp_v1=1.0.0-KDFiMTRhYzliZjFhODBlNWU3NGE2MTFhMDg5MGI5YmRhODg0MDQwODkKGwiGiL_Go7v8imcQsLz7uQYYofoVIAw4AUDrBxADGgZtYWxpdmEiIDU1ZDgxY2EzODJjYjJiYTgzM2NkZGUwZTc5YzAxNWEy; ssid_ucp_v1=1.0.0-KDFiMTRhYzliZjFhODBlNWU3NGE2MTFhMDg5MGI5YmRhODg0MDQwODkKGwiGiL_Go7v8imcQsLz7uQYYofoVIAw4AUDrBxADGgZtYWxpdmEiIDU1ZDgxY2EzODJjYjJiYTgzM2NkZGUwZTc5YzAxNWEy; msToken=n2UKiYYXc9kazEOEHGYi6Lh04touVUlMcQrN3MxnDwYVd_nIcGuBRkKPn-hRsWX6MJkIlPmD0cOay88YvJV8d1sULz0A3O8xQzNW26J8Mzi3FhADzGHnAqnlxW8NdoFc6pE8uPKkTA==; odin_tt=c40d41fa4b16c0b8db79ac24094f435b5f97a85f14b8d60bd7f4ecd54b02d4449d8f1c5504222386994338b0db964585c3bbb074df3e64cdee1be202a79c4940; ttwid=1%7C_tTy9A5t4M8rFFbNlKrcQCt6GVrLWf-ZntIVhHSIfNc%7C1732173319%7Ca033af7e7521aea2b2dd3938a760feebdddf43a55d7c9a00a62123738187edee"""
        },
        {
            "url": f"""https://api-partner-va.tiktokshop.com/api_sens/v1/affiliate/cmp/contact?creator_oecuid={creator_oecuid}&scene=20&user_language=zh-CN&partner_id=8651580312286038790&aid=360019&app_name=i18n_ecom_alliance&device_id=0&fp=verify_m3qzhyhx_MYhszxrZ_1BXn_4kUc_BW4w_XiRi6AUKJ3z9&device_platform=web&cookie_enabled=true&screen_width=2195&screen_height=1235&browser_language=zh-CN&browser_platform=Win32&browser_name=Mozilla&browser_version=5.0+(Windows+NT+10.0%3B+Win64%3B+x64)+AppleWebKit%2F537.36+(KHTML,+like+Gecko)+Chrome%2F129.0.0.0+Safari%2F537.36&browser_online=true&timezone_name=Etc%2FGMT-8&msToken=EcHnk52nbenKEAuZrlAtzvpRMxd6UGSgN5mF1qAe8s8_tbBripvHMeC3OBMslGbFRiK4CSti_zIr-eGorSqPbkb8VJTsGkOvHWk0zarIgG0tSBf9HllMTjwIWvSguOfd-9OFE1tB&X-Bogus=DFSzswVL1GvANHrStKYLrU9WcBrQ&_signature=_02B4Z6wo00001KzVrsgAAIDArNWuyyGvpDCs1apAAEwQc9""",
            "Cookie": """passport_csrf_token=131732750b879ddf962c0392017a03e4; passport_csrf_token_default=131732750b879ddf962c0392017a03e4; csrf_session_id=db7492ab17052f52e5460b3d581a9ab2; sid_guard=bee1004e611f96026b8ee052f8056712%7C1732173800%7C5183968%7CMon%2C+20-Jan-2025+07%3A22%3A48+GMT; uid_tt=becdeb2f50893be309f7a1d731d639dec98add2d0360ce3c5a783f14553b4bf7; uid_tt_ss=becdeb2f50893be309f7a1d731d639dec98add2d0360ce3c5a783f14553b4bf7; sid_tt=bee1004e611f96026b8ee052f8056712; sessionid=bee1004e611f96026b8ee052f8056712; sessionid_ss=bee1004e611f96026b8ee052f8056712; sid_ucp_v1=1.0.0-KDFhMWNlZDU3ZDhjOWY4Y2YyM2FhOTI2ZmI1YWJhNDM1YTBmMjgzNzkKGwiRiIPI0O7jy2YQ6L_7uQYYofoVIAw4AUDrBxADGgZtYWxpdmEiIGJlZTEwMDRlNjExZjk2MDI2YjhlZTA1MmY4MDU2NzEy; ssid_ucp_v1=1.0.0-KDFhMWNlZDU3ZDhjOWY4Y2YyM2FhOTI2ZmI1YWJhNDM1YTBmMjgzNzkKGwiRiIPI0O7jy2YQ6L_7uQYYofoVIAw4AUDrBxADGgZtYWxpdmEiIGJlZTEwMDRlNjExZjk2MDI2YjhlZTA1MmY4MDU2NzEy; msToken=ILxeJJWapC67xsIys0aOHNZk37dI0RsZKMyahcjA6xMsvqj0XkzQ4g4farfOROoAIe0bEoKmIwQ3a61MWAI2tbQzYTDNhRXOKkSmKiqTzDpuhhi-D3bw2HlovQ8OXhqAVeZbOmkN; TTSPC_Side_Menu_Role=0; ttwid=1%7Cwb1QRUz9JOvlR1qk2xSF3YdcLOf_Wuu8kBF7aoKd-tY%7C1732173912%7Ca83edf1be92cada2f728aab07561dd197e709ffd90491c362cf02f874d037fc8; odin_tt=98d683cfcb113df1fde8d651030c6b311f4b6cec2d5948ce285f38b87ed3dc95b81eca6ace61491b44120347e7fdc7405210622c8744a30af3ca3af6bfc8646f"""
        },
        {
            "url": f"""https://api-partner-va.tiktokshop.com/api_sens/v1/affiliate/cmp/contact?creator_oecuid={creator_oecuid}&scene=20&user_language=zh-CN&partner_id=8651580312286038790&aid=360019&app_name=i18n_ecom_alliance&device_id=0&fp=verify_m3r0fndq_IBr8w422_cNFp_4Lay_BqPI_oqYb6sRujqqn&device_platform=web&cookie_enabled=true&screen_width=2195&screen_height=1235&browser_language=zh-CN&browser_platform=Win32&browser_name=Mozilla&browser_version=5.0+(Windows+NT+10.0%3B+Win64%3B+x64)+AppleWebKit%2F537.36+(KHTML,+like+Gecko)+Chrome%2F129.0.0.0+Safari%2F537.36&browser_online=true&timezone_name=Etc%2FGMT-8&msToken=GcX7WQNhs6Xsa_h-dqWkxdlgVkiDvjiQMh6ymEleIx-NLhkLwUhHKG6ywBjy40vXPJHSIzzBCDE0a1-lcH5QGtSlfOK_aVZw4hIF2cI46B6BbFmhvPLw6AXbaNlcHFrQ4E9d8mC4&X-Bogus=DFSzswVLNCUANHrStKYNM09WcBnl&_signature=_02B4Z6wo00001600j7wAAIDDrTSPv-IBEAutNIsAAIx866""",
            "Cookie": """_ga_BZBQ2QHQSP=GS1.1.1732175154.1.0.1732175154.0.0.0; _ga=GA1.1.785161422.1732175154; _fbp=fb.1.1732175154686.851785016117250198; _tt_enable_cookie=1; _ttp=mTjpMGo3tkazKxhSeqvIiXy0uFC.tt.1; csrf_session_id=db7492ab17052f52e5460b3d581a9ab2; passport_csrf_token=c240a37432dcb7272d60836f5adfa2cf; passport_csrf_token_default=c240a37432dcb7272d60836f5adfa2cf; sid_guard=e463704005c7b7a3127e891e930cc61a%7C1732175527%7C5183996%7CMon%2C+20-Jan-2025+07%3A52%3A03+GMT; uid_tt=6e550bdcbeaf9b29441dcb484f54a85b6eba27084dfee4ce8f8d00e288c83ec9; uid_tt_ss=6e550bdcbeaf9b29441dcb484f54a85b6eba27084dfee4ce8f8d00e288c83ec9; sid_tt=e463704005c7b7a3127e891e930cc61a; sessionid=e463704005c7b7a3127e891e930cc61a; sessionid_ss=e463704005c7b7a3127e891e930cc61a; sid_ucp_v1=1.0.0-KDQ4ZjEyMDA3MWZjYzA3MzM1OWUxMGNlNzFmZmE1ODU2NzQyYmM4MGYKGwi3iI7i1Mi5n2cQp837uQYYofoVIAw4AUDrBxADGgZtYWxpdmEiIGU0NjM3MDQwMDVjN2I3YTMxMjdlODkxZTkzMGNjNjFh; ssid_ucp_v1=1.0.0-KDQ4ZjEyMDA3MWZjYzA3MzM1OWUxMGNlNzFmZmE1ODU2NzQyYmM4MGYKGwi3iI7i1Mi5n2cQp837uQYYofoVIAw4AUDrBxADGgZtYWxpdmEiIGU0NjM3MDQwMDVjN2I3YTMxMjdlODkxZTkzMGNjNjFh; msToken=uVbfePlBdQL3e3mfiUWfWfvZIf2oYWj4x63YHLXwy76HRFUrL30x8Jpy6rcWXx0cmsi2ux29T9q20PjsCFce1g-JEw7x_WRP97n3AlFrXudZQfeWDTso4fQ5QEfcwfE_27hwuNYA; TTSPC_Side_Menu_Role=0; ttwid=1%7C5pjKQSmC_JtrZB6_CQ41OG8qwOj2ZeJ1_v6TiTgpLbc%7C1732175540%7C24f5654dbeb6a71d762a10c8a5f8bb44bc55cdf935680542bca217e9683e6a1d; odin_tt=5d038aca1e80a243323367dde70caa2303023b7c223826f3ee6334c8cba228130ab2bb91ffba97fd95323016ca58f852f0d2d13278e490de5695bd0274923c4a"""
        },
        {
            "url": f"""https://api-partner-va.tiktokshop.com/api_sens/v1/affiliate/cmp/contact?creator_oecuid={creator_oecuid}&scene=20&user_language=en-US&partner_id=8651580312286038790&aid=360019&app_name=i18n_ecom_alliance&device_id=0&fp=verify_m3r1qlyp_j0kEhjV4_9Wqd_40Cn_BlCr_hXGHp7EjlcSj&device_platform=web&cookie_enabled=true&screen_width=1680&screen_height=1050&browser_language=en-US&browser_platform=MacIntel&browser_name=Mozilla&browser_version=5.0+(Macintosh%3B+Intel+Mac+OS+X+10_15_7)+AppleWebKit%2F537.36+(KHTML,+like+Gecko)+Chrome%2F130.0.0.0+Safari%2F537.36&browser_online=true&timezone_name=Asia%2FShanghai&msToken=7mVibctJ0PpE2ktbNK1GhV7vowAwvIU3OZS_kDse8xjMgy8VOJyCL63GvpCl7oFr3bowpFctOYyVfr9XdYb6PPs9ce1R-tTSrQGAj3CyVnZt-XS_s3opJw6KoqoVTbiWb4yVHmk=&X-Bogus=DFSzswVu3izANnZBtKYOz09WcBJk&_signature=_02B4Z6wo00001jE7dRQAAIDCMTt1FY9mli4xO3GAAOt-a8""",
            "Cookie": """passport_csrf_token=fa268048ef23161c8d1cedc2b3bc59ca; passport_csrf_token_default=fa268048ef23161c8d1cedc2b3bc59ca; csrf_session_id=470929ccf0b7614b08e8696d07dd4d9e; sid_guard=11afe3707c963b8fe4f83e36ede99513%7C1732177597%7C5183997%7CMon%2C+20-Jan-2025+08%3A26%3A34+GMT; uid_tt=a31dad8bf6498a3945a3cc67c9bf681e26d486d260e57842447998dcc7b9c7d3; uid_tt_ss=a31dad8bf6498a3945a3cc67c9bf681e26d486d260e57842447998dcc7b9c7d3; sid_tt=11afe3707c963b8fe4f83e36ede99513; sessionid=11afe3707c963b8fe4f83e36ede99513; sessionid_ss=11afe3707c963b8fe4f83e36ede99513; sid_ucp_v1=1.0.0-KGJiNTI0NGI1ZmNhM2VjMTA1NjllZTk1N2VkY2U1YTEwN2IzYmNkZjUKGwi3iKumvc67n2cQvd37uQYYofoVIAw4AUDrBxADGgZtYWxpdmEiIDExYWZlMzcwN2M5NjNiOGZlNGY4M2UzNmVkZTk5NTEz; ssid_ucp_v1=1.0.0-KGJiNTI0NGI1ZmNhM2VjMTA1NjllZTk1N2VkY2U1YTEwN2IzYmNkZjUKGwi3iKumvc67n2cQvd37uQYYofoVIAw4AUDrBxADGgZtYWxpdmEiIDExYWZlMzcwN2M5NjNiOGZlNGY4M2UzNmVkZTk5NTEz; msToken=OOEpO8xQUWuOxK6ljhTYd-hzcP2ccpXuPzf6nASk3YQ1LJUsw7kvVY1MGnM-Z95izuLNz-UkmQvqBMHX20w5kKKT4VwObvFqUX07ciAzJVss-xIma137_1hvSm2XtcupUHMniQ==; ttwid=1%7Cb1r2nASt_2vGjG26v1td3PCtna3jqQfbUV7TN26isAw%7C1732177599%7C0a2173a3d33e7cc89e0e4002530a3c47b161bd59c0f47eed9a6c7bc911ea850a; TTSPC_Side_Menu_Role=0; odin_tt=94360aef419277acb89b322458d05598ae6ded2863b80210b873303ed421710860e30ef0a71d10e5158c5eb762d0f383915cb8f4ba49c4644e85a3f87ce603b8"""
        },
        {
            "name": "1327025581@qq.com",
            "url": f"""https://api-partner-va.tiktokshop.com/api_sens/v1/affiliate/cmp/contact?creator_oecuid={creator_oecuid}&scene=11&user_language=zh-CN&partner_id=7166543330979874565&aid=360019&app_name=i18n_ecom_alliance&device_id=0&fp=verify_m3r4wxtz_pVReI0Q3_FXaP_445N_8WGd_vJ4FKcEGFZqe&device_platform=web&cookie_enabled=true&screen_width=1680&screen_height=1050&browser_language=zh-CN&browser_platform=MacIntel&browser_name=Mozilla&browser_version=5.0+(Macintosh%3B+Intel+Mac+OS+X+10_15_7)+AppleWebKit%2F537.36+(KHTML,+like+Gecko)+Chrome%2F120.0.0.0+Safari%2F537.36&browser_online=true&timezone_name=Asia%2FShanghai&msToken=E4RT_QcVUDNILpYCZLFkFiUFGjtnD8oAFPyaLnjMzwDz0H7b9pACje2LXBG2bpv_YkEXoMqXdxQ40RT77-OiOSw4z9j88UKrCmHN9dxx-rTAufOHXuuh2fSmX74Jm3EfiOOiww==&X-Bogus=DFSzswSuoZUANCXGtKFZvmL9Yu8G&_signature=_02B4Z6wo00001yk7WlQAAIDD-5JzqVAaDcspO17AAK181e""",
            "Cookie": """_ga_BZBQ2QHQSP=GS1.1.1732179410.1.0.1732179410.0.0.0; _ga=GA1.1.2038590060.1732179410; _fbp=fb.1.1732179410267.295073942630795422; _tt_enable_cookie=1; _ttp=kr_KrDTAdV_I6bU8P25OMko8Mp0.tt.1; passport_csrf_token=a1333ab97ac3ad403cd683c029eff30a; passport_csrf_token_default=a1333ab97ac3ad403cd683c029eff30a; csrf_session_id=3c3972a9c8917aeee544d514bb4ae674; sid_guard=108baeb88d72dd1c426429537fc5dae0%7C1732179588%7C5183987%7CMon%2C+20-Jan-2025+08%3A59%3A35+GMT; uid_tt=a09a3a2edafa364d7cdcb487d7dcb8cb55523839c111c053d68db32e7397977d; uid_tt_ss=a09a3a2edafa364d7cdcb487d7dcb8cb55523839c111c053d68db32e7397977d; sid_tt=108baeb88d72dd1c426429537fc5dae0; sessionid=108baeb88d72dd1c426429537fc5dae0; sessionid_ss=108baeb88d72dd1c426429537fc5dae0; sid_ucp_v1=1.0.0-KGU1ZTY3MTg1MGIxYTI5N2NlYWY2MmZiMWYzOThlNGY1ZTZlODFkNWEKGwiFiKCS477h-WYQhO37uQYYofoVIAw4AUDrBxADGgZtYWxpdmEiIDEwOGJhZWI4OGQ3MmRkMWM0MjY0Mjk1MzdmYzVkYWUw; ssid_ucp_v1=1.0.0-KGU1ZTY3MTg1MGIxYTI5N2NlYWY2MmZiMWYzOThlNGY1ZTZlODFkNWEKGwiFiKCS477h-WYQhO37uQYYofoVIAw4AUDrBxADGgZtYWxpdmEiIDEwOGJhZWI4OGQ3MmRkMWM0MjY0Mjk1MzdmYzVkYWUw; msToken=jn7RGODT-jZ9HM6B4fqgit_FUayOg_rC44WWVi1D9EX5yM5Ebutlp3VYAwOYPbjQg97WnaQ0b5XWTz3VzaZVlNMaBZ1GG1nMoYYLlpI89eto23iDYUpwYxWSWE4PSNDFZdfb3TI=; ttwid=1%7CIBQzaYy8sy5MV3xid8lKeKEZeSrE97gA-X_ihNTVNAs%7C1732179590%7Ce26e24a6a67b0e5123c1f55f0a0b4c7d5ecca57407eed65fdd48e851fd4c6489; TTSPC_Side_Menu_Role=7; odin_tt=a9b3e225039d9e50227ef834fdca3f0ec133e20b77dd5251eb28d3123d1555da5286fce00e9c9c802347bccf282b68f386b6ce654546801f4cd96f662319e3bc"""
        },
        {
            "name": "NannaDunkinson995@gmail.com",
            "url": f"""https://api-partner-va.tiktokshop.com/api_sens/v1/affiliate/cmp/contact?creator_oecuid={creator_oecuid}&scene=11&user_language=zh-CN&partner_id=7166543330979874565&aid=360019&app_name=i18n_ecom_alliance&device_id=0&fp=verify_m3r302dx_Ow4Ub3eU_7ZkG_44Ml_8IHH_P9yZQjX0fzZI&device_platform=web&cookie_enabled=true&screen_width=1680&screen_height=1050&browser_language=zh-CN&browser_platform=MacIntel&browser_name=Mozilla&browser_version=5.0+(Macintosh%3B+Intel+Mac+OS+X+10_15_7)+AppleWebKit%2F537.36+(KHTML,+like+Gecko)+Chrome%2F120.0.0.0+Safari%2F537.36&browser_online=true&timezone_name=Asia%2FShanghai&msToken=0FzToYYLUq0AmSTct9m2AuASpE82G5Mc18A0uzgYoVGTdgEmZtiTBeoipsGoUnx1VgmcKTxPIrFCcnWn2PGjBzuyAQODBnE1_hPUwpxvBLVR4A5m6936nDp0WvjBLN9YZhoxKw==&X-Bogus=DFSzswVuN6xANaDttKYnH/L9Yu0Y&_signature=_02B4Z6wo00001c5s8hAAAIDBHMXb7YJKBPnObPaAABSn98""",
            "Cookie": """_ga=GA1.1.2038590060.1732179410; _fbp=fb.1.1732179410267.295073942630795422; _tt_enable_cookie=1; _ttp=kr_KrDTAdV_I6bU8P25OMko8Mp0.tt.1; passport_csrf_token=a1333ab97ac3ad403cd683c029eff30a; passport_csrf_token_default=a1333ab97ac3ad403cd683c029eff30a; sid_guard=108baeb88d72dd1c426429537fc5dae0%7C1732179588%7C5183987%7CMon%2C+20-Jan-2025+08%3A59%3A35+GMT; uid_tt=a09a3a2edafa364d7cdcb487d7dcb8cb55523839c111c053d68db32e7397977d; uid_tt_ss=a09a3a2edafa364d7cdcb487d7dcb8cb55523839c111c053d68db32e7397977d; sid_tt=108baeb88d72dd1c426429537fc5dae0; sessionid=108baeb88d72dd1c426429537fc5dae0; sessionid_ss=108baeb88d72dd1c426429537fc5dae0; sid_ucp_v1=1.0.0-KGU1ZTY3MTg1MGIxYTI5N2NlYWY2MmZiMWYzOThlNGY1ZTZlODFkNWEKGwiFiKCS477h-WYQhO37uQYYofoVIAw4AUDrBxADGgZtYWxpdmEiIDEwOGJhZWI4OGQ3MmRkMWM0MjY0Mjk1MzdmYzVkYWUw; ssid_ucp_v1=1.0.0-KGU1ZTY3MTg1MGIxYTI5N2NlYWY2MmZiMWYzOThlNGY1ZTZlODFkNWEKGwiFiKCS477h-WYQhO37uQYYofoVIAw4AUDrBxADGgZtYWxpdmEiIDEwOGJhZWI4OGQ3MmRkMWM0MjY0Mjk1MzdmYzVkYWUw; msToken=jn7RGODT-jZ9HM6B4fqgit_FUayOg_rC44WWVi1D9EX5yM5Ebutlp3VYAwOYPbjQg97WnaQ0b5XWTz3VzaZVlNMaBZ1GG1nMoYYLlpI89eto23iDYUpwYxWSWE4PSNDFZdfb3TI=; odin_tt=a9b3e225039d9e50227ef834fdca3f0ec133e20b77dd5251eb28d3123d1555da5286fce00e9c9c802347bccf282b68f386b6ce654546801f4cd96f662319e3bc; _ga_BZBQ2QHQSP=GS1.1.1732182795.2.0.1732182795.0.0.0; ttwid=1%7CIBQzaYy8sy5MV3xid8lKeKEZeSrE97gA-X_ihNTVNAs%7C1732182799%7C762d8f9624cd3a605fac6eb39ee2e12f18cb2ee57cdfdd0d147f5ffaae2be2f6; TTSPC_Side_Menu_Role=7; csrf_session_id=3c3972a9c8917aeee544d514bb4ae674"""
        },
        {
            "name": "akahilauderdale419@gmail.com",
            "url": f"""https://api-partner-va.tiktokshop.com/api_sens/v1/affiliate/cmp/contact?creator_oecuid={creator_oecuid}&scene=11&user_language=zh-CN&partner_id=7166543330979874565&aid=360019&app_name=i18n_ecom_alliance&device_id=0&fp=verify_m3r3fpud_pHrIP1re_DLq3_4Z2p_8zGD_6Z3mVHT6bP9N&device_platform=web&cookie_enabled=true&screen_width=1680&screen_height=1050&browser_language=zh-CN&browser_platform=MacIntel&browser_name=Mozilla&browser_version=5.0+(Macintosh%3B+Intel+Mac+OS+X+10_15_7)+AppleWebKit%2F537.36+(KHTML,+like+Gecko)+Chrome%2F120.0.0.0+Safari%2F537.36&browser_online=true&timezone_name=Asia%2FShanghai&msToken=NN8xzppvtl157lrBvcjJ0Fp7L7oaXmfW4khHt-0pUBlJVGT_u5PSVK-wBSnb689vsJ7yza1ZPlAgWCYiQcRW_FqrTk-lFiOPUaWIapO4G1Nt8FMBZyYEbpu9nBLWCFjOQaGNpg==&X-Bogus=DFSzswSur52ANCXGtKYaAAL9Yu0e&_signature=_02B4Z6wo000012gIX3gAAIDDuqF2hCOf7vdoCFvAAL1I9c""",
            "Cookie": """_ga_BZBQ2QHQSP=GS1.1.1732180249.1.0.1732180249.0.0.0; _ga=GA1.1.1910697984.1732180250; _fbp=fb.1.1732180250122.940254685200131192; _tt_enable_cookie=1; _ttp=8aBszDChg3vCXDWuoFQe_O0Xzos.tt.1; csrf_session_id=3c3972a9c8917aeee544d514bb4ae674; passport_csrf_token=3eaba196a5173f4aeac5b3a9db859120; passport_csrf_token_default=3eaba196a5173f4aeac5b3a9db859120; sid_guard=530f9fd3afa5eb572c605450f6134286%7C1732180462%7C5183996%7CMon%2C+20-Jan-2025+09%3A14%3A18+GMT; uid_tt=b99291f07550ac0a504c48879bdd92367ced7ad4cdad61ea91448159ab7afe41; uid_tt_ss=b99291f07550ac0a504c48879bdd92367ced7ad4cdad61ea91448159ab7afe41; sid_tt=530f9fd3afa5eb572c605450f6134286; sessionid=530f9fd3afa5eb572c605450f6134286; sessionid_ss=530f9fd3afa5eb572c605450f6134286; sid_ucp_v1=1.0.0-KDU0ZTk3NDYyYjMxNTQ4OGVlZTFiYTRlY2Q3MmU2N2JjNmUyMDk4YWQKGwi3iMbOx7C-n2cQ7vP7uQYYofoVIAw4AUDrBxADGgZtYWxpdmEiIDUzMGY5ZmQzYWZhNWViNTcyYzYwNTQ1MGY2MTM0Mjg2; ssid_ucp_v1=1.0.0-KDU0ZTk3NDYyYjMxNTQ4OGVlZTFiYTRlY2Q3MmU2N2JjNmUyMDk4YWQKGwi3iMbOx7C-n2cQ7vP7uQYYofoVIAw4AUDrBxADGgZtYWxpdmEiIDUzMGY5ZmQzYWZhNWViNTcyYzYwNTQ1MGY2MTM0Mjg2; msToken=50ZITW3z4dhnhH9vEdnW7MVQ9ozRAeM3kM0lwrHnxMl8cqrHwFgiHbA7SJQ2SC7b6tmxadrFsXQtfxJ40D8PsExC1pLS2dWFFZkwi0wZkvgmGHW23K2IfCTVDr4oonospbEX; ttwid=1%7C5PiH6hx1LfgChdoO2RJMJoySHH8c50wPJULfeeeZJx8%7C1732181723%7C4ef9c9696729f1033ac33118d8c43e7ce11f75902c54989213ccb41d2f20d978; TTSPC_Side_Menu_Role=7; odin_tt=8c021d701f5a4d58f32c38a5ceffb539828fa1bd4dacede449678bc867da577fc08b9fb5ac0ee7ad250f12b679ddeba0615831cd9cf86c13c04f1bb7c451c680"""
        },
        {
            "name": "kieferhodsdon537@gmail.com",
            "url": f"""https://api-partner-va.tiktokshop.com/api_sens/v1/affiliate/cmp/contact?creator_oecuid={creator_oecuid}&scene=11&user_language=zh-CN&partner_id=7166543330979874565&aid=360019&app_name=i18n_ecom_alliance&device_id=0&fp=verify_m3r3oegl_UmnJdSdy_rNm9_4aQq_AhA5_ew3uCJ3dmmAD&device_platform=web&cookie_enabled=true&screen_width=1680&screen_height=1050&browser_language=zh-CN&browser_platform=MacIntel&browser_name=Mozilla&browser_version=5.0+(Macintosh%3B+Intel+Mac+OS+X+10_15_7)+AppleWebKit%2F537.36+(KHTML,+like+Gecko)+Chrome%2F120.0.0.0+Safari%2F537.36&browser_online=true&timezone_name=Asia%2FShanghai&msToken=2Wshe2mgHbFt9GBaRUhBA8PgRv-De6cxEbnZsdFy8zRMj-QBr4xK3DiAsojqYb_ifdwxHtng3fToclwTcfBxFKsUgGZ8lddwAaqYkhPaE990xnLNgj2w3LZX2mVyZFiwhqsBJB8=&X-Bogus=DFSzswSu0XhANCXGtKYeW/L9Yu0t&_signature=_02B4Z6wo00001DyUdHQAAIDA7j1diSq59Tg8lHDAAGgi90""",
            "Cookie": """_ga_BZBQ2QHQSP=GS1.1.1732180599.1.0.1732180599.0.0.0; _ga=GA1.1.1961721011.1732180599; _tt_enable_cookie=1; _ttp=4Wzq6x218_MPaB3T628dgMNPW17.tt.1; _fbp=fb.1.1732180599154.315573422348927250; passport_csrf_token=68e4ac78bdefd5ed2ad22e37724a07c6; passport_csrf_token_default=68e4ac78bdefd5ed2ad22e37724a07c6; sid_guard=b1d03b70636e7bee0a12f838025c284d%7C1732180721%7C5183996%7CMon%2C+20-Jan-2025+09%3A18%3A37+GMT; uid_tt=9cd231c05c39242c3a62d334e98b0e82afde82af28b4de28a4a4895b00b98bef; uid_tt_ss=9cd231c05c39242c3a62d334e98b0e82afde82af28b4de28a4a4895b00b98bef; sid_tt=b1d03b70636e7bee0a12f838025c284d; sessionid=b1d03b70636e7bee0a12f838025c284d; sessionid_ss=b1d03b70636e7bee0a12f838025c284d; sid_ucp_v1=1.0.0-KDYzMGFjMmI4NjcyNzU0NmI4NDYxYTIyMjFkNDEwOWZhMmVhMDkwN2IKGQiGiK3EtYr3jmYQ8fX7uQYYofoVOAFA6wcQAxoGbWFsaXZhIiBiMWQwM2I3MDYzNmU3YmVlMGExMmY4MzgwMjVjMjg0ZA; ssid_ucp_v1=1.0.0-KDYzMGFjMmI4NjcyNzU0NmI4NDYxYTIyMjFkNDEwOWZhMmVhMDkwN2IKGQiGiK3EtYr3jmYQ8fX7uQYYofoVOAFA6wcQAxoGbWFsaXZhIiBiMWQwM2I3MDYzNmU3YmVlMGExMmY4MzgwMjVjMjg0ZA; msToken=P7dNLx5IVZAlEdO32xYsw454m8s-0VnNvIVCLFE16OQqenH6Kv_x4jKFPBHYo0hXerTVyH7pEZ1Njzj3IjbjXO2s6twC2RPJza0cSDgc8KoAKzjHW2qnADsNgmag1nAbAeCEk2I=; ttwid=1%7CsYC3c4dJR2cNw3GwCcqiqk0F6QKvGU3zTEpqh2bFg4g%7C1732180723%7C02c14ccf3f2ee96d33629d37748be5dadc0b36d39c398592df373bb80d6dac14; TTSPC_Side_Menu_Role=7; csrf_session_id=3c3972a9c8917aeee544d514bb4ae674"""
        },
        {
            "name": "rainewxckc@gmail.com",
            "url": f"""https://api-partner-va.tiktokshop.com/api_sens/v1/affiliate/cmp/contact?creator_oecuid={creator_oecuid}&scene=20&user_language=zh-CN&partner_id=8651580312286038790&aid=360019&app_name=i18n_ecom_alliance&device_id=0&fp=verify_m3r1jesm_5xd5aGRw_IGRC_4M89_BSnZ_oiijTScgk5JP&device_platform=web&cookie_enabled=true&screen_width=1680&screen_height=1050&browser_language=zh-CN&browser_platform=MacIntel&browser_name=Mozilla&browser_version=5.0+(Macintosh%3B+Intel+Mac+OS+X+10_15_7)+AppleWebKit%2F537.36+(KHTML,+like+Gecko)+Chrome%2F120.0.0.0+Safari%2F537.36&browser_online=true&timezone_name=Asia%2FShanghai&msToken=nvyuJ0uBab_CHbtCAsHFz1uSgo2PtXNQF9a5RpPGzms3aM9__jd4AoUg_8mQnyDqCzB7CkC0UbrbrQxAcKKRc2h_-Y5ZWcYsIVzPfYvCv2nfSqRTRa11mJMQ70hw-WJP6Tl2xg==&X-Bogus=DFSzswVuWktANaDttKYPbt9WcBjC&_signature=_02B4Z6wo000014HT9ygAAIDDgdP3K0raZE-B0.OAAIdSf3""",
            "Cookie": """_fbp=fb.1.1726622121347.187020236865553087; _tt_enable_cookie=1; _ga=GA1.1.416193681.1726622123; _ga_BZBQ2QHQSP=GS1.1.1732176961.6.0.1732176961.0.0.0; _ttp=B45i8jTC1T9Suiyddcnx-CSj2cO.tt.1; passport_csrf_token=975a4f76771e283e176328cd8edaff70; passport_csrf_token_default=975a4f76771e283e176328cd8edaff70; sid_guard=1eb45cd6bd7a02572e060a51277585b0%7C1732177130%7C5183993%7CMon%2C+20-Jan-2025+08%3A18%3A43+GMT; uid_tt=c3ec1e10f3d6d0da5ceb1cf68015b63459ba5a5bcabe711df013085df13ccca5; uid_tt_ss=c3ec1e10f3d6d0da5ceb1cf68015b63459ba5a5bcabe711df013085df13ccca5; sid_tt=1eb45cd6bd7a02572e060a51277585b0; sessionid=1eb45cd6bd7a02572e060a51277585b0; sessionid_ss=1eb45cd6bd7a02572e060a51277585b0; sid_ucp_v1=1.0.0-KGI5M2YwMmQ0YTZhNDNjZTJmMTJjNmNiNTg1YzFmYWRmOTRlNTQ0NGQKGQi3iI7EtMG6n2cQ6tn7uQYYofoVOAFA6wcQAxoGbWFsaXZhIiAxZWI0NWNkNmJkN2EwMjU3MmUwNjBhNTEyNzc1ODViMA; ssid_ucp_v1=1.0.0-KGI5M2YwMmQ0YTZhNDNjZTJmMTJjNmNiNTg1YzFmYWRmOTRlNTQ0NGQKGQi3iI7EtMG6n2cQ6tn7uQYYofoVOAFA6wcQAxoGbWFsaXZhIiAxZWI0NWNkNmJkN2EwMjU3MmUwNjBhNTEyNzc1ODViMA; msToken=tOzVbhoYLTUGgKslsqhd5g6-05lFCdfQOuZQuWcXDFTxHmwVNsq-GemZSdsjCcScWIUZhcMRVPg1s2lYkjGOcUFMXCAZy7UeKfHk_7M0cSlNr7_FHfYpT9opkHSSzbtN5mv3; TTSPC_Side_Menu_Role=0; csrf_session_id=3c3972a9c8917aeee544d514bb4ae674; ttwid=1%7CIxVYZFeTtqkKOLJoxukVt1kIB9-qBPmz2fymZllfk6o%7C1732177847%7C58ca332b94081b3e40a39c63400c33c0c1f14e7dcba3dd7f191f44300518f704"""
        },
        {
            "name": "joanh2695@gmail.com",
            "url": f"""https://api-partner-va.tiktokshop.com/api_sens/v1/affiliate/cmp/contact?creator_oecuid={creator_oecuid}&scene=20&user_language=zh-CN&partner_id=8651580312286038790&aid=360019&app_name=i18n_ecom_alliance&device_id=0&fp=verify_m3r2421r_60xh19AG_d22N_46sI_B9f7_nFXpMRw54DGG&device_platform=web&cookie_enabled=true&screen_width=1680&screen_height=1050&browser_language=zh-CN&browser_platform=MacIntel&browser_name=Mozilla&browser_version=5.0+(Macintosh%3B+Intel+Mac+OS+X+10_15_7)+AppleWebKit%2F537.36+(KHTML,+like+Gecko)+Chrome%2F120.0.0.0+Safari%2F537.36&browser_online=true&timezone_name=Asia%2FShanghai&msToken=nsWJIW96b6IpZSYaNf-tljGMEXfX5dvB1zzV9tM0h9RRniPBV4hsJTEO8c5QVFHVMX3VqxZBwttIC_yqqPIyK3tOY_iozffku8RBdZfozbbuUbk525EuXOHH8sdByCYabPMC&X-Bogus=DFSzswVuA60ANaDttKYyYt9WcBJD&_signature=_02B4Z6wo000018mLP2QAAIDDyYs.Z4mXNpfJizvAAJVlc8""",
            "Cookie": """_ga=GA1.1.1235319771.1732178013; _fbp=fb.1.1732178013159.202695881371644019; _tt_enable_cookie=1; _ttp=28pHNwpqrcc-ku759dMMg6swads.tt.1; passport_csrf_token=7805fccb85a5ac33dd95192a195f25a8; passport_csrf_token_default=7805fccb85a5ac33dd95192a195f25a8; sid_guard=ff18bbefe14f90c5c1913f7438f74a46%7C1732178093%7C5183992%7CMon%2C+20-Jan-2025+08%3A34%3A45+GMT; uid_tt=902cbf88f0a740b4c4e723fbd16139de6e785207ff167fd2be82a5d501818b88; uid_tt_ss=902cbf88f0a740b4c4e723fbd16139de6e785207ff167fd2be82a5d501818b88; sid_tt=ff18bbefe14f90c5c1913f7438f74a46; sessionid=ff18bbefe14f90c5c1913f7438f74a46; sessionid_ss=ff18bbefe14f90c5c1913f7438f74a46; sid_ucp_v1=1.0.0-KGUxYTZkZmFiYmJiY2NjYzg1MDYyNjkxNTg1NGJjY2NjMWRkMTA4NjkKGQi3iLPEm8-6n2cQreH7uQYYofoVOAFA6wcQAxoGbWFsaXZhIiBmZjE4YmJlZmUxNGY5MGM1YzE5MTNmNzQzOGY3NGE0Ng; ssid_ucp_v1=1.0.0-KGUxYTZkZmFiYmJiY2NjYzg1MDYyNjkxNTg1NGJjY2NjMWRkMTA4NjkKGQi3iLPEm8-6n2cQreH7uQYYofoVOAFA6wcQAxoGbWFsaXZhIiBmZjE4YmJlZmUxNGY5MGM1YzE5MTNmNzQzOGY3NGE0Ng; msToken=2h6soI9GyFMGnwExOnuaYHGEMPhgbEgy_v5hGkBh5UXL1YL3PtmpXLDUAIde54zy9TVf8tUz0tcrzRuR4HlSDSsfyFifzVIur7I7bTv74OtuoL2w-prBas5BsRa0s42fk6v09OI=; _ga_BZBQ2QHQSP=GS1.1.1732178013.1.0.1732178094.0.0.0; TTSPC_Side_Menu_Role=0; ttwid=1%7CSf20MFFvW9Nf1dl-zoNiBNnMa3xmkF2zqZMyO0VvNgQ%7C1732178095%7C56f05efff4f2c766ed7dcd33e7385ad29eaba07011947b77feae4564f0c3cf6f; csrf_session_id=3c3972a9c8917aeee544d514bb4ae674"""
        },
        {
            "name": "hubbardrngi@gmail.com",
            "url": f"""https://api-partner-va.tiktokshop.com/api_sens/v1/affiliate/cmp/contact?creator_oecuid={creator_oecuid}&scene=20&user_language=zh-CN&partner_id=8651580312286038790&aid=360019&app_name=i18n_ecom_alliance&device_id=0&fp=verify_m3r28hq1_YHniJ1kA_FbUN_4H4J_AgHl_MNQ6OwX3sNNM&device_platform=web&cookie_enabled=true&screen_width=1680&screen_height=1050&browser_language=zh-CN&browser_platform=MacIntel&browser_name=Mozilla&browser_version=5.0+(Macintosh%3B+Intel+Mac+OS+X+10_15_7)+AppleWebKit%2F537.36+(KHTML,+like+Gecko)+Chrome%2F120.0.0.0+Safari%2F537.36&browser_online=true&timezone_name=Asia%2FShanghai&msToken=n-M03mqPubiCIzzr-hnjYDOJDMmznssMr573YJD7VtTP1TacnxqUH0Kl_CV2Q8VnQsPVmiMAuItOiwD1mWdp7VlAo1H2iYXuyQF8r3bmjGEd2Ed6KszWfScyGS547UUqppZv8g==&X-Bogus=DFSzswVugA2ANaDttKYxez9WcBrv&_signature=_02B4Z6wo00001bCeo6wAAIDBsJ6jrJY3kuWwnqcAAAsa07""",
            "Cookie": """_ga_BZBQ2QHQSP=GS1.1.1732178204.1.0.1732178204.0.0.0; _ga=GA1.1.1565633602.1732178205; _fbp=fb.1.1732178205552.757449080303880064; _tt_enable_cookie=1; _ttp=gW6Uk9X8k-K0EY11fYvqn6G4Faj.tt.1; passport_csrf_token=5e7bb5d318beff7a85414fbf1c8bdfaa; passport_csrf_token_default=5e7bb5d318beff7a85414fbf1c8bdfaa; sid_guard=80ecdc9a4cf031ad0b3470102ce0421f%7C1732178300%7C5183994%7CMon%2C+20-Jan-2025+08%3A38%3A14+GMT; uid_tt=acd9f639f5eb9c71e1cdf6e9192e26f0ff6b71ba8eb96739e9bb968c22c912da; uid_tt_ss=acd9f639f5eb9c71e1cdf6e9192e26f0ff6b71ba8eb96739e9bb968c22c912da; sid_tt=80ecdc9a4cf031ad0b3470102ce0421f; sessionid=80ecdc9a4cf031ad0b3470102ce0421f; sessionid_ss=80ecdc9a4cf031ad0b3470102ce0421f; sid_ucp_v1=1.0.0-KDUzYjQ0OWQxMmRjNDhkZDVmYjI2YWY1MDIwOGExMTZmMzc2YjRiOGMKGQi4iN3uhcu6n2cQ_OL7uQYYofoVOAFA6wcQAxoGbWFsaXZhIiA4MGVjZGM5YTRjZjAzMWFkMGIzNDcwMTAyY2UwNDIxZg; ssid_ucp_v1=1.0.0-KDUzYjQ0OWQxMmRjNDhkZDVmYjI2YWY1MDIwOGExMTZmMzc2YjRiOGMKGQi4iN3uhcu6n2cQ_OL7uQYYofoVOAFA6wcQAxoGbWFsaXZhIiA4MGVjZGM5YTRjZjAzMWFkMGIzNDcwMTAyY2UwNDIxZg; msToken=W0CtVU3YX0Q5ZCRRKELl76wuo8ps8hOj4l_fqtj_42sRPDSyGFXudOGtmDsDw_5-ldackmplaSk7r6kRIPJZmztjAAw4ayTCrDhHC7zptHbqUXWkfzsdoZyFDhbczMW1huxq; TTSPC_Side_Menu_Role=0; ttwid=1%7CL5NDltc2RcArszK915qLAqhZ2xj2u43mOaSMlI6eNjo%7C1732178302%7C35e4bbc296d7a9146cbd1d54983caa4e568fa29a61682857ecfb2200114e96de; csrf_session_id=3c3972a9c8917aeee544d514bb4ae674"""
        },
        {
            "name": "monrealaqtv@gmail.com",
            "url": f"""https://api-partner-va.tiktokshop.com/api_sens/v1/affiliate/cmp/contact?creator_oecuid={creator_oecuid}&scene=20&user_language=zh-CN&partner_id=8651580312286038790&aid=360019&app_name=i18n_ecom_alliance&device_id=0&fp=verify_m3r2e44k_icyGCdL2_XxAm_44Ym_AJoN_n2Yza77ppTtC&device_platform=web&cookie_enabled=true&screen_width=1680&screen_height=1050&browser_language=zh-CN&browser_platform=MacIntel&browser_name=Mozilla&browser_version=5.0+(Macintosh%3B+Intel+Mac+OS+X+10_15_7)+AppleWebKit%2F537.36+(KHTML,+like+Gecko)+Chrome%2F120.0.0.0+Safari%2F537.36&browser_online=true&timezone_name=Asia%2FShanghai&msToken=Wo5eqKSrKLBn2SEYdRPABPsCJFaPG_L-J9U0vLUA4FD6IMgwl8vM1jSvoZULaZwJzxdvgzeAo0x9-4jmIFOuFB1e-VGVufqcclxCbbEZAt9IRObHOmdjYFjpAE-8gZjjjjYf&X-Bogus=DFSzswVuK1xANaDttKY9jz9WcBJh&_signature=_02B4Z6wo00001G6tAYAAAIDAbq0Bg8HemNxurQUAAHydc2""",
            "Cookie": """_ga_BZBQ2QHQSP=GS1.1.1732178437.1.0.1732178437.0.0.0; _ga=GA1.1.893106383.1732178438; _fbp=fb.1.1732178437803.812479301943948545; _tt_enable_cookie=1; _ttp=tiQhlpoZNxFS6Vrw1jUDBsWEvpl.tt.1; passport_csrf_token=e60f3b2025e4f00a37cbdfde7063241a; passport_csrf_token_default=e60f3b2025e4f00a37cbdfde7063241a; csrf_session_id=3c3972a9c8917aeee544d514bb4ae674; sid_guard=aaa1e1add8a3e9ce388de5bc1d3c5445%7C1732178564%7C5183988%7CMon%2C+20-Jan-2025+08%3A42%3A32+GMT; uid_tt=551e0d3bdfddc0e8912e3780aee65675b62b3854ea89d6def133c297d4abc7bc; uid_tt_ss=551e0d3bdfddc0e8912e3780aee65675b62b3854ea89d6def133c297d4abc7bc; sid_tt=aaa1e1add8a3e9ce388de5bc1d3c5445; sessionid=aaa1e1add8a3e9ce388de5bc1d3c5445; sessionid_ss=aaa1e1add8a3e9ce388de5bc1d3c5445; sid_ucp_v1=1.0.0-KGYyMDFhZmY1YTI0ZmRjOGUyYzYzODc0Y2ZlZThjNjQ3YjA2ZDZmOTEKGwi3iJD24-O6n2cQhOX7uQYYofoVIAw4AUDrBxADGgZtYWxpdmEiIGFhYTFlMWFkZDhhM2U5Y2UzODhkZTViYzFkM2M1NDQ1; ssid_ucp_v1=1.0.0-KGYyMDFhZmY1YTI0ZmRjOGUyYzYzODc0Y2ZlZThjNjQ3YjA2ZDZmOTEKGwi3iJD24-O6n2cQhOX7uQYYofoVIAw4AUDrBxADGgZtYWxpdmEiIGFhYTFlMWFkZDhhM2U5Y2UzODhkZTViYzFkM2M1NDQ1; msToken=qt0JTz73YoR1UmqbCe2MlUqlR2ylaz5uRId2rAb991tNbB86gDOX3ZIE-BuSvu17e8E-Ms2TBjjZ8b4Is39ZMIF7I0v93ja2jDedVQFU-c9K1dM2PemV4oIQziFg8y-48a3Tb9c=; ttwid=1%7CBG8OAspuivz2ihmj53LPEI2IOAIsAzX1EjKG5cvAdoI%7C1732178566%7Ce2b751d187214790539a43463ee28636931c061c335f74d6f1f5a35ce057e102; TTSPC_Side_Menu_Role=0; odin_tt=2583d9457010a1bdc4fd8141faca1eb3ea2e44ad9591e03931ccb7c781de54281d363669322c344c2fadd2451571f2d8801537207a419f169ed2b291c4fedd09"""
        },
        {
            "name": "tabhubolikad@gmail.com",
            "url": f"""https://api-partner-va.tiktokshop.com/api_sens/v1/affiliate/cmp/contact?creator_oecuid={creator_oecuid}&scene=20&user_language=zh-CN&partner_id=8651580312286038790&aid=360019&app_name=i18n_ecom_alliance&device_id=0&fp=verify_m3r2gkf8_wuM48wsY_OPCQ_4V8j_9om1_ltDGezHB5TVc&device_platform=web&cookie_enabled=true&screen_width=1680&screen_height=1050&browser_language=zh-CN&browser_platform=MacIntel&browser_name=Mozilla&browser_version=5.0+(Macintosh%3B+Intel+Mac+OS+X+10_15_7)+AppleWebKit%2F537.36+(KHTML,+like+Gecko)+Chrome%2F120.0.0.0+Safari%2F537.36&browser_online=true&timezone_name=Asia%2FShanghai&msToken=dSPS13zDVdUVoOclekg8N36-b3hZY0oghoW9Su-ZP3cUULQAwfCXszaxpfemaa80fh47DW7Rqzwr0T3_DfhC6LU5A1WIRek7UYl5Zn5i9zs7StMtjnRJR6H3JiCvb22ySrwjow==&X-Bogus=DFSzswVu/abANaDttKYH2t9WcBje&_signature=_02B4Z6wo00001ooGaEwAAIDCigZoTqfiWPKKBmzAAMXL90""",
            "Cookie": """_fbp=fb.1.1732178535373.74162394907854782; _ga_BZBQ2QHQSP=GS1.1.1732178535.1.0.1732178535.0.0.0; _ga=GA1.1.209419566.1732178536; _tt_enable_cookie=1; _ttp=i8lE1mEzMECMUf8uu2GtreihX8e.tt.1; passport_csrf_token=a9804510497e4eab6fd361bf0c3dc29f; passport_csrf_token_default=a9804510497e4eab6fd361bf0c3dc29f; sid_guard=524596321a6d0186f08bd8e717c4eff9%7C1732178676%7C5183996%7CMon%2C+20-Jan-2025+08%3A44%3A32+GMT; uid_tt=bcbf3a0eec48604f586d47cfbda13991b90e96f0c141746024d6a1b16ae8a441; uid_tt_ss=bcbf3a0eec48604f586d47cfbda13991b90e96f0c141746024d6a1b16ae8a441; sid_tt=524596321a6d0186f08bd8e717c4eff9; sessionid=524596321a6d0186f08bd8e717c4eff9; sessionid_ss=524596321a6d0186f08bd8e717c4eff9; sid_ucp_v1=1.0.0-KGI3ZjY5NjQyODQ2MjEyMTU3MDAxYzEyOWUxMzc0ZjFjOGViMzk1ODgKGQi3iIT02dK6n2cQ9OX7uQYYofoVOAFA6wcQAxoGbWFsaXZhIiA1MjQ1OTYzMjFhNmQwMTg2ZjA4YmQ4ZTcxN2M0ZWZmOQ; ssid_ucp_v1=1.0.0-KGI3ZjY5NjQyODQ2MjEyMTU3MDAxYzEyOWUxMzc0ZjFjOGViMzk1ODgKGQi3iIT02dK6n2cQ9OX7uQYYofoVOAFA6wcQAxoGbWFsaXZhIiA1MjQ1OTYzMjFhNmQwMTg2ZjA4YmQ4ZTcxN2M0ZWZmOQ; msToken=i1P0Rb88qiuCyEeT9ep5wSPKrh5CXy94z9RzWlacj1fAIqoVF15zCjoz3Ah9T1HsJb5hCTuORABz1TnBXQGOX2IoO1LjTKZKqn9HDKp6TEhrq6kZUaCDmGzu9mMYmzokrH3AhZU=; ttwid=1%7CZV4_UHv5cpDFrjjOV5ryJGrxydNT2GlWFOiQg6_z6hE%7C1732178679%7C166f74c5c2e5db19fa1826875c91369a27ebf7524687ea2f32ce7add04e6c971; TTSPC_Side_Menu_Role=0; csrf_session_id=3c3972a9c8917aeee544d514bb4ae674"""
        },
    ]
    print(f"---------------------{index} ---------------------------------")
    cookie_len = len(cookie_list)
    if index < 0 or index >= cookie_len:
        raise Exception("cookie for done!")
    return cookie_list[index]


if __name__ == '__main__':
    # get_no_request_seller_contact_id()
    # data = [{'field': 1, 'value': '349393849', 'title': None}]
    # user_id = 308076
    # resetDataAffiliate(data, user_id)

    print(tap_user_list("123", 1))
