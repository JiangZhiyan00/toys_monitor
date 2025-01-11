import os
import json
import time
from dataclasses import dataclass
from typing import List

import requests
import yagmail
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor


@dataclass
class WebsiteConfig:
    website: str
    name: str
    pic: str
    url: str
    elementType: str
    monitorText: str
    noticeSeconds: int
    timeout: int
    emails: List[str]


def load_config(file_path: str) -> List[WebsiteConfig]:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [WebsiteConfig(**item) for item in data]


PROXY_URL_PREFIX = "https://proxy.jzy88.top/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0"
}


def get_cache_key(email, url):
    return f"{email}|{url}"


def load_last_notice_time(cache_file="notice_cache.json"):
    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            return json.load(f)
    return {}


def save_last_notice_time(emails, url, timestamp, cache_file="notice_cache.json"):
    cache = load_last_notice_time(cache_file)
    for email in emails:
        key = get_cache_key(email, url)
        cache[key] = timestamp
    with open(cache_file, "w") as f:
        json.dump(cache, f)


def should_notice(email, url, notice_seconds):
    cache = load_last_notice_time()
    key = get_cache_key(email, url)
    last_time = cache.get(key, 0)
    return time.time() - last_time >= notice_seconds


def check_and_notice(config: WebsiteConfig):
    try:
        # 发送请求
        response = requests.get(
            PROXY_URL_PREFIX + config.url, headers=HEADERS, timeout=config.timeout
        )
        response.raise_for_status()

        # 解析 HTML
        soup = BeautifulSoup(response.text, "html.parser")

        # 查找元素
        button = soup.find(config.elementType, string=config.monitorText)
        if button:
            print(
                f"网站:{config.website} 商品页面:{config.name} 元素:{config.elementType} '{config.monitorText}' 存在"
            )

            notice_emails = []
            for email in config.emails:
                if should_notice(email, config.url, config.noticeSeconds):
                    notice_emails.append(email)
                else:
                    print(f"{email} 对 {config.url} 在通知间隔内，跳过检查")

            send_email(config, notice_emails)
        else:
            print(
                f"网站:{config.website} 商品页面:{config.name} 元素:{config.elementType} '{config.monitorText}' 不存在"
            )
    except Exception as e:
        print(
            f"发生错误,网站:{config.website} 商品页面:{config.name} 元素:{config.elementType} '{config.monitorText}' 错误:{e}"
        )


def send_email(config: WebsiteConfig, emails: List[str]):
    if not emails:
        print(f"没有需要通知的邮箱")
        return
    try:
        with yagmail.SMTP(os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD")) as yag:
            # 构建一个完整的HTML邮件内容
            html_content = f"""
            <html>
                <body>
                    <h2>{config.website}-{config.name} 现已有货!</h2>
                    <h3><a href='{config.url}'>点击查看商品</a></h3>
                    <p><img src='{config.pic}' alt='商品图片' style='max-width: 500px;'></p>
                    <h4><small>此邮件为系统自动发送，请勿直接回复。</small></h4>
                </body>
            </html>
            """
            yag.send(
                to=emails,
                subject=f"{config.website}-{config.name} 现已有货!",
                contents=[html_content],  # 将整个HTML内容作为一个字符串发送
            )
            print(
                f"邮件发送成功,网站:{config.website} 商品页面:{config.name} 元素:{config.elementType} emails: {emails}"
            )
            save_last_notice_time(emails, config.url, time.time())
    except Exception as e:
        print(
            f"邮件发送失败,网站:{config.website} 商品页面:{config.name} 元素:{config.elementType} emails: {emails} error: {e}"
        )


if __name__ == "__main__":
    try:
        print("任务开始......")
        configs = load_config("config.json")

        with ThreadPoolExecutor(max_workers=5) as executor:
            for config in configs:
                executor.submit(check_and_notice, config)
    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        print("任务结束......")
        exit(0)
