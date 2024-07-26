import xlwt
import time
import os


# excel内样式
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


# excel内样式
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


def mkdir(path):
    folder = os.path.exists(os.path.join(os.getcwd(), path))
    if not folder:  # 判断是否存在文件夹如果不存在则创建为文件夹
        os.makedirs(path)  # makedirs 创建文件时如果路径不存在会创建这个路径


# 保存excel文档
def save_data_excel(warit_excel_data, filename):
    wb = xlwt.Workbook()
    # 创建工作表对象（Worksheet）
    sheet_save_name = time.strftime("%Y-%m-%d", time.localtime())
    sheet = wb.add_sheet(sheet_save_name)
    header_style = setting_style_xls_header()
    body_style = setting_style_xls_body()
    # 添加表头数据
    # 0:id 1:uniqueId 2:nickname  3:signature
    titles = (
        'User Id', 'Unique Id', '达人名称', 'email', '达人标签', '带货标签', '30天涨粉量', '带货商品数', '粉丝数量', '关注数量',
        '获赞数',
        '发布视频数量')
    for index, title in enumerate(titles):
        sheet.write(0, index, title, header_style)
    for row in range(len(warit_excel_data)):
        for col in range(len(titles)):
            # sheet.write(row + 1, col, warit_excel_data[row][col], body_style)
            sheet.col(col).width = 25 * 300
    # 保存Excel工作簿
    mkdir("excel")
    wb.save("./excel/" + filename + '.xls')
