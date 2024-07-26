import pymysql
import log

logging = log.Logger("sql.log", level='INFO')

db = pymysql.connect(
    host='127.0.0.1',
    port=3306,
    user='root',
    passwd='123456',
    db='crm-data-crawl',
    charset='utf8'
)


# data = cursor.fetchone()
# print("Database version : %s " % data)
def insert_tiktok_user_info(user_id, unique_id, nickname, avatar_larger, avatar_medium, avatar_thumb, signature, region,
                            sec_uid, bio_link):
    try:
        cursor = db.cursor()
        # 使用预处理语句创建表
        sql = "INSERT INTO TIKTOK_USER_INFO(id,unique_id, nickname, avatar_larger, avatar_medium,avatar_thumb,signature,region,sec_uid,bio_link) VALUES (" + user_id + "," + unique_id + "," + nickname + "," + avatar_larger + "," + avatar_medium + "," + avatar_thumb + "," + signature + "," + region + "," + sec_uid + "," + bio_link + ")"
        # 执行sql语句
        logging.logger.info(sql)
        cursor.execute(sql)
        # 提交到数据库执行
        db.commit()
    except Exception as ex:
        logging.logger.error(ex)
        db.rollback()
    finally:
        db.close()


def insert_tiktok_creator_info(user_id, creator_oecuid, is_authorized, handle, units_sold_range, selection_region,
                               med_gmv_revenue_range, creator_bind_mcn_name, industry_groups, top_follower_gender,
                               top_follower_ages, follower_cnt, top_follower_age, video_avg_view_cnt):
    try:
        cursor = db.cursor()
        # 使用预处理语句创建表
        sql = ("""INSERT INTO TIKTOK_CREATOR_USER_INFO(
        id,creator_oecuid, is_authorized, handle, units_sold_range,selection_region,med_gmv_revenue_range,creator_bind_mcn_name,industry_groups,top_follower_gender,top_follower_ages,follower_cnt,top_follower_age,video_avg_view_cnt
        ) VALUES ('"""
               + user_id + "','" + creator_oecuid + "','" + is_authorized + "','" + handle + "','" + units_sold_range + "','" + selection_region + "','" + med_gmv_revenue_range + "','" + creator_bind_mcn_name + "','" + industry_groups + "','" + top_follower_gender + "','" + top_follower_ages + "','" + follower_cnt + "','" + top_follower_age + "','" + video_avg_view_cnt + "')")
        # 执行sql语句
        logging.logger.info(sql)
        cursor.execute(sql)
        # 提交到数据库执行
        db.commit()
    except Exception as ex:
        logging.logger.error(ex)
        db.rollback()
    finally:
        db.close()


def insert_tiktok_user_stats(user_id, follower_count, following_count, heart, heart_count, video_count, digg_count,
                             friend_count):
    try:
        cursor = db.cursor()
        # 使用预处理语句创建表
        sql = ("""INSERT INTO TIKTOK_USER_STATS(
        user_id,follower_count,following_count,heart,heart_count,video_count,digg_count,friend_count
        ) VALUES ('"""
               + user_id + "','" + follower_count + "','" + following_count + "','" + heart + "','" + heart_count +
               "','" + video_count + "','" + digg_count + "','" + friend_count + "')")
        # 执行sql语句
        logging.logger.info(sql)
        cursor.execute(sql)
        # 提交到数据库执行
        db.commit()
    except Exception as ex:
        logging.logger.error(ex)
        db.rollback()
    finally:
        db.close()


# insert_tiktok_user_info("1", "id", "id", "id", "id", "id", "id", "id", "id", "id")
# insert_tiktok_creator_info("1", "2", "4", "5", "6", "3", "你好", "测试", "i测试d", "id测试", "ivd", "i测试d", "测试",
#                            "测试")
# insert_tiktok_user_stats("1", "2", "4", "5", "6", "3", "123", "123")
