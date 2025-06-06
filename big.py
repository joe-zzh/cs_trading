import requests
import json
import time # Optional: for adding a delay between requests
import os # Optional: for saving data to files
import csv # Import the csv module

# 请求的 URL
url = "https://sdt-api.ok-skins.com/user/item/block/v1/relation?timestamp=1749212600563"

# 请求头
headers = {
    "accept": "application/json",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "access-token": "f6be86dc-47cd-459b-9a1e-e58ef8353b28",
    "content-type": "application/json",
    "language": "zh_CN",
    "origin": "https://steamdt.com",
    "priority": "u=1, i",
    "referer": "https://steamdt.com/",
    "sec-ch-ua": '"Microsoft Edge";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0",
    "x-app-version": "1.0.0",
    "x-currency": "CNY",
    "x-device": "1",
    "x-device-id": "84bbee2d-6ad0-4b69-9c88-9f8404a0c28"
}

# 请求体
payload = {
    "type": "HOT",
    "level": 0,
    "platform": "ALL",
    "typeDay": "5",
    "timestamp": "1749212600563"
}

# 将请求体转换为 JSON 字符串
payload_json = json.dumps(payload)

def scrape_data_to_csv(filename="scrape_results.csv"):
    """发送 POST 请求并处理响应，将数据保存到 CSV 文件"""
    try:
        print(f"正在向 {url} 发送请求...")
        # 发送 POST 请求
        response = requests.post(url, headers=headers, data=payload_json)

        # 检查响应状态码
        if response.status_code == 200:
            print("请求成功！")
            # 解析 JSON 响应
            data = response.json()

            # 检查是否成功获取到数据列表
            if data and data.get("success") and data.get("data") and isinstance(data["data"], list):
                results = data["data"]

                # 将数据写入 CSV 文件
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    # 定义 CSV 文件的列头
                    fieldnames = ['Name (中文)', 'Index', 'Rise/Fall Difference', 'Rise/Fall Rate']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                    # 写入列头
                    writer.writeheader()

                    # 写入数据行
                    for item in results:
                        writer.writerow({
                            'Name (中文)': item.get('nameZh', ''),
                            'Index': item.get('index', ''),
                            'Rise/Fall Difference': item.get('riseFallDiff', ''),
                            'Rise/Fall Rate': item.get('riseFallRate', '')
                        })

                print(f"数据已成功保存到 {filename}")

            else:
                print("响应中未找到有效的数据列表。")
                print(json.dumps(data, indent=4)) # 打印完整响应体以便查看问题

        else:
            print(f"请求失败，状态码：{response.status_code}")
            print(f"响应体：{response.text}")

    except requests.exceptions.RequestException as e:
        print(f"请求发生错误：{e}")
    except Exception as e:
        print(f"处理数据时发生错误：{e}")

# 如果您想重复爬取，可以使用一个循环
# 例如，每隔一定时间（如 60 秒）爬取一次
# while True:
#     scrape_data_to_csv()
#     time.sleep(60) # 暂停 60 秒

# 如果只想运行一次，直接调用函数
scrape_data_to_csv()