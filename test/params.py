import log
import json
import redis
import sys

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
redis_pipe = redis_client.pipeline()

redis_user_info_key = RedisKeyConstants.redis_user_info_key
table_name_add = ""
user_info = {'signature': '', 'id': '6792648514788377605', 'unique_id': 'imfrank2cool',
             'nickname': 'Stay motivated Frank',
             'avatar_larger': 'https://p19-pu-sign-useast8.tiktokcdn-us.com/tos-useast8-avt-0068-tx2/f5732a2537414981fc7bdaa031c6a30f~c5_1080x1080.jpeg?lk3s=a5d48078&nonce=3284&refresh_token=951ce66d58e78a369ae28aa7035df2a4&x-expires=1724313600&x-signature=IjSn0MmL3UFaG%2F3Cbz%2FZVH5siJI%3D&shp=a5d48078&shcp=81f88b70',
             'avatar_medium': 'https://p16-pu-sign-useast8.tiktokcdn-us.com/tos-useast8-avt-0068-tx2/f5732a2537414981fc7bdaa031c6a30f~c5_720x720.jpeg?lk3s=a5d48078&nonce=19667&refresh_token=522c2a48fc7cc16df7b5d7bfcbb716de&x-expires=1724313600&x-signature=tkFaZcOC1FJGxanTy2Um0pYKby8%3D&shp=a5d48078&shcp=81f88b70',
             'avatar_thumb': 'https://p16-pu-sign-useast8.tiktokcdn-us.com/tos-useast8-avt-0068-tx2/f5732a2537414981fc7bdaa031c6a30f~c5_100x100.jpeg?lk3s=a5d48078&nonce=84463&refresh_token=26dec7f5c4eb627747501c59843c70d0&x-expires=1724313600&x-signature=DLexGW1iXq8tGZrVMuKuuM%2BSDJk%3D&shp=a5d48078&shcp=81f88b70',
             'region': 'US', 'sec_uid': 'MS4wLjABAAAABeQ9lp4B5alaLblFhhaP7ftVtjV4oQTQoQAJlD79oe93DhVIhKT1UOMj78pBFgFS',
             'bio_link': str({'link': 'https://linktr.ee/imfrank2cool', 'risk': 0})}
user_info_insert_sql = (
        "INSERT INTO `TIKTOK_USER_INFO"  + "`(id,unique_id,nickname,avatar_larger,avatar_medium,avatar_thumb,"
                                                           "signature,region,sec_uid,bio_link) VALUES(%(id)s, %(unique_id)s, %(nickname)s, %(avatar_larger)s, "
                                                           "%(avatar_medium)s,%(avatar_thumb)s,%(signature)s,%(region)s, %(sec_uid)s, %(bio_link)s)")

mysql = Mysql()
try:
        mysql.insertOne(user_info_insert_sql, user_info)
except Exception as ex:
    mysql.dispose(isEnd=0)
    logging.logger.error(ex)
    logging.logger.error(user_info)
    raise Exception(ex)