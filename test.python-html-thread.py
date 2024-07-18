import requests
import xlwt
from lxml import etree
import json
import time
import re
import redis
from concurrent.futures import ThreadPoolExecutor
import log
import excel

# 线程池初始化
pool = ThreadPoolExecutor(max_workers=8)
thread_num = 8

# redis初始化
redis_client = redis.Redis(host="localhost", port=6379, db=0)
redis_key_name = "python_data_crawl"
redis_key_error_num = redis_key_name + "_error_num"
redis_key_response_num = redis_key_name + "_response_num"
redis_key_tik_tok_request_error_num = redis_key_name + "_tik_tok_request_error_num"
redis_client.set(redis_key_error_num, 0)
redis_client.set(redis_key_response_num, 0)
redis_client.set(redis_key_tik_tok_request_error_num, 0)

# log初始化
logging = log.Logger('all.log', level='INFO')
# 时间格式化
timeArray = time.localtime(time.time())
otherStyleTime = time.strftime("%Y%m%d", timeArray)
numStyleTime = time.strftime("%H%M%S", timeArray)

# 从echotik获取用户列表
def get_echotik_users_list(start, page):
    time_type = 'daily'  # daily:日榜 weekly:周榜 monthly:月榜
    time_range = str(otherStyleTime)  # 数据批次 20240716:日榜 20240708-20240714:周榜 20240601-20240630:月榜
    product_categories = ""
    influencer_role = '2'  # 爬取板块
    currency = 'USD'  # USD美国 VND越南 THB泰国 MYR马来西亚 PHP菲律宾
    region = 'US'  # US美国 VN越南 TH泰国 MY马来西亚 PH菲律宾
    url = ("https://echotik.live/api/v1/data/influencers?"
           + "time_type=" + time_type
           + "&time_range=" + time_range
           + "&page=" + str(start)
           + "&influencer_role="+influencer_role
           + "&influencer_categories="
           + "&product_categories=" + product_categories
           + "&per_page=" + str(page))
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_0) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/71.0.3578.98 Safari/537.36',
        'authorization': 'Bearer 267006|bvJXZYqIlwz9YRB9lyjY7BXchtXetfU2YJUKWmFR',
        'x-currency': currency,
        'x-region': region,
    }
    # logging.logger.info("请求url："+url)
    global response_echotik_users
    try:
        response_echotik_users = requests.get(url=url, headers=headers)
    except Exception as ex:
        logging.logger.error(ex)
        logging.logger.error("\033[31mEchotik官网获取数据失败，请检查网络!'\033[0m")
        # 失败计数，超过10次失败结束
        redis_client.incr(redis_key_error_num, 1)
        return []
    redis_client.get(redis_key_error_num).decode()
    res_data = json.loads(response_echotik_users.text)
    data_list = res_data.get("data")
    # logging.logger.info(data_list)
    users_unique_id_list = []
    for data in data_list:
        users_unique_id_list.append(data.get("unique_id"))
    logging.logger.debug("爬取Echotik达人列表,本次数据" + str(len(users_unique_id_list)) + "条...\n")
    print("爬取Echotik达人列表,本次数据" + str(len(users_unique_id_list)) + "条...\n")
    if len(users_unique_id_list) == 0:
        # 0条数据超过10次，代表没有数据
        redis_client.incr(redis_key_response_num, 1)
    else:
        redis_client.get(redis_key_response_num).decode()
    return users_unique_id_list


# 设置用户属性
def set_user_info(user_data, user_state):
    user_info_array = ['0', '0', '0', '0', '0', '0', '0', '0']
    if user_data is None:
        return user_info_array
    else:
        user_email = re.search(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',
                               user_data.get('signature'), 0)
        if user_email is not None:
            user_email = user_email.group()
        else:
            user_email = 'TK主页无邮箱信息'
        try:
            user_info_array = [user_data.get('id'), user_data.get('uniqueId'),
                               user_data.get('nickname'), user_email]
            if user_state is not None:
                # '粉丝数量', '关注数量', '点赞数', '发布视频数量'
                user_info_array.append(user_state.get('followerCount'))
                user_info_array.append(user_state.get('followingCount'))
                user_info_array.append(user_state.get('heart'))
                user_info_array.append(user_state.get('videoCount'))
            else:
                user_info_array.append('0')
                user_info_array.append('0')
                user_info_array.append('0')
                user_info_array.append('0')
        except:
            #当前账号数据权限不够
            return user_info_array
        return user_info_array


