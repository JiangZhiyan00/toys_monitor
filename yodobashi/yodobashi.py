import os

import requests
import yagmail
from bs4 import BeautifulSoup

# 配置
# 有货示例
# https://www.yodobashi.com/product/100000001008874972/
# 无货示例
# https://www.yodobashi.com/product/100000001008874972/
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0"
}
URL = "https://www.yodobashi.com/product/100000001008874972/"  # 替换为你的目标 URL
BUTTON_TEXT = "ショッピングカートに入れる"  # 按钮上的文字
SMTP_USER = "your_email@example.com"  # 替换为你的邮箱
SMTP_PASSWORD = "your_password"  # 替换为你的邮箱密码
TO_EMAIL = "receiver@example.com"  # 接收通知的邮箱


def get_proxies():
    """检查环境变量并返回代理配置"""
    http_proxy = os.getenv("HTTP_PROXY")
    https_proxy = os.getenv("HTTPS_PROXY")
    return {
        "http": "http://127.0.0.1:7900" if http_proxy is None else http_proxy,
        "https": "http://127.0.0.1:7900" if https_proxy is None else https_proxy,
    }


def check_button():
    try:
        # 获取代理配置
        proxies = get_proxies()
        print(f"检测到代理配置：{proxies}")

        # 发送请求
        response = requests.get(URL, headers=HEADERS, proxies=proxies, timeout=30)
        response.raise_for_status()  # 如果响应错误，抛出异常

        # 解析 HTML
        soup = BeautifulSoup(response.text, "html.parser")

        # 查找按钮
        button = soup.find("button", string=BUTTON_TEXT)
        if button:
            print(f"按钮 '{BUTTON_TEXT}' 存在")
            # send_email()
        else:
            print(f"按钮 '{BUTTON_TEXT}' 不存在")
    except Exception as e:
        print(f"出现错误: {e}")


def send_email():
    try:
        # 配置发送邮件
        yag = yagmail.SMTP(SMTP_USER, SMTP_PASSWORD)

        # 邮件内容
        subject = f"按钮 '{BUTTON_TEXT}' 出现"
        body = f"按钮 '{BUTTON_TEXT}' 已在页面 {URL} 上出现，请及时处理。"

        # 发送邮件
        yag.send(to=TO_EMAIL, subject=subject, contents=body)
        print("邮件发送成功")
    except Exception as e:
        print(f"邮件发送失败: {e}")


if __name__ == "__main__":
    check_button()
