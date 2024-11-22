import base64
import hashlib
import hmac
import socket
import time

import requests


def setFeiShuMsg(msg):
    url = "https://open.feishu.cn/open-apis/bot/v2/hook/a216788d-55b0-445f-a8cb-36e05a7c9045"
    time_int = int(time.time())
    # print(time_int)
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    # print(ip_address)
    body = {
        "timestamp": time_int,
        "sign": gen_sign(time_int, "d4hFPpR8XJ1TmmV0TWsjMh"),
        "msg_type": "text",
        "content": {
            "text": f"{msg}。\n报错主机ip地址：{ip_address}"
        }
    }
    headers = {
        "Content-Type ": "application/json"
    }
    requests.post(url, json=body, headers=headers, timeout=20)


def gen_sign(timestamp, secret):
    # 拼接timestamp和secret
    string_to_sign = '{}\n{}'.format(timestamp, secret)
    hmac_code = hmac.new(string_to_sign.encode("utf-8"), digestmod=hashlib.sha256).digest()
    # 对结果进行base64处理
    sign = base64.b64encode(hmac_code).decode('utf-8')
    return sign


if __name__ == '__main__':
    setFeiShuMsg("越南爬取失败")
