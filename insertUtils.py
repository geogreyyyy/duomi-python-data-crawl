from MySqlCon import Mysql
import log
import json
import redis

# 申请资源
logging = log.Logger("sql.log", level='INFO')

redis_client = redis.Redis(host="localhost", port=6379, db=0)
redis_pipe = redis_client.pipeline()

redis_user_info_key = "tiktok_user_info:"


def insert_creator_user(data, redis_stats_id):
    mysql = Mysql()
    creator_user = data["creator_user"]
    creator_user_insert_sql = (
        "INSERT INTO `TIKTOK_CREATOR_USER_INFO`("
        "user_id,creator_oecuid,unique_id,units_sold_range,"
        "selection_region,med_gmv_revenue_range,creator_bind_mcn_name,industry_groups,top_follower_gender,"
        "top_follower_ages,follower_cnt,top_follower_age,video_avg_view_cnt"
        ") VALUES("
        "%(user_id)s, %(creator_oecuid)s, %(handle)s,%(units_sold_range)s,%(selection_region)s,"
        "%(med_gmv_revenue_range)s,%(creator_bind_mcn_name)s,%(industry_groups)s, %(top_follower_gender)s, "
        "%(top_follower_ages)s,%(follower_cnt)s,%(top_follower_age)s, %(video_avg_view_cnt)s )"
    )
    creator_user_update_sql = (
        "UPDATE `TIKTOK_CREATOR_USER_INFO` SET unique_id = %(handle)s,"
        "units_sold_range=%(units_sold_range)s,selection_region=%(selection_region)s,med_gmv_revenue_range=%("
        "med_gmv_revenue_range)s,creator_bind_mcn_name=%(creator_bind_mcn_name)s,industry_groups=%(industry_groups)s,"
        "top_follower_gender=%(top_follower_gender)s,top_follower_ages=%(top_follower_ages)s,follower_cnt=%("
        "follower_cnt)s,top_follower_age=%(top_follower_age)s,video_avg_view_cnt=%(video_avg_view_cnt)s"
        "WHERE user_id = %(user_id)s")
    try:
        if redis_stats_id:
            mysql.update(creator_user_update_sql, creator_user)
        else:
            mysql.insertOne(creator_user_insert_sql, creator_user)

    except Exception as ex:
        logging.logger.error(creator_user)
        logging.logger.error(ex)
        mysql.dispose(isEnd=0)
        return

    user_info = data["user_data"]
    user_info_insert_sql = (
        "INSERT INTO `TIKTOK_USER_INFO`(id,unique_id,nickname,avatar_larger,avatar_medium,avatar_thumb,"
        "signature,region,sec_uid,bio_link) VALUES(%(id)s, %(unique_id)s, %(nickname)s, %(avatar_larger)s, "
        "%(avatar_medium)s,%(avatar_thumb)s,%(signature)s,%(region)s, %(sec_uid)s, %(bio_link)s)")
    user_info_update_sql = (
        "UPDATE `TIKTOK_USER_INFO` SET unique_id=%(unique_id)s,nickname=%(nickname)s,"
        "avatar_larger=%(avatar_larger)s,avatar_medium=%(avatar_medium)s,avatar_thumb=%(avatar_thumb)s,"
        "signature=%(signature)s,region= %(region)s,sec_uid= %(sec_uid)s,bio_link= %(bio_link)s WHERE id = %(id)s")
    try:
        if redis_stats_id:
            mysql.update(user_info_update_sql, user_info)
        else:
            mysql.insertOne(user_info_insert_sql, user_info)
    except Exception as ex:
        logging.logger.error(user_info)
        logging.logger.error(ex)
        mysql.dispose(isEnd=0)
        return

    user_stats = data["user_stats"]
    user_stats_insert_sql = (
        "INSERT INTO `TIKTOK_USER_STATS`(user_id,follower_count,following_count,heart,heart_count,video_count,"
        "digg_count,friend_count) VALUES(%(user_id)s, %(follower_count)s, %(following_count)s, %(heart)s,"
        "%(heart_count)s,%(video_count)s, %(digg_count)s, %(friend_count)s)")
    user_stats_update_sql = (
        "UPDATE `TIKTOK_USER_STATS` SET follower_count=%(follower_count)s,following_count=%(following_count)s,"
        "heart=%(heart)s,heart_count=%(heart_count)s,video_count=%(video_count)s,"
        "digg_count=%(digg_count)s,friend_count= %(friend_count)s WHERE user_id = %(user_id)s")
    try:
        if redis_stats_id:
            mysql.update(user_stats_update_sql, user_stats)
        else:
            mysql.insertOne(user_stats_insert_sql, user_stats)
    except Exception as ex:
        logging.logger.error(user_stats)
        logging.logger.error(ex)
        mysql.dispose(isEnd=0)
        return
    mysql.dispose()


def insert_data(data, unique_id_list):
    if len(data) == 0:
        return
    for uniq_id in unique_id_list:
        handle = uniq_id["handle"]["value"]
        redis_stats_id = redis_client.get(redis_user_info_key + handle)
        try:
            if redis_stats_id:
                insert_creator_user(data[handle], True)
            else:
                insert_creator_user(data[handle], False)
            redis_client.set(redis_user_info_key + handle, json.dumps(data[handle]))
        except Exception as ex:
            logging.logger.error(handle+"出错!")
            logging.logger.error(ex)

