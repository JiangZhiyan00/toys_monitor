# 商品监控脚本

这是一个简单的 Python 脚本，用于监控指定网站上的商品是否有货，并在有货时发送邮件通知。

## 功能

- **多网站监控:** 可以同时监控多个网站的商品。
- **灵活的元素定位:** 通过配置 `elementTypes` 和 `monitorText` 定位页面上的特定元素。
- **邮件通知:** 当商品有货时，发送邮件通知到指定的邮箱。
- **通知频率控制:** 可以设置通知间隔，避免频繁发送邮件。
- **代理支持:** 可以配置是否使用代理访问网站。
- **重试机制:** 当请求失败时，会自动重试。

## 使用方法

1.  **安装依赖:**

    ```bash
    pip install -r requirements.txt
    ```

2.  **配置 `config.json`:**

    `config.json` 文件用于配置需要监控的商品信息。它是一个 JSON 数组，每个元素代表一个需要监控的商品。以下是 `config.json` 中每个参数的含义：

    ```json
    [
      {
        "website": "yodobashi",
        "name": "仮面ライダー555",
        "pic": "https://image.yodobashi.com/product/100/000/001/008/874/982/100000001008874982_10204.jpg",
        "url": "https://www.yodobashi.com/product/100000001008874982/",
        "elementTypes": ["a"],
        "monitorText": "ショッピングカートに入れる",
        "needProxy": true,
        "noticeSeconds": 1800,
        "timeout": 5,
        "emails": ["user1@xx.com", "user2@yy.com"],
        "maxRetries": 3
      }
    ]
    ```

    - `website` (string): 网站的名称，用于标识邮件通知中的来源。
    - `name` (string): 商品的名称，用于标识邮件通知中的商品。
    - `pic` (string): 商品的图片 URL，用于在邮件中显示商品图片。
    - `url` (string): 商品的 URL，用于访问商品页面。
    - `elementTypes` (array of strings): 用于定位目标元素的 HTML 标签类型列表。例如 `["div", "span", "a"]` 表示先查找 `div` 标签，然后在找到的 `div` 标签中查找 `span` 标签，最后在找到的 `span` 标签中查找 `a` 标签。
    - `monitorText` (string): 需要监控的文本内容，用于在 `elementTypes` 定位的元素中查找。
    - `needProxy` (boolean, optional): 是否需要使用代理访问网站，默认为 `false`。
    - `noticeSeconds` (integer, optional): 通知间隔，即同一个邮箱在设定时间内不会重复收到该商品的邮件提醒，单位为秒，默认为 `1800` 秒（30 分钟）。
    - `timeout` (integer, optional): 请求超时时间，单位为秒，默认为 `5` 秒。
    - `emails` (array of strings): 接收通知邮件的邮箱列表。
    - `maxRetries` (integer, optional): 请求失败时的最大重试次数，默认为 `3` 次。

    **注意:**

    - `config.json` 文件支持注释，但请确保除去注释部分后，JSON 格式是正确的。
    - `elementTypes` 和 `monitorText` 的组合用于精确定位页面上表示商品有货的元素。您需要根据实际的网站 HTML 结构进行调整。

3.  **配置环境变量:**

    您需要在系统环境变量中设置以下两个变量：

    - `SMTP_USER`: 您的 SMTP 邮箱用户名。
    - `SMTP_PASSWORD`: 您的 SMTP 邮箱密码或授权码。

4.  **运行脚本:**

    ```bash
    python main.py
    ```

    脚本会读取 `config.json` 文件中的配置，并开始监控商品。当商品有货时，会发送邮件通知。

## 注意事项

- 请确保您的网络连接正常。
- 请确保您的 SMTP 邮箱配置正确。
- 请根据实际情况调整 `config.json` 中的参数。
- 如果遇到问题，请查看脚本的输出信息。
