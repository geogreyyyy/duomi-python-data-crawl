# 使用selenium库来模拟人的行为
import time
import json

from selenium import webdriver

option = webdriver.ChromeOptions()
option.add_argument('--disable-gpu')  # 禁止gpu加速
option.add_argument("no-sandbox")  # 取消沙盒模式
option.add_argument("disable-blink-features=AutomationControlled")  # 禁用启用Blink运行时的功能
option.add_experimental_option('excludeSwitches', ['enable-automation'])  # 开发者模式
driver = webdriver.Chrome(options=option)

# 移除 `window.navigator.webdriver`. scrapy 默认为True
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        })
        """
})

def get_email(url):
    # 开始访问youtube
    driver.get(url)
    driver.find_element('xpath', 'more-icon').click()
    time.sleep(5)
    driver.find_element('xpath',
                        '//*[@id="page-header"]/yt-page-header-renderer/yt-page-header-view-model/'
                        'div/div[1]/div/yt-description-preview-view-model/truncated-text/button/span/span').click()
    driver.find_element('xpath',
                        '//*[@id="view-email-button-container"]/yt-button-view-model/button-view-model/button').click()
    time.sleep(5)
    iframe = driver.find_element('xpath', '//*[@id="recaptcha"]/div/div/iframe')
    # 切换到iframe上
    driver.switch_to.frame(iframe)
    time.sleep(5)
    driver.find_element('xpath', '//*[@id="recaptcha-anchor"]/div[1]').click()
    time.sleep(5)
    # 切回主页面
    driver.switch_to.default_content()
    driver.find_element('xpath', '//*[@id="submit-btn"]/span').click()
    time.sleep(5)
    email = driver.find_element('xpath', '//*[@id="email"]').text
    print(email)
    return email

try:
    url = 'https://www.youtube.com/channel/UCVXCo0W9pk2dDkEBNLhTt7A'
    driver.get(url)
    driver.find_element('xpath', '//*[@id="buttons"]/ytd-button-renderer/yt-button-shape/a/yt-touch-feedback-shape/div'
                                 '/div[2]').click()
    driver.find_element('xpath', '//*[@id="identifierId"]').send_keys('cick-y@foxmail.com')
    driver.find_element('xpath', '//*[@id="identifierNext"]/div/button').click()
    time.sleep(10)
    driver.find_element('xpath', '//*[@id="password"]/div[1]/div/div[1]/input').send_keys('13065162873yjz')
    driver.find_element('xpath', '//*[@id="passwordNext"]/div/button').click()
    time.sleep(5)
    email = get_email(url)
    item = {'url': url, 'email': email}
    print(item)
except Exception as ex:
    print("出现如下异常%s"%ex)
    driver.quit()

