import requests
import pandas as pd
import time
import os

def fetch_kline(api_url, headers, params, mode='all'):
    """通用K线抓取函数，支持全量和只抓最新一批"""
    all_kline_data = []
    current_max_time_seconds = params.get('maxTime', int(time.time()))
    while True:
        params['timestamp'] = int(time.time() * 1000)
        params['maxTime'] = current_max_time_seconds
        try:
            if api_url.endswith('/kline') and 'statistics' in api_url:
                resp = requests.get(api_url, headers=headers, params=params)
            else:
                resp = requests.post(api_url, headers=headers, json=params)
            resp.raise_for_status()
            data = resp.json()
            if data.get("success") and data.get("data"):
                kline_batch = data["data"]
                if not kline_batch:
                    break
                all_kline_data.extend(kline_batch)
                oldest_timestamp = int(kline_batch[0][0])
                if mode == 'latest':
                    break
                if oldest_timestamp >= current_max_time_seconds and len(kline_batch) > 0:
                    break
                current_max_time_seconds = oldest_timestamp - 1
                time.sleep(0.5)
            else:
                break
        except Exception as e:
            print(f"Error fetching kline: {e}")
            break
    return all_kline_data

def save_kline_to_csv(kline_data, filename):
    if not kline_data:
        print(f"No data to save for {filename}")
        return
    df = pd.DataFrame(kline_data)
    df = df.iloc[:, :7]
    df.columns = ["date", "open", "close", "high", "low", "volume", "amount"]
    df["date"] = pd.to_datetime(df["date"], unit="s").dt.strftime("%Y-%m-%d")
    if os.path.exists(filename):
        df_old = pd.read_csv(filename)
        df_new = df[~df["date"].isin(df_old["date"])]
        if df_new.empty:
            print(f"{filename} 今日数据已存在，无需追加。")
            return
        df_all = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df_all = df
    df_all.to_csv(filename, index=False, encoding="utf-8-sig")
    print(f"{filename} 已追加 {len(df)} 条新数据。") 