import redis
import sys

sys.path.append("..")
from config import RedisKeyConstants as RedisKeyConstants
from config import Config

redis_client = redis.Redis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, db=Config.REDIS_DB,
                           password=Config.REDIS_PASSWORD)
result = redis_client.blpop(RedisKeyConstants.data_crawl_search_key)
print(str(result[1], encoding='utf-8'))
