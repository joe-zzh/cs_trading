import os
import time
import pandas as pd
from datetime import datetime
import requests

# 指数板块配置
index_sections = [
    {"type": "HOT", "typeVal": "1368024613355786240", "level": 0, "nameZh": "百战指数"},
    {"type": "HOT", "typeVal": "1402501509110038528", "level": 0, "nameZh": "千战指数"},
    {"type": "HOT", "typeVal": "1401696786733232128", "level": 0, "nameZh": "多普勒指数"},
    {"type": "HOT", "typeVal": "1401697417900486656", "level": 0, "nameZh": "伽玛多普勒指数"},
    {"type": "HOT", "typeVal": "1355758503748096000", "level": 0, "nameZh": "原皮指数"},
]

output_dir = "data/index"
os.makedirs(output_dir, exist_ok=True)

headers = {
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "zh-CN,zh;q=0.9",
    "access-token": "undefined",
    "language": "zh_CN",
    "origin": "https://steamdt.com",
    "priority": "u=1, i",
    "referer": "https://steamdt.com/",
    "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    "x-app-version": "1.0.0",
    "x-currency": "CNY",
    "x-device": "1",
    "x-device-id": "0fdc1236-31ee-464b-bb73-a33616b068c2"
}

base_api_url = "https://sdt-api.ok-skins.com/user/item/block/v1/"

def fetch_latest_kline_for_section(section):
    section_type = section.get("type")
    section_type_val = section.get("typeVal")
    section_level = section.get("level")
    section_name_zh = section.get("nameZh", "未知板块")
    current_max_time_seconds = int(time.time())
    kline_timestamp = int(time.time() * 1000)
    kline_url = f"{base_api_url}kline?timestamp={kline_timestamp}"
    kline_payload = {
        "type": section_type,
        "level": section_level,
        "typeVal": section_type_val,
        "klineType": "2",
        "platform": "HOT",
        "timestamp": f"{kline_timestamp}",
        "maxTime": current_max_time_seconds
    }
    try:
        print(f"Fetching latest K-line for {section_name_zh}...")
        resp = requests.post(kline_url, headers=headers, json=kline_payload)
        resp.raise_for_status()
        data = resp.json()
        if data.get("success") and data.get("data"):
            kline_batch = data["data"]
            if not kline_batch:
                print(f"No new data for {section_name_zh}.")
                return []
            return kline_batch
        else:
            print(f"Failed to fetch latest K-line for {section_name_zh}.")
            return []
    except Exception as e:
        print(f"Error fetching latest K-line for {section_name_zh}: {e}")
        return []

def append_new_kline_to_csv(kline_data, section_name_zh):
    if not kline_data:
        return
    df_new = pd.DataFrame(kline_data)
    df_new = df_new.iloc[:, :7]
    df_new.columns = ["date", "open", "close", "high", "low", "volume", "amount"]
    df_new["date"] = pd.to_datetime(df_new["date"], unit="s").dt.strftime("%Y-%m-%d")
    filename = os.path.join(output_dir, f"{section_name_zh}.csv")
    if os.path.exists(filename):
        df_old = pd.read_csv(filename)
        # 只保留新数据中date在旧数据中没有的部分
        df_new = df_new[~df_new["date"].isin(df_old["date"])]
        if df_new.empty:
            print(f"{section_name_zh} 今日数据已存在，无需追加。")
            return
        df_all = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df_all = df_new
    df_all.to_csv(filename, index=False, encoding="utf-8-sig")
    print(f"{section_name_zh} 已追加 {len(df_new)} 条新数据。")

if __name__ == "__main__":
    for section in index_sections:
        kline_data = fetch_latest_kline_for_section(section)
        append_new_kline_to_csv(kline_data, section["nameZh"])
    print("所有指数最新K线数据已抓取并追加。") 