import os
import time
from kline_fetcher import fetch_kline, save_kline_to_csv

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

index_sections = [
    {"type": "HOT", "typeVal": "1368024613355786240", "level": 0, "nameZh": "百战指数"},
    {"type": "HOT", "typeVal": "1402501509110038528", "level": 0, "nameZh": "千战指数"},
    {"type": "HOT", "typeVal": "1401696786733232128", "level": 0, "nameZh": "多普勒指数"},
    {"type": "HOT", "typeVal": "1401697417900486656", "level": 0, "nameZh": "伽玛多普勒指数"},
    {"type": "HOT", "typeVal": "1355758503748096000", "level": 0, "nameZh": "原皮指数"},
]

def fetch_and_save_index_sections(mode='all'):
    api_url = "https://sdt-api.ok-skins.com/user/item/block/v1/kline"
    for section in index_sections:
        params = {
            "type": section["type"],
            "level": section["level"],
            "typeVal": section["typeVal"],
            "klineType": "2",
            "platform": "HOT",
            "timestamp": int(time.time() * 1000),
            "maxTime": int(time.time())
        }
        kline_data = fetch_kline(api_url, headers, params, mode=mode)
        filename = os.path.join(output_dir, f"{section['nameZh']}.csv")
        save_kline_to_csv(kline_data, filename)

def fetch_and_save_market(mode='all'):
    api_url = "https://sdt-api.ok-skins.com/user/statistics/v1/kline"
    params = {
        "type": "2",
        "timestamp": int(time.time() * 1000),
        "maxTime": int(time.time())
    }
    kline_data = fetch_kline(api_url, headers, params, mode=mode)
    filename = os.path.join(output_dir, "大盘.csv")
    save_kline_to_csv(kline_data, filename)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['all', 'latest'], default='all')
    parser.add_argument('--market', action='store_true', help='抓取大盘')
    parser.add_argument('--index', action='store_true', help='抓取指数')
    args = parser.parse_args()

    if args.market:
        fetch_and_save_market(mode=args.mode)
    if args.index:
        fetch_and_save_index_sections(mode=args.mode)
    if not args.market and not args.index:
        # 默认都抓
        fetch_and_save_market(mode=args.mode)
        fetch_and_save_index_sections(mode=args.mode) 