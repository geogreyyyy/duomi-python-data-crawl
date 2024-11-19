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
    sql = """SELECT user_id,creator_oecuid FROM tiktok_creator_user_info WHERE user_id IN ( SELECT id FROM tiktok_user_info WHERE is_request IS NULL AND region !='US' ) LIMIT 10"""
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
    sql = f"""UPDATE tiktok_user_info SET 
    whatsapp = '{data.get('whatsapp', '')}',
    viber_number= '{data.get('viber_number', '')}',
    facebook_number='{data.get('facebook_number', '')}',
    zalo_number='{data.get('zalo_number', '')}',
    line_number='{data.get('line_number', '')}',
    email='{data.get('email', '')}',
    other_contact='{data.get('other_contact', '')}',
    is_request = {request_state} ,
    update_by = 'python-tiktok-shop-partner',
    update_time = '{time.strftime('%Y-%m-%d %H:%M:%S')}'
    WHERE id = '{data.get('user_id', '')}' """
    mysql.update(sql)
    mysql.dispose()


# 格式化爬取数据
def resetData(response_data, user_id):
    save_data = {}
    if len(response_data) > 0 & user_id is not None:
        save_data['user_id'] = user_id
        save_data['other_contact'] = json.dumps(response_data)
        for field_data in response_data:
            field_value = replaceContactType.sellerContactMap.get(field_data['field'], None)
            if field_value is not None:
                save_data[field_value] = field_data['value']
        print(save_data)
        update_user_contact(save_data, REQUEST_TRUE)


# 格式化失败的爬取数据
def resetErrorData(response_data, user_id):
    save_data = {}
    if user_id is not None:
        save_data['user_id'] = user_id
        save_data['other_contact'] = json.dumps(response_data)
        print(save_data)
        update_user_contact(save_data, REQUEST_ERROR)


if __name__ == '__main__':
    # get_no_request_seller_contact_id()
    data = [{'field': 32, 'value': '349393849', 'title': None}]
    user_id = 308076
    resetData(data, user_id)
