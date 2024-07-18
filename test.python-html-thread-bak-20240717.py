import requests
import xlwt
from lxml import etree
import json
import _thread
import time
import re
from concurrent.futures import ThreadPoolExecutor
import threading

pool = ThreadPoolExecutor(max_workers=8)

def setting_style_xls_body():
    body_style = xlwt.XFStyle()
    font = xlwt.Font()
    # 字体大小（20是基准单位，18表示18px）
    font.height = 14 * 18
    # 是否使用粗体
    font.bold = False
    # 是否使用斜体
    font.italic = False
    # 字体颜色
    font.colour_index = 0
    body_style.font = font
    align = xlwt.Alignment()
    # 垂直方向的对齐方式
    align.vert = xlwt.Alignment.VERT_CENTER
    # 水平方向的对齐方式
    align.horz = xlwt.Alignment.HORZ_CENTER
    body_style.alignment = align
    return body_style


def setting_style_xls_header():
    header_style = xlwt.XFStyle()
    pattern = xlwt.Pattern()
    pattern.pattern = xlwt.Pattern.SOLID_PATTERN
    # 0 - 黑色、1 - 白色、2 - 红色、3 - 绿色、4 - 蓝色、5 - 黄色、6 - 粉色、7 - 青色
    pattern.pattern_fore_colour = 4
    font = xlwt.Font()
    # 字体大小（20是基准单位，18表示18px）
    font.height = 15 * 18
    # 是否使用粗体
    font.bold = False
    # 是否使用斜体
    font.italic = False
    # 字体颜色
    font.colour_index = 1
    header_style.font = font
    header_style.pattern = pattern
    align = xlwt.Alignment()
    # 垂直方向的对齐方式
    align.vert = xlwt.Alignment.VERT_CENTER
    # 水平方向的对齐方式
    align.horz = xlwt.Alignment.HORZ_CENTER
    header_style.alignment = align
    return header_style


def get_echotik_users_list(start, page):
    url = ("https://echotik.live/api/v1/data/influencers/leaderboard/champion-sales?time_type=daily&time_range=20240715"
           "&page=" + str(start) + "&influencer_role=&influencer_categories=&product_categories=&per_page=" + str(page))
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_0) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/71.0.3578.98 Safari/537.36',
        'authorization': 'Bearer 267006|bvJXZYqIlwz9YRB9lyjY7BXchtXetfU2YJUKW'
    }
    global response_echotik_users
    try:
        response_echotik_users = requests.get(url=url, headers=headers)
    except:
        print("\033[31mEchotik官网获取数据失败，请检查网络!'\033[0m")
        return []
    # print(response_echotik_users.text)
    res_data = json.loads(response_echotik_users.text)
    # print(response.text)
    data_list = res_data.get("data")
    users_unique_id_list = []
    for data in data_list:
        users_unique_id_list.append(data.get("unique_id"))
    print("爬取Echotik达人列表,本次数据" + str(len(users_unique_id_list)) + "条...\n")
    return users_unique_id_list


def set_user_info(user_data, user_state):
    # print(user_data.get('user').get('signature'))
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


def get_tiktok_user_data(user_unique_id_list):
    warit_excel_data = []
    # print(user_unique_id_list)
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
        except:
            print("\033[31m用户：" + uniq_id + "TK官网无法访问，请检查网络!'\033[0m")
            continue
        #获取页面原始编码格式
        page_text = response.text
        tree = etree.HTML(page_text)
        li_list = tree.xpath('//*[@id="__UNIVERSAL_DATA_FOR_REHYDRATION__"]/text()')
        response_data = json.loads(li_list[0])
        user_detail = response_data.get('__DEFAULT_SCOPE__').get('webapp.user-detail')
        print("爬取Tiktok主页中...\n")
        print("获取TK用户" + str(uniq_id) + "主页数据\n")
        user_info = user_detail.get('userInfo')  # 用户基本信息 签名(邮箱) uniqueId 头像
        if user_info is None:
            continue
        user_data = user_info.get("user")
        user_state = user_info.get('stats')  # 用户粉丝 点赞数  朋友数
        warit_excel_data.append(set_user_info(user_data, user_state))
    return warit_excel_data


def paginate(total_pages, pages_per_range):
    ranges = []
    for i in range(1, total_pages // pages_per_range + 1):
        # 计算当前范围的起始和结束页码
        start_page = i
        ranges.append((start_page, 50))
    if len(ranges) * 50 < total_pages:
        ranges.append([str(len(ranges) + 1), '50'])
    return ranges


def start_collect_echotik_user_id(page):
    ranges = paginate(page, 50)
    user_list = []
    user_data_split = paginate_user_id_list(len(ranges), 8)
    print(user_data_split[0])
    print(user_data_split[1])
    print(user_data_split[2])
    print(user_data_split[3])
    for page_data in ranges:
        print(page_data)
        user_list.extend(get_echotik_users_list(page_data[0], page_data[1]))
    print("获取用户列表完成，总共获得" + str(len(user_list)) + "条数据\n")
    return user_list


def save_data_excel(warit_excel_data, filename):
    wb = xlwt.Workbook()
    # 创建工作表对象（Worksheet）
    sheet_save_name = time.strftime("%Y-%m-%d", time.localtime())
    sheet = wb.add_sheet(sheet_save_name)
    header_style = setting_style_xls_header()
    body_style = setting_style_xls_body()
    # 添加表头数据
    # 0:id 1:uniqueId 2:nickname  3:signature
    titles = ('User Id', 'Unique Id', '达人名称', 'email', '粉丝数量', '关注数量', '获赞数', '发布视频数量')
    for index, title in enumerate(titles):
        sheet.write(0, index, title, header_style)
    for row in range(len(warit_excel_data)):
        for col in range(len(titles)):
            sheet.write(row + 1, col, warit_excel_data[row][col], body_style)
            sheet.col(col).width = 25 * 300
    # 保存Excel工作簿
    now = int(time.time())
    wb.save(filename + '.xls')


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

    thread_num = 8
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
    save_data_excel(result_data, "TikTok用户画像-" + str(int(time.time())) + "-" + str(len(result_data)) + "条")
    # for range_ in ranges:
    #     thread_request_tiktok_user_data(user_list[range_[0]:range_[1] + 1],
    #                                     '-(' + str(range_[0] + 1) + '-' + str(range_[1] + 1) + ')')

    print("爬取数据完成.")
    print(f'耗时:{time.time() - t:.4f}s')
