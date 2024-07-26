from MySqlCon import Mysql
import log
import json
import redis

# 申请资源


logging = log.Logger("sql.log", level='INFO')

# sqlAll = "SELECT * FROM tiktok_user_stats where user_id =  %(user_id)s"
# result = mysql.getAll(sqlAll, {"user_id": "1"})
# if result:
#     for row in result:
#         print(row)
# 释放资源

# data = [{"user_id": "2", "follower_count": "1", "following_count": "1", "heart": "1", "heart_count": "1",
#          "video_count": "1", "digg_count": "1", "friend_count": "1"}]
redis_client = redis.Redis(host="localhost", port=6379, db=0)

print(redis_client.get("python_data_crawl_tiktok_num"))

redis_user_stats_key = "user_stats:"


def insert_user_stats(data):
    mysql = Mysql()
    insert_sql = (
        "INSERT INTO `TIKTOK_USER_STATS`(user_id,follower_count,following_count,heart,heart_count,video_count,"
        "digg_count,friend_count) VALUES(%(user_id)s, %(follower_count)s, %(following_count)s, %(heart)s,"
        "%(heart_count)s,%(video_count)s, %(digg_count)s, %(friend_count)s)")
    update_sql = (
        "UPDATE `TIKTOK_USER_STATS` SET follower_count=%(follower_count)s,following_count=%(following_count)s,"
        "heart=%(heart)s,heart_count=%(heart_count)s,video_count=%(video_count)s,"
        "digg_count=%(digg_count)s,friend_count= %(friend_count)s WHERE user_id = %(user_id)s")
    try:
        for user_stats in data:
            redis_stats_id = redis_client.get(redis_user_stats_key + user_stats["user_id"])
            if redis_stats_id is None:
                redis_client.set(redis_user_stats_key + user_stats["user_id"], user_stats)
        # mysql.insertMany(sql, data)
    except Exception as ex:
        logging.logger.error(ex)
    finally:
        mysql.dispose()