# 爬取tiktok主页
def get_tiktok_user_data(user_unique_id_list):
    warit_excel_data = []
    # logging.logger.info(user_unique_id_list)
    for uniq_id in user_unique_id_list:
        url = 'https://www.tiktok.com/@' + str(uniq_id) + '?lang=en'
        # 请求头必须添加
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_0) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/71.0.3578.98 Safari/537.36',
        }
        global response
        try:
            response = requests.get(url=url, headers=headers)
        except Exception as ex:
            logging.logger.error(ex)
            logging.logger.error("\033[31m用户：" + uniq_id + "TK官网无法访问，请检查网络!'\033[0m")
            continue
        # 获取页面原始编码格式
        page_text = response.text
        tree = etree.HTML(page_text)
        li_list = tree.xpath('//*[@id="__UNIVERSAL_DATA_FOR_REHYDRATION__"]/text()')
        try:
            response_data = json.loads(li_list[0])
            user_detail = response_data.get('__DEFAULT_SCOPE__').get('webapp.user-detail')
            logging.logger.debug("爬取Tiktok主页中...\n")
            print("爬取Tiktok主页中...\n")
            logging.logger.debug("获取TK用户" + str(uniq_id) + "主页数据\n")
            print("获取TK用户" + str(uniq_id) + "主页数据\n")
            user_info = user_detail.get('userInfo')  # 用户基本信息 签名(邮箱) uniqueId 头像
            if user_info is None:
                continue
            user_data = user_info.get("user")
            user_state = user_info.get('stats')  # 用户粉丝 点赞数  朋友数
            warit_excel_data.append(set_user_info(user_data, user_state))
        except Exception as ex:
            redis_client.incr(redis_key_tik_tok_request_error_num, 1)
            if int(redis_client.get(redis_key_tik_tok_request_error_num)) >= 20:
                logging.logger.error('TikTok官网失败超过次数，请检查网络!')
                break
            logging.logger.error(ex)
            continue
        redis_client.set(redis_key_tik_tok_request_error_num, 0)
    return warit_excel_data


# 把总数据量拆分成50每页的数据
def paginate(total_pages, pages_per_range):
    ranges = []
    for i in range(1, total_pages // pages_per_range + 1):
        # 计算当前范围的起始和结束页码
        start_page = i
        ranges.append((start_page, 50))
    if len(ranges) * 50 < total_pages:
        ranges.append([str(len(ranges) + 1), '50'])
    return ranges


# 开始爬取echotik网站
def start_collect_echotik_user_id(page):
    ranges = paginate(page, 50)
    user_list = []
    user_data_split = paginate_user_id_list(len(ranges), thread_num)
    for page_data in ranges:
        user_list.extend(get_echotik_users_list(page_data[0], page_data[1]))
        if int(redis_client.get(redis_key_response_num)) >= 10:
            logging.logger.info("\033[31m EchoTik网站用户列表已全部爬取完成'\033[0m")
            break
        if int(redis_client.get(redis_key_error_num)) >= 10:
            logging.logger.error("\033[31m EchoTik网站连接失败，请检查网络'\033[0m")
            break
    unique_user_list = list(set(user_list))
    same_user_num = len(user_list) - len(unique_user_list)
    logging.logger.info(
        "获取用户列表完成，总共获得" + str(len(user_list)) + "条数据,其中重复:" + str(same_user_num) + "条，去重共" + str(
            len(
                unique_user_list)) + "条.\n")
    return unique_user_list


# 分割用户id列表给多线程
def paginate_user_id_list(total, N):
    if N <= 0:
        raise ValueError("N必须大于0")
    pages_per_range = total // N
    remainder = total % N
    ranges = []
    start = 1
    for i in range(N):
        if i == N - 1:
            end = start + pages_per_range + remainder - 1
        else:
            end = start + pages_per_range - 1
        ranges.append((start - 1, end - 1))
        start = end + 1
    return ranges


if __name__ == "__main__":
    page = int(input("请输入爬取的数量(50倍数抓取):"))
    # 开始计时
    t = time.time()
    # 处理数据爬虫
    user_list = start_collect_echotik_user_id(page)

    ranges = paginate_user_id_list(len(user_list), thread_num)
    result_data = []
    # 固定8个线程
    thread1 = pool.submit(get_tiktok_user_data, user_list[ranges[0][0]:ranges[0][1]])
    thread2 = pool.submit(get_tiktok_user_data, user_list[ranges[1][0]:ranges[1][1]])
    thread3 = pool.submit(get_tiktok_user_data, user_list[ranges[2][0]:ranges[2][1]])
    thread4 = pool.submit(get_tiktok_user_data, user_list[ranges[3][0]:ranges[3][1]])
    thread5 = pool.submit(get_tiktok_user_data, user_list[ranges[4][0]:ranges[4][1]])
    thread6 = pool.submit(get_tiktok_user_data, user_list[ranges[5][0]:ranges[5][1]])
    thread7 = pool.submit(get_tiktok_user_data, user_list[ranges[6][0]:ranges[6][1]])
    thread8 = pool.submit(get_tiktok_user_data, user_list[ranges[7][0]:ranges[7][1]])

    result_data.extend(thread1.result())
    result_data.extend(thread2.result())
    result_data.extend(thread3.result())
    result_data.extend(thread4.result())
    result_data.extend(thread5.result())
    result_data.extend(thread6.result())
    result_data.extend(thread7.result())
    result_data.extend(thread8.result())
    pool.shutdown()
    if len(result_data) == 0:
        logging.logger.error("爬取数据为空！不存储Excel")
    else:
        excel.save_data_excel(result_data, "TikTok用户画像-" + str(otherStyleTime)+"-"+ str(numStyleTime) + "-" + str(len(
            result_data)) + "条")

    logging.logger.info("爬取数据完成.")
    logging.logger.info(f'耗时:{time.time() - t:.4f}s')
