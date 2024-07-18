import requests
import json

url = "https://www.tiktok.com/api/post/item_list/?WebIdLastTime=1721030717&aid=1988&app_language=en&app_name=tiktok_web&browser_language=zh-CN&browser_name=Mozilla&browser_online=true&browser_platform=MacIntel&browser_version=5.0%20%28Macintosh%3B%20Intel%20Mac%20OS%20X%2010_15_7%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F126.0.0.0%20Safari%2F537.36&channel=tiktok_web&cookie_enabled=true&count=35&coverFormat=2&cursor=0&data_collection_enabled=false&device_id=7391770571065230866&device_platform=web_pc&focus_state=true&from_page=user&history_len=7&is_fullscreen=false&is_page_visible=true&language=en&needPinnedItemIds=true&odinId=7391770530205418514&os=mac&post_item_list_request_type=0&priority_region=&referer=&region=SG&screen_height=1080&screen_width=1920&secUid=MS4wLjABAAAAtRnx89ppqTm4pLPdZJHQj69UmgHPC4oeBY69Bu5JHiOOClD6yG6VPtuZY48x2ORj&tz_name=Asia%2FShanghai&user_is_login=false&webcast_language=en&msToken=5BvWUDVAWXtPjQKtT71oItbAGYnY6q2p5vjaQcEek62p5ar4JfOrX1vaIaj-DrCCIxI_zFGylOchj7DHmfitz_lOEQC0UOY0xzMcwouJKpAC0TPZi9IyYYXVZTbOPb3Ki9enOiCHA4ym7jMzohbrTs4=&X-Bogus=DFSzswVO1etANJoVtwDyXjLNKBYQ&_signature=_02B4Z6wo00001l6ssVgAAIDBDFORQ6VAbwJerLXAAPFOc2"

payload = {}
headers = {
    'priority': 'u=0, i',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Cookie': 'tt_csrf_token=fUpQpmBb-yDTwC3v7lJGeHS1TfdW6Mdp-TxY; ak_bmsc=49F8A1107C611B7955056674055D15F5~000000000000000000000000000000~YAAQpFA7F9RodZeQAQAAACZstRj+emKLgG1ecZcUSm9loXEDFXh8UpgFEuOIaqWu/WrF++89QivzmGaw4so02QH55HvtyQDpJyhgdt3lD+w2f6zgwWcImIcbB82gQkemEtzXdpuSdSpcwcWn2abZ7pYjcwsT0BlWlPiNJeB9Oj4Iof/kwBZM9BrMP5AiJL+/pjYUETwdJYPYGV1k+k2Tm+1EFNIj9imXN7MZo6gMUDSzFU1ZM8BOxg0YbWiD5BeMgYiQ4Q13Eic9vDlwclQQNQ/l0BPZXPfxsaXeNeW2Vl5uUjkkqAcNOPbAe901gWuW35nvklB70DO9HG7D4/wJCaxKumgbQnDNg5Pl/PpGoNZxRvw7fPsuFXk5bbBOvjKURB5KcP3T7UTR; tt_chain_token=hFXCcFiSUydWTTot3t8bCQ; tiktok_webapp_theme_auto_dark_ab=1; tiktok_webapp_theme_source=system; odin_tt=2dec33a398fb47bd3f1d510fab040ba2af5dcc324f25f6d60bc7993019fc880c9a58cf94599cc55e069502789361860cb39733f83d9e4ed123641b480a6a7830f180efe0f3d8babef4487c3d65847167; perf_feed_cache={%22expireTimestamp%22:1721203200000%2C%22itemIds%22:[%227385958060994350379%22%2C%227388870722917223685%22]}; tiktok_webapp_theme=dark; bm_sv=4834BE9DA464D36DD67BD5F280799096~YAAQrlA7F5HlZ5qQAQAAZFp7tRhWNsXogqeAz5X6xuCLxa6Mi4LOKHmG3vgNpqwgSIYcI1ktrxBDQQODqwPkF2MBzgeOC2/XHiKiS3VztJyFuV0zByTzJshEBd+5UeQUT2kq3ONzH22lWzhHMs1o83/gNRwQRMopmevGoSuc6AKK7Z2xSRQMrf3IYaWvmrKEBeX/Fdaj1ALcpNjYTyu4/mholn0pSX8mZhJImn/UWj0msgClYoooi55UJJ0Crn4G~1; ttwid=1%7CM1vdbeI2bDJCLBXJCwIa942uUzFqcSu63LVps_P6qW8%7C1721031680%7Cacaa889dcf5ce7a4e851609e0d473c56e97870b5705699623374b099dc07aa51; msToken=wIS9esFZM53K83bFs9nJB3SMc9SHwXxiEdR97wkEmuy1wSlJ24KBWyPDnIlREZTn5MrmTRF1AdwD7EQYo50KIBWvsZOIfg7UmBEHwndJZXZZPfgZI61p0wPAueGBouf73hw49znFNPZe2l4rot6A7uE'
}

response = requests.request("GET", url, headers=headers, data=payload)
# print(response.url)
# print(response.text)

response_data = json.loads(response.text)
author = response_data.get('itemList')[0].get('author')

print('uniqueId:' + author.get('uniqueId'))
print('------------------------------------------------------------------------------')
print('signature:' + author.get('signature'))
print('------------------------------------------------------------------------------')
print('id:' + author.get('id'))
print('------------------------------------------------------------------------------')
