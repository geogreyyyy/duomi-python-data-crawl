import time
import uuid
import redis
from concurrent.futures import ThreadPoolExecutor

import sys

sys.path.append("..")
from config import Config

redis_client = redis.Redis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, db=Config.REDIS_DB,
                           password=Config.REDIS_PASSWORD)


# 加锁的过程

def acquire_lock(lock_name, args=None, acquire_timeout=30, time_out=120):
    global redis_client
    identifier = str(uuid.uuid4())
    # Client attempts to acquire lock before this time
    end = time.time() + acquire_timeout
    lock_names = lock_name
    while time.time() < end:
        try:
            # Attempt to acquire the lock using setnx (set if not exists)
            if redis_client.setnx(lock_names, identifier):
                # If lock acquired, set expiration for automatic release
                redis_client.expire(lock_name, time_out)
                return identifier
            # If lock exists but has no expiration, set the expiration again
            elif redis_client.ttl(lock_name) == -1:
                redis_client.expire(lock_name, time_out)

        except Exception as e:
            print(f"Error: {str(e)}. Attempting to reconnect...")
            # Try reconnecting the Redis client
            try:
                redis_client = redis.StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, db=Config.REDIS_DB,
                                                 password=Config.REDIS_PASSWORD)
                print("Reconnected to Redis.")
            except Exception as reconnection_error:
                print(f"Reconnection failed: {str(reconnection_error)}")
                # Exit loop or continue based on the policy for reconnection
                time.sleep(1)  # Wait before retrying to connect

        time.sleep(0.001)  # Small delay before retrying

    return False


# 锁的释放
def release_lock(lock_name, identifire):
    lock_names = lock_name
    pipe = redis_client.pipeline(True)
    while True:
        try:
            # 通过watch命令监视某个键，当该键未被其他客户端修改值时，事务成功执行。当事务运行过程中，发现该值被其他客户端更新了值，任务失败
            pipe.watch(lock_names)
            # print(pipe.get((lock_names)))
            if pipe.get(lock_names).decode() == identifire:  # 检查客户端是否仍然持有该锁
                # multi命令用于开启一个事务，它总是返回ok
                # multi执行之后， 客户端可以继续向服务器发送任意多条命令， 这些命令不会立即被执行， 而是被放到一个队列中， 当 EXEC 命令被调用时， 所有队列中的命令才会被执行
                pipe.multi()
                # 删除键，释放锁
                pipe.delete(lock_names)
                # execute命令负责触发并执行事务中的所有命令
                pipe.execute()
                return True
            pipe.unwatch()
            break
        except Exception as ex:
            print(f"redisLock - release_lock:{ex}")
            time.sleep(10)
            # # 释放锁期间，有其他客户端改变了键值对，锁释放失败，进行循环
            pass
    return False


pool = ThreadPoolExecutor(max_workers=8)


# 模拟加锁解锁的过程
def exec_test(lockname, args):
    # while True:
    identifire = acquire_lock(lockname, args)
    print(f'identifire :{identifire}')
    # 如果获取到锁,则进行业务逻辑处理
    if identifire:
        # sleep 3s 模拟业务逻辑处理,处理完之后进行锁释放,让其他进程获取锁
        time.sleep(3)
        res = release_lock(lockname, identifire)
        print(f'释放状态: {res}')
        # break
    else:
        print('获取redis分布式锁失败,其他进程正在使用')
        # time.sleep(1)


if __name__ == '__main__':
    pool.submit(exec_test, "test", 1)
    pool.submit(exec_test, "test", 1)
    pool.shutdown()
