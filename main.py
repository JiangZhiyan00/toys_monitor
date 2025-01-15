import os
import json
import time
from dataclasses import dataclass
from typing import List

import requests
import jsoncomment
import yagmail
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from bs4 import Tag


PROXY_URL_PREFIX = "https://proxy.jzy88.top/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0"
}


@dataclass
class WebsiteConfig:
    website: str
    name: str
    pic: str
    url: str
    elementTypes: List[str]
    monitorText: str
    emails: List[str]
    needProxy: bool = False
    noticeSeconds: int = 1800
    timeout: int = 5
    maxRetries: int = 3


def load_config(file_path: str) -> List[WebsiteConfig]:
    with open(file_path, "r", encoding="utf-8") as f:
        json_parser = jsoncomment.JsonComment(json)
        data = json_parser.load(f)
    return [WebsiteConfig(**item) for item in data]


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


def find_nested_element(
    soup: BeautifulSoup, element_types: list[str], target_text: str
) -> list[Tag]:

    if not element_types:
        return []

    parents = [soup]
    # 查找除最后一个元素外的所有父元素
    for element_type in element_types[:-1]:
        new_parents = []
        for parent in parents:
            found = parent.find_all(element_type)
            new_parents.extend(found)
        parents = new_parents
        if not parents:
            return []

    # 查找所有包含指定文本的元素
    results = []
    for parent in parents:
        found = parent.find_all(element_types[-1], string=target_text)
        results.extend(found)
    return results


def make_request_with_retry(
    url: str, headers: dict, timeout: int, max_retries: int = 3
) -> requests.Response:
    for retry in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=timeout)

            if response.status_code == 503 and retry < max_retries - 1:
                print(f"遇到503错误，正在进行第{retry + 1}次重试...")
                time.sleep(1)
                continue

            response.raise_for_status()
            return response

        except requests.exceptions.RequestException as e:
            if retry == max_retries - 1:
                raise
            print(f"请求失败，正在进行第{retry + 1}次重试... 错误: {e}")
            time.sleep(1)

    raise requests.exceptions.RequestException(f"请求{url}, 重试{max_retries}次均失败")


def check_and_notice(config: WebsiteConfig):
    try:
        # 使用封装的重试方法发送请求
        response = make_request_with_retry(
            PROXY_URL_PREFIX + config.url if config.needProxy else config.url,
            HEADERS,
            config.timeout,
            config.maxRetries,
        )

        # 解析 HTML
        soup = BeautifulSoup(response.text, "html.parser")

        # 查找元素
        elements = find_nested_element(soup, config.elementTypes, config.monitorText)
        if elements:
            print(
                f"网站:{config.website} 商品页面:{config.name} 元素:{config.elementTypes} '{config.monitorText}' 存在"
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
                f"网站:{config.website} 商品页面:{config.name} 元素:{config.elementTypes} '{config.monitorText}' 不存在"
            )
    except Exception as e:
        print(
            f"发生错误,网站:{config.website} 商品页面:{config.name} 元素:{config.elementTypes} '{config.monitorText}' 错误:{e}"
        )


def send_email(config: WebsiteConfig, emails: List[str]):
    if not emails:
        print(
            f"网站:{config.website} 商品页面:{config.name} 元素:{config.elementTypes} 没有需要通知的邮箱"
        )
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
                f"邮件发送成功,网站:{config.website} 商品页面:{config.name} 元素:{config.elementTypes} emails: {emails}"
            )
            save_last_notice_time(emails, config.url, time.time())
    except Exception as e:
        print(
            f"邮件发送失败,网站:{config.website} 商品页面:{config.name} 元素:{config.elementTypes} emails: {emails} error: {e}"
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
