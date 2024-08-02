# # coding:utf-8
#
# import requests
# from lxml import etree
# import json
# import time
# import re
# import redis
# from concurrent.futures import ThreadPoolExecutor
# import log
# import excel
# import argparse
# from config import RedisKeyConstants as RedisKeyConstants
# from config import Config
#
# # 时间格式化
# timeArray = time.localtime(time.time())
# otherStyleTime = time.strftime("%Y%m%d", timeArray)
# numStyleTime = time.strftime("%H%M%S", timeArray)
# time_default_range = str(otherStyleTime)
#
# parser = argparse.ArgumentParser(description='argparse into.')
# parser.add_argument('--page', '-p', type=str, default="50", required=True, help="请输入爬取的数量(50倍数抓取)")
# parser.add_argument('--categories', '-cate', type=str, default="", required=False, help="请输入爬取类型")
# parser.add_argument('--currency', '-cur', type=str, default="", required=False, help="输入地区")
# parser.add_argument('--region', '-re', type=str, default="", required=False, help="输入地区")
# parser.add_argument('--time-type', '-tt', type=str, default="daily", required=False, help="爬取类型daily:日榜 weekly:周榜 "
#                                                                                           "monthly:月榜")
# parser.add_argument('--time-range', '-tr', type=str, default=time_default_range, required=False, help="爬取类型daily:日榜 "
#                                                                                                       "weekly:周榜 "
#                                                                                                       "monthly:月榜")
# args = parser.parse_args()
# # 线程池初始化
# pool = ThreadPoolExecutor(max_workers=8)
# thread_num = 2
#
# # redis初始化
# redis_client = redis.Redis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, db=Config.REDIS_DB)
# redis_key_error_num = RedisKeyConstants.redis_key_error_num
# redis_key_response_num = RedisKeyConstants.redis_key_response_num
# redis_key_tik_tok_request_error_num = RedisKeyConstants.redis_key_tik_tok_request_error_num
# redis_key_tik_tok_request_wait_num = RedisKeyConstants.redis_key_tik_tok_request_wait_num
# redis_client.set(redis_key_error_num, 0)
# redis_client.set(redis_key_response_num, 0)
# redis_client.set(redis_key_tik_tok_request_error_num, 0)
# redis_client.set(redis_key_tik_tok_request_wait_num, 0)
#
# # log初始化
# logging = log.Logger("TikTok用户画像-" + str(otherStyleTime) + '.log', level='INFO')
#
#
# # 从echotik获取用户列表
# def get_echotik_users_list(start, page):
#     time_type = args.time_type  # daily:日榜 weekly:周榜 monthly:月榜
#     time_range = args.time_range  # 数据批次 20240716:日榜 20240708-20240714:周榜 20240601-20240630:月榜
#     product_categories = ""
#     influencer_categories = args.categories  # 达人分类 空：全部  Public+Figure：公众人物  Entertainment：娱乐  Beauty：颜值
#     # Personal+Blog：个人博客  Art：艺术  Music%2FDance：音乐/舞蹈  Fashion：时尚  Media：媒体  Sports：运动健身  Pets：宠物  Education：教育
#     # Baby：母婴  Food：美食
#     currency = args.currency  # USD美国 VND越南 THB泰国 MYR马来西亚 PHP菲律宾
#     region = args.region  # US美国 VN越南 TH泰国 MY马来西亚 PH菲律宾
#     url = ("https://echotik.live/api/v1/data/influencers?"
#            + "time_type=" + time_type
#            + "&time_range=" + time_range
#            + "&page=" + str(start)
#            + "&product_categories=" + product_categories
#            + "&influencer_categories=" + influencer_categories
#            + "&per_page=" + str(page))
#     headers = {
#         'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_0) AppleWebKit/537.36 (KHTML, like Gecko) '
#                       'Chrome/71.0.3578.98 Safari/537.36',
#         'authorization': 'Bearer 282540|YAx0kwuPpb2TMmLsXlKDSlYY3pOyIwQyWQfXAGmX',
#         'x-currency': currency,
#         'x-region': region,
#         'x-lang': 'zh-CN',
#     }
#     logging.logger.info("请求url：" + url)
#     try:
#         response_echotik_users = requests.get(url=url, headers=headers)
#     except Exception as ex:
#         logging.logger.error(ex)
#         logging.logger.error("\033[31mEchotik官网获取数据失败，请检查网络!'\033[0m")
#         # 失败计数，超过10次失败结束
#         redis_client.incr(redis_key_error_num, 1)
#         return []
#     redis_client.get(redis_key_error_num).decode()
#     res_data = json.loads(response_echotik_users.text)
#     data_list = res_data.get("data")
#     # logging.logger.info(data_list)
#     users_list = []  # 达人id
#     for data in data_list:
#         users_list.append(
#             [data.get("unique_id"), data.get("category"), data.get("category_product"), data.get("follower_30d_count"),
#              data.get("total_product_cnt")])
#     logging.logger.debug("爬取Echotik达人列表,本次数据" + str(len(users_list)) + "条...\n")
#     print("爬取Echotik达人列表,本次数据" + str(len(users_list)) + "条...\n")
#     if len(users_list) == 0:
#         # 0条数据超过10次，代表没有数据
#         redis_client.incr(redis_key_response_num, 1)
#     else:
#         redis_client.get(redis_key_response_num).decode()
#     return users_list
#
#
# # 设置用户属性
# def set_user_info(user_data, user_state, echo_tik_user_info):
#     user_info_array = ['0', '0', '0', '0', '0', '0', '0', '0']
#     if user_data is None:
#         return user_info_array
#     else:
#         user_email = re.search(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',
#                                user_data.get('signature'), 0)
#         if user_email is not None:
#             user_email = user_email.group()
#         else:
#             user_email = 'TK主页无邮箱信息'
#         try:
#             user_info_array = [user_data.get('id'), user_data.get('uniqueId'),
#                                user_data.get('nickname'), user_email, echo_tik_user_info[1], echo_tik_user_info[2],
#                                echo_tik_user_info[3], echo_tik_user_info[4]]
#             if user_state is not None:
#                 # '粉丝数量', '关注数量', '点赞数', '发布视频数量'
#                 user_info_array.append(user_state.get('followerCount'))
#                 user_info_array.append(user_state.get('followingCount'))
#                 user_info_array.append(user_state.get('heart'))
#                 user_info_array.append(user_state.get('videoCount'))
#             else:
#                 user_info_array.append('0')
#                 user_info_array.append('0')
#                 user_info_array.append('0')
#                 user_info_array.append('0')
#         except:
#             # 当前账号数据权限不够
#             return user_info_array
#         return user_info_array
#
#
# # 爬取tiktok主页
# def get_tiktok_user_data(user_unique_id_list):
#     warit_excel_data = []
#     # logging.logger.info(user_unique_id_list)
#     for uniq_id in user_unique_id_list:
#         if int(redis_client.get(redis_key_tik_tok_request_wait_num)) > 40:
#             time.sleep(10)
#             redis_client.set(redis_key_tik_tok_request_wait_num, 0)
#             logging.logger.info("反爬措施，停10秒......")
#         url = 'https://www.tiktok.com/@' + str(uniq_id[0]) + '?lang=en'
#         # 请求头必须添加
#         headers = {
#             'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_0) AppleWebKit/537.36 (KHTML, like Gecko) '
#                           'Chrome/71.0.3578.98 Safari/537.36',
#         }
#         try:
#             response = requests.get(url=url, headers=headers)
#         except Exception as ex:
#             logging.logger.error(ex)
#             logging.logger.error("\033[31m用户：" + uniq_id[0] + "TK官网无法访问，请检查网络!'\033[0m")
#             continue
#         # 获取页面原始编码格式
#         page_text = response.text
#         tree = etree.HTML(page_text)
#         li_list = tree.xpath('//*[@id="__UNIVERSAL_DATA_FOR_REHYDRATION__"]/text()')
#         try:
#             response_data = json.loads(li_list[0])
#             user_detail = response_data.get('__DEFAULT_SCOPE__').get('webapp.user-detail')
#             print("获取TK用户" + str(uniq_id[0]) + "主页数据\n")
#             user_info = user_detail.get('userInfo')  # 用户基本信息 签名(邮箱) uniqueId 头像
#             if user_info is None:
#                 continue
#             user_data = user_info.get("user")
#             user_state = user_info.get('stats')  # 用户粉丝 点赞数  朋友数
#             warit_excel_data.append(set_user_info(user_data, user_state, uniq_id))
#         except Exception as ex:
#             redis_client.incr(redis_key_tik_tok_request_error_num, 1)
#             if int(redis_client.get(redis_key_tik_tok_request_error_num)) >= 20:
#                 logging.logger.error('TikTok官网失败超过次数，请检查网络!')
#                 break
#             logging.logger.error(ex)
#             continue
#         redis_client.set(redis_key_tik_tok_request_error_num, 0)
#         redis_client.incr(redis_key_tik_tok_request_wait_num, 1)
#     return warit_excel_data
#
#
# # 把总数据量拆分成50每页的数据
# def paginate(total_pages, pages_per_range):
#     ranges = []
#     for i in range(1, int(total_pages) // pages_per_range + 1):
#         # 计算当前范围的起始和结束页码
#         start_page = i
#         ranges.append((start_page, 50))
#     if len(ranges) * 50 < int(total_pages):
#         ranges.append([str(len(ranges) + 1), '50'])
#     return ranges
#
#
# # 开始爬取echotik网站
# def start_collect_echotik_user_id(page):
#     ranges = paginate(page, 50)
#     ls_data = []
#     for page_data in ranges:
#         echotik_user_data = get_echotik_users_list(page_data[0], page_data[1])
#
#         while len(echotik_user_data) == 0:
#             echotik_user_data = get_echotik_users_list(page_data[0], page_data[1])
#             if int(redis_client.get(redis_key_response_num)) >= 10:
#                 logging.logger.info("\033[31m EchoTik网站用户列表已全部爬取完成'\033[0m")
#                 break
#             if int(redis_client.get(redis_key_error_num)) >= 10:
#                 logging.logger.error("\033[31m EchoTik网站连接失败，请检查网络'\033[0m")
#                 break
#         if int(redis_client.get(redis_key_response_num)) >= 10:
#             logging.logger.info("\033[31m EchoTik网站用户列表已全部爬取完成'\033[0m")
#             break
#         ls_data.extend(echotik_user_data)
#
#     unique_users_list = list(set([tuple(t) for t in ls_data]))
#     same_user_num = len(ls_data) - len(unique_users_list)
#     logging.logger.info(
#         "获取用户列表完成，总共获得" + str(len(ls_data)) + "条数据,其中重复:" + str(same_user_num) + "条，去重共" + str(
#             len(unique_users_list)) + "条.\n")
#     return unique_users_list
#
#
# # 分割用户id列表给多线程
# def paginate_user_id_list(total, N):
#     if N <= 0:
#         raise ValueError("N必须大于0")
#     pages_per_range = total // N
#     remainder = total % N
#     ranges = []
#     start = 1
#     for i in range(N):
#         if i == N - 1:
#             end = start + pages_per_range + remainder - 1
#         else:
#             end = start + pages_per_range - 1
#         ranges.append((start - 1, end - 1))
#         start = end + 1
#     return ranges
#
#
# if __name__ == "__main__":
#     page = args.page
#     # 开始计时
#     t = time.time()
#     print(page)
#     # 处理数据爬虫
#     aa = redis_client.get("test-unused-EchoTik-user")
#     if aa is not None:
#         user_list = json.loads(aa)
#     else:
#         user_list = start_collect_echotik_user_id(page)
#         redis_client.set("test-unused-EchoTik-user", json.dumps(user_list))
#     ranges = paginate_user_id_list(len(user_list), 2)
#
#     result_data = []
#     # 固定8个线程
#     thread1 = pool.submit(get_tiktok_user_data, user_list)
#     result_data.extend(thread1.result())
#     pool.shutdown()
#     if len(result_data) == 0:
#         logging.logger.error("爬取数据为空！不存储Excel")
#     else:
#         excel.save_data_excel(result_data,
#                               "TikTok用户画像-" + str(otherStyleTime) + "-" + str(numStyleTime) + "-" + str(len(
#                                   result_data)) + "条-(" + args.currency + ")")
#
#     logging.logger.info("爬取数据完成.")
#     logging.logger.info(f'耗时:{time.time() - t:.4f}s')
