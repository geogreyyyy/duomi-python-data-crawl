import json
import re
import sys
import time

import redis

import log

sys.path.append("..")
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


def update_creator_user(data):
    mysql = Mysql()
    creator_data = data.get("creator_user")
    if creator_data is not None:
        creator_user_update_sql = f"""  
        UPDATE `TIKTOK_CREATOR_USER_INFO{table_name_add}`
        SET creator_oecuid = %(creator_oecuid)s,  
            unique_id = %(handle)s, 
            nickname = %(nickname)s, 
            units_sold_range = %(units_sold_range)s,  
            thumb_url_list =%(thumb_url_list)s,  
            top_video_data =%(top_video_data)s,  
            url_list = %(url_list)s,
            units_sold = %(units_sold)s,  
            selection_region = %(selection_region)s,  
            med_gmv_revenue_range = %(med_gmv_revenue_range)s,  
            med_gmv_revenue = %(med_gmv_revenue)s,  
            creator_bind_mcn_name = %(creator_bind_mcn_name)s,  
            industry_groups = %(industry_groups)s,  
            top_follower_gender = %(top_follower_gender)s,  
            top_follower_ages = %(top_follower_ages)s,  
            follower_cnt = %(follower_cnt)s,  
            top_follower_age = %(top_follower_age)s,  
            video_avg_view_cnt = %(video_avg_view_cnt)s,
            update_by = 'python-tiktok-shop-partner',
            update_time = '{time.strftime('%Y-%m-%d %H:%M:%S')}'
        WHERE user_id = %(user_id)s  
        """
        try:
            mysql.update(creator_user_update_sql, creator_data)
        except Exception as ex:
            mysql.dispose(isEnd=0)
            logging.logger.error(ex)
            logging.logger.error(creator_data)
            raise Exception(ex)
    user_info = data.get("user_data")
    if user_info is not None:
        user_info_update_sql = f"""  
        UPDATE `TIKTOK_USER_INFO{table_name_add}`  
        SET unique_id = %(unique_id)s,  
            nickname = %(nickname)s,  
            avatar_larger = %(avatar_larger)s,  
            avatar_medium = %(avatar_medium)s,  
            avatar_thumb = %(avatar_thumb)s,  
            signature = %(signature)s,  
            region = %(region)s,  
            sec_uid = %(sec_uid)s,  
            bio_link = %(bio_link)s,  
            update_by = 'python-tiktok-shop-partner',
            update_time = '{time.strftime('%Y-%m-%d %H:%M:%S')}'
        WHERE id = %(id)s  
        """
        try:
            mysql.update(user_info_update_sql, user_info)
        except Exception as ex:
            mysql.dispose(isEnd=0)
            logging.logger.error(ex)
            logging.logger.error(user_info)
            raise Exception(ex)
    user_stats_data = data.get("user_stats")
    if user_stats_data is not None:
        user_stats_update_sql = f"""  
        UPDATE `TIKTOK_USER_STATS{table_name_add}`  
        SET follower_count = %(follower_count)s,  
            following_count = %(following_count)s,  
            heart = %(heart)s,
            heart_count = %(heart_count)s,  
            video_count = %(video_count)s,  
            digg_count = %(digg_count)s,  
            friend_count = %(friend_count)s,  
            update_by = 'python-tiktok-shop-partner',
            update_time = '{time.strftime('%Y-%m-%d %H:%M:%S')}'
        WHERE user_id = %(user_id)s  
        """
        try:
            mysql.update(user_stats_update_sql, user_stats_data)
        except Exception as ex:
            mysql.dispose(isEnd=0)
            logging.logger.error(ex)
            logging.logger.error(user_stats_data)
            raise Exception(ex)
    mysql.dispose()


