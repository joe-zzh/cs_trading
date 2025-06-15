import requests
import json
import time
import os # Import the os module

base_api_url = "https://sdt-api.ok-skins.com/user/item/block/v1/"

# Define the directory to save data
output_dir = "data/index"

# Create the directory if it does not exist
os.makedirs(output_dir, exist_ok=True)

headers = {
    "accept": "application/json",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "zh-CN,zh;q=0.9",
    "access-token": "undefined", # 注意：如果需要实际的access-token，这里需要替换
    "content-type": "application/json",
    "language": "zh_CN",
    "origin": "https://steamdt.com",
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

# Step 1: Get next-level sections
next_level_url = f"{base_api_url}next-level?timestamp={int(time.time() * 1000)}"
next_level_payload = {
    "type": "BROAD",
    "level": 0,
    "platform": "ALL",
    "typeVal": "",
    "typeDay": "1",
    "timestamp": f"{int(time.time() * 1000)}" # Use current timestamp for payload as well
}

try:
    print("Fetching next-level sections...")
    next_level_response = requests.post(next_level_url, headers=headers, json=next_level_payload)
    next_level_response.raise_for_status()
    
    next_level_data = next_level_response.json()
    if next_level_data.get("success") and next_level_data.get("data"):
        sections = next_level_data["data"]
        print(f"Found {len(sections)} next-level sections.")

        # Step 2 & 3: Iterate through sections and fetch K-line data
        for section in sections:
            section_type = section.get("type")
            section_type_val = section.get("typeVal")
            section_level = section.get("level")
            section_name_zh = section.get("nameZh", "未知板块")

            print(f"\n--- Fetching K-line data for section: {section_name_zh} (type={section_type}, typeVal={section_type_val}, level={section_level}) ---")

            all_kline_data_for_section = []
            current_max_time_seconds = int(time.time())

            while True:
                kline_timestamp = int(time.time() * 1000)
                kline_url = f"{base_api_url}kline?timestamp={kline_timestamp}"
                kline_payload = {
                    "type": section_type,
                    "level": section_level,
                    "typeVal": section_type_val,
                    "klineType": "2", # Fixed to '2'代表日k，'1'为时k,'3'为周k
                    "platform": "BUFF",
                    "timestamp": f"{kline_timestamp}",
                    "maxTime": current_max_time_seconds # Add maxTime for pagination
                }

                try:
                    print(f"  Fetching K-line data (klineType=2, maxTime={current_max_time_seconds})...")
                    kline_response = requests.post(kline_url, headers=headers, json=kline_payload)
                    kline_response.raise_for_status()

                    kline_data = kline_response.json()

                    if kline_data.get("success") and kline_data.get("data"):
                        kline_batch = kline_data["data"]

                        if not kline_batch:
                            print("  当前maxTime没有返回数据，停止爬取此板块的K线数据。")
                            break

                        all_kline_data_for_section.extend(kline_batch)

                        # 找到当前批次中最旧的时间戳（秒级）
                        oldest_timestamp_in_current_batch = int(kline_batch[0][0])
                        
                        # 检测maxTime是否向前推进，防止无限循环
                        if oldest_timestamp_in_current_batch >= current_max_time_seconds and len(kline_batch) > 0:
                            print(f"  检测到 maxTime 没有向前推进，可能已达到数据尽头或API行为异常。停止爬取此板块的K线数据。")
                            break

                        current_max_time_seconds = oldest_timestamp_in_current_batch - 1 # 请求该最旧时间戳之前的数据

                        time.sleep(0.5) # Add a short delay
                    else:
                        print("  没有更多数据了或请求失败，停止爬取此板块的K线数据。")
                        print("  响应内容:", kline_response.text)
                        break

                except requests.exceptions.RequestException as e:
                    print(f"  请求K线数据时发生错误: {e}")
                    if hasattr(e, 'response') and e.response is not None:
                        print(f"  响应内容: {e.response.text}")
                    break
                except json.JSONDecodeError:
                    print("  K线数据响应不是有效的JSON格式。")
                    print("  原始响应内容：", kline_response.text)
                    break
                except IndexError:
                    print("  K线数据结构不符合预期，停止爬取此板块的K线数据。")
                    print("  原始响应内容：", kline_response.text)
                    break
            
            # Save all collected K-line data for the section
            if all_kline_data_for_section:
                filename = os.path.join(output_dir, f"{section_name_zh}.json")
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(all_kline_data_for_section, f, indent=4, ensure_ascii=False)
                print(f"  总共获取到 {len(all_kline_data_for_section)} 条K线数据，并已保存到 {filename}")
            else:
                print(f"  未获取到 {section_name_zh} 的K线数据。")
    else:
        print("Failed to get next-level sections or no data returned.")
        print(json.dumps(next_level_data, indent=4, ensure_ascii=False))

except requests.exceptions.RequestException as e:
    print(f"Failed to fetch next-level sections: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print(f"Response content: {e.response.text}") 