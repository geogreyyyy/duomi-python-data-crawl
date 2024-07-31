import sys

sys.path.append("..")
from MySqlCon import Mysql


# 获取店铺Cookie
def get_cookie(shop_id):
    mysql = Mysql()
    sql = "select cookie from tiktok_shop_info where id = %(shop_id)s"
    result = mysql.getOne(sql, {"shop_id": shop_id})

    return result
