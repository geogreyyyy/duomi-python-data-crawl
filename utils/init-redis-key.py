import redis
from MySqlCon import Mysql
import sys
import log
import json
import numpy as np

sys.path.append("..")
from config import RedisKeyConstants as RedisKeyConstants
from config import Config

redis_client = redis.Redis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, db=Config.REDIS_DB)
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
    uniqueId = str(item.get("unique_id"), encoding="utf-8")
    pipe.set(redis_user_info_key + uniqueId, json.dumps(item,cls=MyEncoder,indent=4))
pipe.execute()
