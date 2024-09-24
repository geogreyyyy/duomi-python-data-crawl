import time

import log
import json
import redis
import sys

import re

sys.path.append("..")
from utils import createTableUtils
from utils import tagsEnums as tagsEnums
from utils import redisLock
from config import RedisKeyConstants as RedisKeyConstants
from config import Config
from MySqlCon import Mysql

# 申请资源
logging = log.Logger("../sql.log", level='INFO')

redis_client = redis.Redis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, db=Config.REDIS_DB,
                           password=Config.REDIS_PASSWORD)

redis_user_info_key = RedisKeyConstants.redis_user_info_key
table_name_add = ""


# 小店后台插入数据库
def insert_creator_user(data):
    mysql = Mysql()
    creator_user = data["creator_user"]
    creator_user_insert_sql = f"""INSERT INTO `TIKTOK_CREATOR_USER_INFO{table_name_add}`(user_id,creator_oecuid,
    unique_id,units_sold_range,selection_region,med_gmv_revenue_range,creator_bind_mcn_name,industry_groups,
    top_follower_gender,top_follower_ages,follower_cnt,top_follower_age,video_avg_view_cnt,create_by,create_time) 
    VALUES(%(user_id)s, %(creator_oecuid)s, %(handle)s,%(units_sold_range)s,%(selection_region)s,
    %(med_gmv_revenue_range)s,%(creator_bind_mcn_name)s,%(industry_groups)s, %(top_follower_gender)s,
    %(top_follower_ages)s,%(follower_cnt)s, %(top_follower_age)s, %(video_avg_view_cnt)s,'python-tiktok-shop-partner','{time.strftime('%Y-%m-%d %H:%M:%S')}' )"""

    try:
        mysql.insertOne(creator_user_insert_sql, creator_user)
    except Exception as ex:
        mysql.dispose(isEnd=0)
        logging.logger.error(ex)
        logging.logger.error(creator_user)
        raise Exception(ex)

    user_info = data["user_data"]
    user_info_insert_sql = f"""INSERT INTO `TIKTOK_USER_INFO{table_name_add}`(id,unique_id,nickname,avatar_larger,
    avatar_medium,avatar_thumb,signature,region,sec_uid,bio_link,create_by,create_time) VALUES(%(id)s, %(unique_id)s,
    %(nickname)s, %(avatar_larger)s, %(avatar_medium)s,%(avatar_thumb)s,%(signature)s,%(region)s, %(sec_uid)s,
    %(bio_link)s,'python-tiktok-shop-partner','{time.strftime('%Y-%m-%d %H:%M:%S')}' )"""
    try:
        mysql.insertOne(user_info_insert_sql, user_info)
    except Exception as ex:
        mysql.dispose(isEnd=0)
        logging.logger.error(ex)
        logging.logger.error(user_info)
        raise Exception(ex)

    user_stats = data["user_stats"]
    user_stats_insert_sql = f"""INSERT INTO `TIKTOK_USER_STATS{table_name_add}`(user_id,follower_count,
    following_count,heart,heart_count,video_count,digg_count,friend_count,create_by,create_time) VALUES(%(user_id)s, 
    %(follower_count)s, %(following_count)s, %(heart)s, %(heart_count)s,%(video_count)s, %(digg_count)s, 
    %(friend_count)s,'python-tiktok-shop-partner','{time.strftime('%Y-%m-%d %H:%M:%S')}')"""
    try:
        mysql.insertOne(user_stats_insert_sql, user_stats)
    except Exception as ex:
        mysql.dispose(isEnd=0)
        logging.logger.error(ex)
        logging.logger.error(user_stats)
        raise Exception(ex)
    mysql.dispose()


