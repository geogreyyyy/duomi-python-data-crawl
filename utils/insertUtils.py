import time

import log
import json
import redis
import sys
import re

sys.path.append("..")
from utils import createTableUtils
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
def insert_creator_user(data, redis_stats_id):
    mysql = Mysql()
    creator_user = data["creator_user"]
    creator_user_insert_sql = (
            "INSERT INTO `TIKTOK_CREATOR_USER_INFO" + table_name_add + "`("
                                                                       "user_id,creator_oecuid,unique_id,units_sold_range,"
                                                                       "selection_region,med_gmv_revenue_range,creator_bind_mcn_name,industry_groups,top_follower_gender,"
                                                                       "top_follower_ages,follower_cnt,top_follower_age,video_avg_view_cnt"
                                                                       ") VALUES("
                                                                       "%(user_id)s, %(creator_oecuid)s, %(handle)s,%(units_sold_range)s,%(selection_region)s,"
                                                                       "%(med_gmv_revenue_range)s,%(creator_bind_mcn_name)s,%(industry_groups)s, %(top_follower_gender)s, "
                                                                       "%(top_follower_ages)s,%(follower_cnt)s,%(top_follower_age)s, %(video_avg_view_cnt)s )"
    )
    creator_user_update_sql = (
            "UPDATE `TIKTOK_CREATOR_USER_INFO" + table_name_add + "` SET unique_id = %(handle)s,"
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
        mysql.dispose(isEnd=0)
        logging.logger.error(ex)
        logging.logger.error(creator_user)
        raise Exception(ex)

    user_info = data["user_data"]
    user_info_insert_sql = (
            "INSERT INTO `TIKTOK_USER_INFO" + table_name_add + "`(id,unique_id,nickname,avatar_larger,avatar_medium,avatar_thumb,"
                                                               "signature,region,sec_uid,bio_link) VALUES(%(id)s, %(unique_id)s, %(nickname)s, %(avatar_larger)s, "
                                                               "%(avatar_medium)s,%(avatar_thumb)s,%(signature)s,%(region)s, %(sec_uid)s, %(bio_link)s)")
    user_info_update_sql = (
            "UPDATE `TIKTOK_USER_INFO" + table_name_add + "` SET unique_id=%(unique_id)s,nickname=%(nickname)s,"
                                                          "avatar_larger=%(avatar_larger)s,avatar_medium=%(avatar_medium)s,avatar_thumb=%(avatar_thumb)s,"
                                                          "signature=%(signature)s,region= %(region)s,sec_uid= %(sec_uid)s,bio_link= %(bio_link)s WHERE id = %(id)s")
    try:
        if redis_stats_id:
            mysql.update(user_info_update_sql, user_info)
        else:
            mysql.insertOne(user_info_insert_sql, user_info)
    except Exception as ex:
        mysql.dispose(isEnd=0)
        logging.logger.error(ex)
        logging.logger.error(user_info)
        raise Exception(ex)

    user_stats = data["user_stats"]
    user_stats_insert_sql = (
            "INSERT INTO `TIKTOK_USER_STATS" + table_name_add + "`(user_id,follower_count,following_count,heart,heart_count"
                                                                ",video_count,"
                                                                "digg_count,friend_count) VALUES(%(user_id)s, %(follower_count)s, %(following_count)s, %(heart)s,"
                                                                "%(heart_count)s,%(video_count)s, %(digg_count)s, %(friend_count)s)")
    user_stats_update_sql = (
            "UPDATE `TIKTOK_USER_STATS" + table_name_add + "` SET follower_count=%(follower_count)s,following_count=%("
                                                           "following_count)s,"
                                                           "heart=%(heart)s,heart_count=%(heart_count)s,video_count=%(video_count)s,"
                                                           "digg_count=%(digg_count)s,friend_count= %(friend_count)s WHERE user_id = %(user_id)s")
    try:
        if redis_stats_id:
            mysql.update(user_stats_update_sql, user_stats)
        else:
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
    # creator_user_insert_sql = (
    #         "INSERT INTO `TIKTOK_CREATOR_USER_INFO" + table_name_add + "`("
    #                                                                    "user_id,creator_oecuid,unique_id,units_sold_range,"
    #                                                                    "selection_region,med_gmv_revenue_range,creator_bind_mcn_name,industry_groups,top_follower_gender,"
    #                                                                    "top_follower_ages,follower_cnt,top_follower_age,video_avg_view_cnt"
    #                                                                    ") VALUES("
    #                                                                    "%(user_id)s, %(creator_oecuid)s, %(handle)s,%(units_sold_range)s,%(selection_region)s,"
    #                                                                    "%(med_gmv_revenue_range)s,%(creator_bind_mcn_name)s,%(industry_groups)s, %(top_follower_gender)s, "
    #                                                                    "%(top_follower_ages)s,%(follower_cnt)s,%(top_follower_age)s, %(video_avg_view_cnt)s )"
    # )
    #
    # try:
    #    mysql.insertOne(creator_user_insert_sql, data)
    # except Exception as ex:
    #     mysql.dispose(isEnd=0)
    #     logging.logger.error(ex)
    #     logging.logger.error(data)
    #     raise Exception(ex)
    user_info_insert_sql = f"""INSERT INTO `TIKTOK_USER_INFO{table_name_add}`(id,unique_id,nickname,avatar_larger,
    signature, region,create_time,create_by,origin) VALUES(%(uid)s, %(handle_name)s, %(nick_name)s, %(avatar_url)s, 
    %(brief)s,%(region)s,{time.time()},'python',1))"""
    try:
        data["brief"] = re.search(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',
                                  data.get("brief"), 0)
        data["region"] = data.get("region").get("active_country")
        mysql.insertOne(user_info_insert_sql, json.dumps(data))
    except Exception as ex:
        mysql.dispose(isEnd=0)
        logging.logger.error(ex)
        logging.logger.error(data)
        raise Exception(ex)

    # user_stats = data["user_stats"]
    # user_stats_insert_sql = (
    #         "INSERT INTO `TIKTOK_USER_STATS" + table_name_add + "`(user_id,follower_count,following_count,heart,heart_count"
    #                                                             ",video_count,"
    #                                                             "digg_count,friend_count) VALUES(%(user_id)s, %(follower_count)s, %(following_count)s, %(heart)s,"
    #                                                             "%(heart_count)s,%(video_count)s, %(digg_count)s, %(friend_count)s)")
    # try:
    #     mysql.insertOne(user_stats_insert_sql, user_stats)
    # except Exception as ex:
    #     mysql.dispose(isEnd=0)
    #     logging.logger.error(ex)
    #     logging.logger.error(user_stats)
    #     raise Exception(ex)
    mysql.dispose()


def get_table_index(data_num):
    table_name = ""
    mysql = Mysql()
    table_index = createTableUtils.get_table_index()
    this_index = f"_{table_index["this_index"]}" if table_index["this_index"] != 0 else ""
    result = mysql.getOne(f"select count(id) as num from tiktok_user_info{this_index}")
    if result["num"] + data_num > Config.MAX_TABLE_NUM:
        table_name = "_" + str(table_index["next_index"])
        createTableUtils.create_new_table()
    elif table_index["this_index"] != 0:
        table_name = "_" + str(table_index["this_index"])
    mysql.close_create()
    global table_name_add
    table_name_add = table_name


def insert_data(data, unique_id_list):
    if len(data) == 0:
        return
    get_table_index(len(data))
    lock = redisLock.acquire_lock(RedisKeyConstants.lock_insert_data)
    if lock:
        try:
            for uniq_id in unique_id_list:
                handle = str(uniq_id["handle"]["value"])
                try:
                    if data.get(handle) is None:
                        raise Exception("储存数据中：" + handle + " 不存在")
                    redis_stats_id = redis_client.get(redis_user_info_key + handle)
                    if redis_stats_id:
                        insert_creator_user(data[handle], True)
                    else:
                        insert_creator_user(data[handle], False)
                    redis_client.set(redis_user_info_key + handle, json.dumps(data[handle]))
                except Exception as ex:
                    logging.logger.error(handle + "出错!")
                    logging.logger.error(ex)
        finally:
            redisLock.release_lock(RedisKeyConstants.lock_insert_data, lock)


def updateSearchKey(search_key, state):
    mysql = Mysql()
    mysql.update("update search_key set state = %s where id = %s", [state, str(search_key)])
    mysql.dispose()


data_list = [
    {
        "privilege": {
            "badges": [
                {
                    "badge_type": 5
                }
            ]
        },
        "feature_info": {
            "recent_items": [
                {
                    "comment": "75",
                    "heart": "8830",
                    "hide": False,
                    "video_url": "https://v77.tiktokcdn.com/18cd698933b2208d3ebc4da4f0e59ffd/66cc8c04/video/tos/maliva/tos-maliva-ve-0068c799-us/osQyFtFGUYasxBRyeAb3AfetB4A7MKQg4eESDC/?a=2043&bti=NjQ7OGYwLzA6&ch=0&cr=0&dr=0&er=0&lr=default&cd=0%7C0%7C0%7C0&cv=1&br=2588&bt=1294&cs=0&ds=6&ft=.NpOcInz7ThdTJOrXq8Zmo&mime_type=video_mp4&qs=0&rc=OzhkZDM4ZjZoZGlnaTo5NUBpam5qZm45cmVqdDMzaTczNEAxNi0yNWFfNmMxNC4uM18xYSMuYW9eMmRrcmxgLS1kMTJzcw%3D%3D&vvpl=1&l=2024082608055808A052E0019428355A5A&btag=e00090000&cc=13",
                    "views": "71427",
                    "title": "Asi de limpio me quedó 🙌@La Familia Lopez @Orlando ",
                    "share": "32",
                    "cover_url": "https://p16-sign.tiktokcdn-us.com/obj/tos-useast8-p-0068-tx2/9ba0ae64bd0343cea578e6e1a789999f_1722879802?lk3s=c6b69ba0&nonce=94250&refresh_token=dfccf31ee8fe5d5a8e05d1672add86c4&x-expires=1725264000&x-signature=eMP89fSL4D5Mt8SO6odjtuOR%2BHM%3D&shp=c6b69ba0&shcp=-",
                    "create_time": "1722879799",
                    "item_id": "7399712319925669151",
                    "is_relevant": True
                },
                {
                    "comment": "26065",
                    "heart": "311085",
                    "hide": False,
                    "video_url": "https://v77.tiktokcdn.com/70f1b398b2c913ff7f186b1e327182bb/66cc8bd6/video/tos/useast2a/tos-useast2a-ve-0068c003/62cf30ccb1254c9aa101d6561ce6d435/?a=2043&bti=NjQ7OGYwLzA6&ch=0&cr=0&dr=0&er=0&lr=default&cd=0%7C0%7C0%7C0&cv=1&br=2906&bt=1453&cs=0&ds=6&ft=.NpOcInz7ThdTJOrXq8Zmo&mime_type=video_mp4&qs=0&rc=N2U8ZzU6PDg0PGk6ZmQ4PEBpMzQzeDc6ZnhqOTMzNzczM0BgMS4uLS5hXjQxMjZfYWNfYSMxZC4tcjRvMy5gLS1kMTZzcw%3D%3D&vvpl=1&l=2024082608055808A052E0019428355A5A&btag=e00088000&cc=13",
                    "views": "2765934",
                    "title": "Todo el que comente en este video LO SIGO … lo seguiremos para atrás @orland.94 @lafamilia_lopez @idk_britney @Orlando Leduar",
                    "share": "741",
                    "cover_url": "https://p16-sign-va.tiktokcdn.com/obj/tos-maliva-p-0068/7baaef6b45f947c5ad1004c350584378_1635976636?lk3s=c6b69ba0&nonce=69008&refresh_token=ccfe111d02107099cec4c58c58facf93&x-expires=1725264000&x-signature=Rc4ilNs71fLi1WX%2FlcVc5embhmY%3D&shp=c6b69ba0&shcp=-",
                    "create_time": "1635976628",
                    "item_id": "7026466111386422534",
                    "is_relevant": False
                },
                {
                    "comment": "284",
                    "heart": "29634",
                    "hide": False,
                    "video_url": "https://v77.tiktokcdn.com/b9fc6c472290fe42cbcbecbc156ab302/66cc8bd6/video/tos/maliva/tos-maliva-ve-0068c799-us/oYUnpIeEBjvbAADqwivjAIQhIiUdByBCy52Im4/?a=2043&bti=NjQ7OGYwLzA6&ch=0&cr=0&dr=0&er=0&lr=default&cd=0%7C0%7C0%7C0&cv=1&br=1660&bt=830&cs=0&ds=6&ft=.NpOcInz7ThdTJOrXq8Zmo&mime_type=video_mp4&qs=0&rc=OjQ8NzQ3ODtnZjdmOWQ1N0BpM2RmOnM5cngzbjMzZzczNEBiXjEzLS8wXjQxNTM0MmItYSNvZWBeMmRrb3BgLS1kMS9zcw%3D%3D&vvpl=1&l=2024082608055808A052E0019428355A5A&btag=e00088000&cc=13",
                    "views": "260400",
                    "title": "#dúo con @Orlando ",
                    "share": "28",
                    "cover_url": "https://p16-sign.tiktokcdn-us.com/obj/tos-useast5-p-0068-tx/ce5cbe73c06d4d28ace48a375c7f2338_1698172459?lk3s=c6b69ba0&nonce=43898&refresh_token=d8f77bcb8ee42feb9c3675b84b77eee1&x-expires=1725264000&x-signature=QOq2pWgKG2op5Q6XYjeJOviW1I8%3D&shp=c6b69ba0&shcp=-",
                    "create_time": "1698172458",
                    "is_bc_video": True,
                    "item_id": "7293595099630406954",
                    "is_relevant": False
                },
                {
                    "comment": "52",
                    "heart": "8860",
                    "hide": False,
                    "video_url": "https://v77.tiktokcdn.com/8306529856b104c10c0ffd331252630a/66cc8bcc/video/tos/maliva/tos-maliva-ve-0068c799-us/ocByLwEEIEAmdSwfz0FVDdLNpbGEREAeDB9RQr/?a=2043&bti=NjQ7OGYwLzA6&ch=0&cr=0&dr=0&er=0&lr=default&cd=0%7C0%7C0%7C0&cv=1&br=5620&bt=2810&cs=0&ds=6&ft=.NpOcInz7ThdTJOrXq8Zmo&mime_type=video_mp4&qs=0&rc=ZjNmOjdmPDM6NGg8Ojo1Z0BpamVqZm85cjp3dTMzaTczNEA1YjAtNi02NjAxMTUzY19gYSNobmxzMmRjMC5gLS1kMTJzcw%3D%3D&vvpl=1&l=2024082608055808A052E0019428355A5A&btag=e00088000&cc=13",
                    "views": "52978",
                    "title": "@La Familia Lopez @Orlando ",
                    "share": "26",
                    "cover_url": "https://p16-sign.tiktokcdn-us.com/obj/tos-useast8-p-0068-tx2/116becf9397147788a0e5c0a20df3ff9_1724109241?lk3s=c6b69ba0&nonce=42222&refresh_token=83f1906e7973acb708bf029c70a5dc71&x-expires=1725264000&x-signature=Zj5%2B%2FWFdPB2s90%2Bq9SDiErQA1HA%3D&shp=c6b69ba0&shcp=-",
                    "create_time": "1724109238",
                    "item_id": "7404992726837562654",
                    "is_relevant": False
                },
                {
                    "comment": "1577",
                    "heart": "192273",
                    "hide": False,
                    "video_url": "https://v16m.tiktokcdn.com/cce8d00a80d67fb7eabd7dcc3ff579ec/66cc8bd0/video/tos/useast2a/tos-useast2a-ve-0068c002/e0279a9fc68c4b7b9553994494d03af4/?a=2043&bti=NjQ7OGYwLzA6&ch=0&cr=0&dr=0&er=0&lr=default&cd=0%7C0%7C0%7C0&cv=1&br=1982&bt=991&cs=0&ds=6&ft=.NpOcInz7ThdTJOrXq8Zmo&mime_type=video_mp4&qs=0&rc=OzxmZTo0NmQ2NDc2NzM0NkBpM3lnbzQ6ZnYzOTMzNzczM0BfMi8yLTM2NS0xMTYuLjYuYSNycnM2cjRvYzNgLS1kMTZzcw%3D%3D&vvpl=1&l=2024082608055808A052E0019428355A5A&btag=e00088000&cc=3",
                    "views": "2295891",
                    "title": "No se esperaba esto 🙈🙈🙈@lafamilia_lopez @leduorland @orland.94",
                    "share": "650",
                    "cover_url": "https://p16-sign-va.tiktokcdn.com/obj/tos-maliva-p-0068/baa431a4160a45ab9d4156ea4c487de0_1636567090?lk3s=c6b69ba0&nonce=825&refresh_token=e82f47cb8302c591000b4b2be25f1623&x-expires=1725264000&x-signature=k%2BHBwTD0U5Cwj0jxmtHMMHpX9IA%3D&shp=c6b69ba0&shcp=-",
                    "create_time": "1636567089",
                    "item_id": "7029002121664105733",
                    "is_relevant": False
                },
                {
                    "comment": "172",
                    "heart": "24656",
                    "hide": False,
                    "video_url": "https://v77.tiktokcdn.com/b23af523725fa9d25e1ca765716df912/66cc8bdf/video/tos/maliva/tos-maliva-ve-0068c799-us/oYf3npJSOBDiLlKIQE4izEAHHrfg6lW9BER6iY/?a=2043&bti=NjQ7OGYwLzA6&ch=0&cr=0&dr=0&er=0&lr=default&cd=0%7C0%7C0%7C0&cv=1&br=2988&bt=1494&cs=0&ds=6&ft=.NpOcInz7ThdTJOrXq8Zmo&mime_type=video_mp4&qs=0&rc=aGU8MzVoNGc4MzU3OjNmN0BpMzppeW05cjc8bjMzZzczNEAxM2BeYTU1XzExYy4zMl4yYSMyZDZpMmRzc3FgLS1kMS9zcw%3D%3D&vvpl=1&l=2024082608055808A052E0019428355A5A&btag=e00088000&cc=13",
                    "views": "249429",
                    "title": "🙈🙈🙈",
                    "share": "50",
                    "cover_url": "https://p19-sign.tiktokcdn-us.com/obj/tos-useast5-p-0068-tx/79782e5fe8bd41d5ad1a333fe045198d_1698340758?lk3s=c6b69ba0&nonce=68032&refresh_token=66771147fb9033b5280c6a76a30753de&x-expires=1725264000&x-signature=DOebHRvH7B9EBzZe2TL7o%2F8njzQ%3D&shp=c6b69ba0&shcp=-",
                    "create_time": "1698340757",
                    "is_bc_video": True,
                    "item_id": "7294317975883009323",
                    "is_relevant": False
                }
            ],
            "is_favorite": False
        },
        "base_info": {
            "status": 1,
            "banned_in_tt": False,
            "uid": "7026453230193280006",
            "tags": [
                "searchFilter_search_filter_danceCategory",
                "searchFilter_search_filter_lipSyncingCategory"
            ],
            "nick_name": "Leduar Lopez",
            "feature_items": [],
            "data_center": 2,
            "brief": "Síguenos en Instagram ⬆️\nContenido diario en Facebook 👇",
            "tt_status_error": False,
            "price": {
                "currency": "USD",
                "aio_price": "0",
                "starting_rate": "150",
                "aio_currency": "USD"
            },
            "avatar_url": "https://p16-sign-va.tiktokcdn.com/tos-maliva-avt-0068/0b59fbec1e222d03555ff11d6d4504a3~c5_300x300.jpeg?lk3s=a5d48078&nonce=7123&refresh_token=6391949a69f1dc6be2b8596e839ba575&x-expires=1724832000&x-signature=7llRV8JhiaogewYuKuQGn8QwZY0%3D&shp=a5d48078&shcp=c6b69ba0",
            "avatar_uri": "tos-useast5-avt-0068-tx/0b59fbec1e222d03555ff11d6d4504a3",
            "performance": {
                "median_views": 282247,
                "fans_cnt": "2049235",
                "avg_views": 367163,
                "engagement_rate": 0.0889199748635292
            },
            "region": {
                "register_country": "US",
                "register_city": "NULL",
                "active_country": "US",
                "recent_regions": [],
                "system_region": "US"
            },
            "handle_name": "leduarlopez",
            "id": "7027278960408920069"
        },
        "settings": {
            "receive_invitation": True
        }
    }
]


def insert_data_creator_marketplace(data):
    if len(data) == 0:
        return
    get_table_index(len(data))
    lock = redisLock.acquire_lock(RedisKeyConstants.lock_insert_data)
    if lock:
        try:
            for user in data:
                handle = user["base_info"]
                try:
                    if redis_client.get(RedisKeyConstants.redis_user_info_key + handle["handle_name"]) is not None:
                        raise Exception("储存数据中：" + handle["handle_name"] + "已存在，不写入")
                    insert_creator_marketplacce(handle)
                    redis_client.set(redis_user_info_key + handle["handle_name"], "")
                except Exception as ex:
                    logging.logger.error(handle["handle_name"] + "出错!")
                    logging.logger.error(ex)
        finally:
            redisLock.release_lock(RedisKeyConstants.lock_insert_data, lock)


insert_data_creator_marketplace(data_list)
