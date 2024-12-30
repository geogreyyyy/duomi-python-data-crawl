import redis
from MySqlCon import Mysql
import sys
import json
import numpy as np

sys.path.append("..")
from config import RedisKeyConstants as RedisKeyConstants
from config import Config

redis_client = redis.Redis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, db=1,
                           password=Config.REDIS_PASSWORD)


# 初始化redis
def init_unique_id():
    pipe = redis_client.pipeline()
    redis_user_info_key = RedisKeyConstants.redis_user_info_key

    mysql = Mysql()
    sql = "SELECT id,unique_id,signature FROM tiktok_user_info"

    # 列表中存在key则删除
    has_key = redis_client.keys(pattern=redis_user_info_key + "*")
    if len(has_key) != 0:
        redis_client.delete(*redis_client.keys(redis_user_info_key + "*"))

    class MyEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, bytes):
                return str(obj, encoding='utf-8')
            return json.JSONEncoder.default(self, obj)

    result = mysql.getAll(sql)
    for item in result:
        uniqueId = str(item.get("unique_id"))
        pipe.set(redis_user_info_key + uniqueId, json.dumps(item, cls=MyEncoder, indent=4))
    pipe.execute()


insert_sql = """
    insert into search_key(id,search_key,state) Values(%(id)s,%(search_key)s,%(state)s)
"""


def insert_search_key_sql():
    search_data = []
    for char1 in range(ord('a'), ord('z') + 1):
        search_data.append({"id": str(chr(char1)), "search_key": str(chr(char1)), "state": 1, })
        for char2 in range(ord('a'), ord('z') + 1):
            search_data.append(
                {"id": str(chr(char1) + chr(char2)), "search_key": str(chr(char1) + chr(char2)), "state": 1, })
            for char3 in range(ord('a'), ord('z') + 1):
                for char4 in range(ord('a'), ord('z') + 1):
                    search_data.append(
                        {"id": str(chr(char1) + chr(char2)),
                         "search_key": str(chr(char1) + chr(char2) + chr(char3) + chr(char4)),
                         "state": 1, })

    # for char1 in range(ord('0'), ord('9') + 1):
    #     search_data.append({"id": str(chr(char1)), "search_key": str(chr(char1)), "state": 1, })
    #     for char2 in range(ord('0'), ord('9') + 1):
    #         search_data.append(
    #             {"id": str(chr(char1) + chr(char2)), "search_key": str(chr(char1) + chr(char2)), "state": 1, })
    #         for char3 in range(ord('0'), ord('9') + 1):
    #             search_data.append(
    #                 {"id": str(chr(char1) + chr(char2) + chr(char3)),
    #                  "search_key": str(chr(char1) + chr(char2) + chr(char3)), "state": 1, })
    #             for char4 in range(ord('0'), ord('9') + 1):
    #                 search_data.append(
    #                     {"id": str(chr(char1) + chr(char2) + chr(char3) + chr(char4)),
    #                      "search_key": str(chr(char1) + chr(char2) + chr(char3) + chr(char4)), "state": 1, })

    # mysql.insertMany(insert_sql, search_data)
    # mysql.dispose()
    return search_data


def init_redis_search_key():
    result = insert_search_key_sql()
    redis_client.delete("tiktok_shop_partner_center_PH_search_key")
    r = redis_client.pipeline()
    for item in result:
        r.lpush("tiktok_shop_partner_center_PH_search_key", item["search_key"])
    r.execute()


def insert_record_key_sql():
    search_data = []
    search_data.append({"id": 'aaliyahharris', "search_key": 'aaliyahharris', "state": 1, })
    return search_data


def init_redis_record_key():
    result = insert_record_key_sql()
    redis_client.delete("tiktok_TK_record_search_key")
    r = redis_client.pipeline()
    for item in result:
        r.lpush("tiktok_TK_record_search_key", item["search_key"])
    r.execute()


if __name__ == '__main__':
    pipe = redis_client.pipeline()
    redis_user_info_key = "jOb_product_img:"
    # 列表中存在key则删除
    has_key = redis_client.keys(pattern=redis_user_info_key + "*")
    if len(has_key) != 0:
        redis_client.delete(*redis_client.keys(redis_user_info_key + "*"))

    # init_unique_id()
    # init_unique_id()
    # init_redis_search_key()
    # aa = init_redis_record_key()
    # print(aa)