# Creator Marketplace 平台插入数据库
def insert_creator_marketplacce(data):
    mysql = Mysql()
    creator_user_insert_sql = f"""INSERT INTO TIKTOK_CREATOR_USER_INFO{table_name_add} ( user_id,creator_oecuid,
    unique_id,industry_groups,create_by,create_time,origin) VALUES(%(user_id)s, %(creator_oecuid)s, %(handle)s,%(industry_groups)s,
    'python','{time.strftime('%Y-%m-%d %H:%M:%S')}',1)"""
    try:
        tag_list = []
        for tag in data.get("tags"):
            industry_data = tagsEnums.tags.get(tag)
            if industry_data is not None:
                tag_list.append(industry_data)
            else:
                tag_list.append(tag)
        tag_data = ",".join(tag_list)
        creator_data = {
            "user_id": data.get("uid"),
            "creator_oecuid": data.get("id"),
            "handle": data.get("handle_name"),
            "industry_groups": tag_data,
        }
        mysql.insertOne(creator_user_insert_sql, creator_data)
    except Exception as ex:
        mysql.dispose(isEnd=0)
        logging.logger.error(ex)
        logging.logger.error(data)
        raise Exception(ex)

    user_info_insert_sql = f"""INSERT INTO `TIKTOK_USER_INFO{table_name_add}`(id,unique_id,nickname,avatar_larger,
    signature, region,create_time,create_by,origin) VALUES(%(id)s, %(unique_id)s, %(nickname)s, %(avatar_larger)s,
    %(signature)s,%(region)s,'{time.strftime('%Y-%m-%d %H:%M:%S')}','python',1)"""
    try:
        signature = re.search(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',
                              data.get("brief"), 0)
        if signature is not None:
            signature = signature.group()
        else:
            signature = ""
        user_info = {"id": data.get("uid"),
                     "unique_id": data.get("handle_name"),
                     "nickname": data.get("nick_name"),
                     "avatar_larger": data.get("avatar_url"),
                     "signature": signature,
                     "region": data.get("region").get("active_country")
                     }

        mysql.insertOne(user_info_insert_sql, user_info)
    except Exception as ex:
        mysql.dispose(isEnd=0)
        logging.logger.error(ex)
        logging.logger.error(data)
        raise Exception(ex)

    user_stats_insert_sql = f"""INSERT INTO TIKTOK_USER_STATS{table_name_add} (user_id,follower_count,
    video_count,create_by,create_time,origin) VALUES(%(user_id)s, %(follower_count)s, 
    %(video_count)s,'python','{time.strftime('%Y-%m-%d %H:%M:%S')}','1')"""
    try:
        performance = data.get("performance")
        user_stats = {
            "user_id": data.get("uid"),
            "follower_count": performance.get("fans_cnt"),
            "video_count": performance.get("median_views"),
        }
        mysql.insertOne(user_stats_insert_sql, user_stats)
    except Exception as ex:
        mysql.dispose(isEnd=0)
        logging.logger.error(ex)
        logging.logger.error(user_stats)
        raise Exception(ex)
    mysql.dispose()


def get_table_index(data_num):
    table_name = ""
    # TODO 暂时不需要分表
    # mysql = Mysql()
    # table_index = createTableUtils.get_table_index()
    # this_index = f"_{table_index["this_index"]}" if table_index["this_index"] != 0 else ""
    # result = mysql.getOne(f"select count(id) as num from tiktok_user_info{this_index}")
    # if result["num"] + data_num > Config.MAX_TABLE_NUM:
    #     table_name = "_" + str(table_index["next_index"])
    #     createTableUtils.create_new_table()
    # elif table_index["this_index"] != 0:
    #     table_name = "_" + str(table_index["this_index"])
    # mysql.close_create()
    global table_name_add
    table_name_add = table_name


def insert_data(data, unique_id_list):
    if len(data) == 0:
        return
    get_table_index(len(data))
    lock = redisLock.acquire_lock(RedisKeyConstants.lock_insert_data)
    insert_num = 0
    if lock:
        try:
            for uniq_id in unique_id_list:
                handle = str(uniq_id["handle"]["value"])
                try:
                    if data.get(handle) is None:
                        continue
                    insert_creator_user(data[handle])
                    redis_client.set(redis_user_info_key + handle, json.dumps(data[handle]))
                    insert_num = insert_num + 1
                except Exception as ex:
                    logging.logger.error(handle + "出错!")
                    logging.logger.error(ex)
        finally:
            redisLock.release_lock(RedisKeyConstants.lock_insert_data, lock)
    return insert_num


def updateSearchKey(search_key, state):
    mysql = Mysql()
    mysql.update("update search_key set state = %s where id = %s", [state, str(search_key)])
    mysql.dispose()


def insert_data_creator_marketplace(data):
    if len(data) == 0:
        return 0
    get_table_index(len(data))
    lock = redisLock.acquire_lock(RedisKeyConstants.lock_insert_data)
    no_insert_num = 0
    if lock:
        try:
            for user in data:
                handle = user["base_info"]
                try:
                    if redis_client.get(RedisKeyConstants.redis_user_info_key + handle["handle_name"]) is not None:
                        no_insert_num = no_insert_num + 1
                        continue
                    insert_creator_marketplacce(handle)
                    redis_client.set(redis_user_info_key + handle["handle_name"], "")
                except Exception as ex:
                    logging.logger.error(handle["handle_name"] + "出错!")
                    logging.logger.error(ex)
        finally:
            redisLock.release_lock(RedisKeyConstants.lock_insert_data, lock)
    logging.logger.info(f"总共插入{len(data)}条数据，其中重复{no_insert_num}条")
    return len(data) - no_insert_num