# 小店后台插入数据库
def insert_creator_user(data):
    mysql = Mysql()
    creator_user = data["creator_user"]
    creator_user_insert_sql = f"""INSERT INTO `TIKTOK_CREATOR_USER_INFO{table_name_add}`(user_id,creator_oecuid,nickname,
    unique_id,thumb_url_list,url_list,top_video_data,units_sold_range,units_sold,selection_region,med_gmv_revenue,med_gmv_revenue_range,creator_bind_mcn_name,industry_groups,
    top_follower_gender,top_follower_ages,follower_cnt,top_follower_age,video_avg_view_cnt,create_by,create_time) 
    VALUES(%(user_id)s, %(creator_oecuid)s, %(nickname)s, %(handle)s,%(thumb_url_list)s,%(url_list)s,%(top_video_data)s,%(units_sold_range)s,%(units_sold)s,%(selection_region)s,
    %(med_gmv_revenue)s,%(med_gmv_revenue_range)s,%(creator_bind_mcn_name)s,%(industry_groups)s, %(top_follower_gender)s,
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
    insert_num = 0
    update_num = 0
    if len(data) == 0:
        return insert_num
    get_table_index(len(data))
    lock = redisLock.acquire_lock(RedisKeyConstants.lock_insert_data)
    if lock:
        try:
            for uniq_id in unique_id_list:
                handle = str(uniq_id["handle"]["value"])
                try:
                    if data.get(handle) is None:
                        continue
                    if redis_client.get(RedisKeyConstants.redis_user_info_key + handle) is None:
                        insert_creator_user(data[handle])
                        insert_num = insert_num + 1
                        redis_client.set(redis_user_info_key + handle, json.dumps(data[handle]))
                    else:
                        update_creator_user(data[handle])
                        update_num = update_num + 1
                except Exception as ex:
                    logging.logger.error(handle + "出错!")
                    logging.logger.error(ex)
        finally:
            redisLock.release_lock(RedisKeyConstants.lock_insert_data, lock)
    return [insert_num, update_num]


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


def record_data(data, unique_id_list):
    if len(data) == 0:
        return
    get_table_index(len(data))
    lock = redisLock.acquire_lock(RedisKeyConstants.lock_insert_data)
    insert_num = 0
    update_num = 0
    if lock:
        try:
            for handle in unique_id_list:
                try:
                    if redis_client.get(RedisKeyConstants.redis_user_info_key + handle) is not None:
                        update_creator_user(data[handle])
                        update_num = update_num + 1
                    else:
                        insert_creator_user(data[handle])
                        insert_num = insert_num + 1
                    redis_client.set(redis_user_info_key + handle, json.dumps(data[handle]))
                except Exception as ex:
                    logging.logger.error(handle + "出错!")
                    logging.logger.error(ex)
                    # 如果是主键冲突，写入redis
                    if str(ex).find("Duplicate entry") != -1:
                        redis_client.set(redis_user_info_key + handle, json.dumps(data[handle]))
        finally:
            redisLock.release_lock(RedisKeyConstants.lock_insert_data, lock)
    return [insert_num, update_num]


# 设置用户属性 --------爬取达人数据
def set_user_info_partner(user_data, user_stats, create_user_info):
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
            resp_data_user_data["bio_link"] = json.dumps(user_data.get('bioLink', ''))
            # create_user_info
            resp_data_creator_data["creator_oecuid"] = create_user_info.get('creator_oecuid').get("value", "")
            resp_data_creator_data["user_id"] = user_data.get('id')
            resp_data_creator_data["handle"] = create_user_info.get('handle').get("value", "")
            resp_data_creator_data["nickname"] = create_user_info.get('nickname').get("value", "")
            # 头像
            avatar = create_user_info.get("avatar")
            if avatar.get("is_authorized"):
                resp_data_creator_data["thumb_url_list"] = json.dumps(avatar.get("value").get("thumb_url_list", {}))
                resp_data_creator_data["url_list"] = json.dumps(avatar.get("value").get("url_list", {}))
            else:
                resp_data_creator_data["thumb_url_list"] = "[]"
                resp_data_creator_data["url_list"] = "[]"
            if create_user_info.get('is_authorized') is not None:
                resp_data_creator_data["is_authorized"] = 1 if create_user_info.get('is_authorized').get("value",
                                                                                                         "") else 2
            # 成交件大概范围
            if create_user_info.get('units_sold_range') is not None:
                resp_data_creator_data["units_sold_range"] = create_user_info.get('units_sold_range').get("value", "")
            # 成交件数
            if create_user_info.get('units_sold') is not None:
                resp_data_creator_data["units_sold"] = create_user_info.get('units_sold').get("value", "")
            if create_user_info.get('selection_region') is not None:
                resp_data_creator_data["selection_region"] = create_user_info.get('selection_region').get("value", "")
            # GMV大概范围
            if create_user_info.get('med_gmv_revenue_range') is not None:
                resp_data_creator_data["med_gmv_revenue_range"] = create_user_info.get('med_gmv_revenue_range').get(
                    "value",
                    "")
            # GMV详细数据
            if create_user_info.get('med_gmv_revenue').get("is_authorized"):
                resp_data_creator_data["med_gmv_revenue"] = json.dumps(create_user_info.get('med_gmv_revenue').get("value"))
            else:
                resp_data_creator_data["med_gmv_revenue"] = "{}"
            # MCN机构
            resp_data_creator_data["creator_bind_mcn_name"] = ''
            if create_user_info.get('creator_bind_mcn_name') is not None:
                creator_bind_mcn_name = create_user_info.get('creator_bind_mcn_name')
                if creator_bind_mcn_name.get("value") is not None:
                    resp_data_creator_data["creator_bind_mcn_name"] = json.dumps(
                        create_user_info.get('creator_bind_mcn_name').get("value", ""))
            # 达人兴趣标签
            resp_data_creator_data["industry_groups"] = ''
            if create_user_info.get('category') is not None:
                industry_groups = []
                category_value = create_user_info.get('category').get("value", [])
                for name in category_value:
                    industry_groups.append(name["name"])
                resp_data_creator_data["industry_groups"] = ",".join(industry_groups)
            # 视频信息
            if create_user_info.get("top_video_data").get("is_authorized"):
                resp_data_creator_data["top_video_data"] = json.dumps(
                    create_user_info.get("top_video_data").get("value", {}))
            if create_user_info.get('top_follower_gender') is not None:
                resp_data_creator_data["top_follower_gender"] = json.dumps(
                    create_user_info.get('top_follower_gender').get("value", ""))
            if create_user_info.get('top_follower_ages') is not None:
                resp_data_creator_data["top_follower_ages"] = ",".join(
                    create_user_info.get('top_follower_ages').get("value", ""))
            if create_user_info.get('follower_cnt') is not None:
                resp_data_creator_data["follower_cnt"] = create_user_info.get('follower_cnt').get("value", "")
            if create_user_info.get('top_follower_age') is not None:
                resp_data_creator_data["top_follower_age"] = json.dumps(
                    create_user_info.get('top_follower_age').get("value", ""))
            if create_user_info.get('video_avg_view_cnt') is not None:
                resp_data_creator_data["video_avg_view_cnt"] = create_user_info.get('video_avg_view_cnt').get("value",
                                                                                                              "")
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
