import requests
import json
import time
import os
import pandas as pd # 导入 pandas 库

# 根据你提供的接口返回结构，定义CSV列名
# 这是一个列表的列表，每个内层列表有8个元素
CSV_COLUMNS = ["Timestamp", "sellPrice", "sellCount", "biddingPrice", "biddingCount", "turnOver", "volume", "existingCount"]

def get_and_save_csv(itemId, item_name, save_dir="./data_csv"):
    """
    使用所有平台 itemId 从接口抓取数据，并保存为 CSV 文件。
    返回 True 表示成功，False 表示失败或无数据。
    """
    headers = {
        "accept": "application/json",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "access-token": "undefined",
        "cache-control": "no-cache",
        "content-type": "application/json",
        "language": "zh_CN",
        "origin": "https://steamdt.com",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://steamdt.com/",
        "sec-ch-ua": "\"Chromium\";v=\"136\", \"Microsoft Edge\";v=\"136\", \"Not.A/Brand\";v=\"99\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0",
        "x-app-version": "1.0.0",
        "x-currency": "CNY",
        "x-device": "1",
        "x-device-id": "55df873d-f8e8-43a0-af19-4e9ea2700deb"
    }
    url = "https://sdt-api.ok-skins.com/user/steam/type-trend/v2/item/details"
    params = {
        "timestamp": "1749043894278"
    }
    # 这里平台参数还是BUFF，itemId是尝试使用的那个
    data = {
        "platform": "BUFF",
        "typeDay": "5",
        "dateType": 3,
        "specialStyle": "",
        "itemId": itemId,
        "timestamp": "1749043894278"
    }
    data = json.dumps(data, separators=(',', ':'))

    try:
        print(f"  尝试抓取 itemId {itemId} ({item_name})...")
        resp = requests.post(url, headers=headers, params=params, data=data, timeout=15)
        resp.raise_for_status()

        response_data = resp.json()

        historical_data_list = response_data.get("data")

        # 检查是否成功抓取到有效数据 (success为true且data非空列表)
        if response_data.get("success") is True and isinstance(historical_data_list, list) and historical_data_list:
            # 将数据列表转换为 pandas DataFrame
            df = pd.DataFrame(historical_data_list)

            # 为DataFrame设置列名，检查列数是否为预期的8列
            if df.shape[1] == 8:
                 df.columns = CSV_COLUMNS
            else:
                 print(f"  警告: itemId {itemId} ({item_name}) 返回数据的列数 ({df.shape[1]}) 与预设列名 ({len(CSV_COLUMNS)}) 不匹配。原始列名将保留。")
                 # 如果列数不匹配，不设置列名
                 pass

            # 确保保存目录存在
            os.makedirs(save_dir, exist_ok=True)
            # 使用 itemId 作为文件名，保存为 CSV
            csv_path = os.path.join(save_dir, f"{itemId}.csv")
            df.to_csv(csv_path, index=False, encoding="utf-8")
            print(f"  ✅ 成功抓取并保存数据到 {csv_path}")
            return True # 表示成功抓取并保存

        else:
            # 打印接口返回的原始数据（前200字符），用于调试空数据或失败响应
            print(f"  itemId {itemId} ({item_name}) 返回空数据或失败响应。返回内容（前200字符）：{resp.text[:200]}...")
            return False # 表示失败或无数据

    except requests.exceptions.RequestException as e:
        print(f"  itemId {itemId} ({item_name}) 请求失败: {e}")
        return False
    except json.JSONDecodeError:
        print(f"  itemId {itemId} ({item_name}) 返回内容不是有效的 JSON。")
        print(f"  返回内容（前200字符）：{resp.text[:200]}...")
        return False
    except Exception as e:
        print(f"  处理 itemId {itemId} ({item_name}) 时发生未知错误: {e}")
        return False


if __name__ == "__main__":
    # 假定 base_info.json 文件存在
    base_info_path = "C:/CS/base_info/base_info.json"

    if not os.path.exists(base_info_path):
        print(f"错误：找不到 {base_info_path} 文件。请检查路径。")
    else:
        with open(base_info_path, "r", encoding="utf-8") as f:
            base_info = json.load(f)

        items_data = base_info.get("data", [])

        total_items = len(items_data)
        print(f"开始批量抓取数据，共 {total_items} 个物品...")

        for idx, item in enumerate(items_data):
            item_name = item.get("name", "未知物品")
            platform_list = item.get("platformList", [])
            print(f"\n正在处理 ({idx+1}/{total_items}) 物品: {item_name}")

            found_data_for_item = False # 标志当前物品是否已找到有效数据

            if not platform_list:
                print(f"  {item_name} 没有平台信息，跳过。")
                continue

            for platform in platform_list:
                platform_name = platform.get("name", "未知平台")
                platform_item_id = platform.get("itemId")

                if platform_item_id:
                    print(f"  正在尝试使用 {platform_name} 的 itemId: {platform_item_id}")
                    # 调用 get_and_save_csv 函数
                    success = get_and_save_csv(platform_item_id, item_name)

                    if success: # 如果 get_and_save_csv 返回 True 表示成功
                        found_data_for_item = True
                        break # 找到数据了，跳出当前物品的平台循环

                else:
                    print(f"  {platform_name} 没有 itemId，跳过。")

                # 无论成功与否，尝试完一个平台ID后都等待一下
                time.sleep(0.5) # 平台尝试间隔

            if not found_data_for_item:
                print(f"  {item_name} 尝试所有平台 itemId 后仍未抓取到有效数据。")
            else:
                 # 如果当前物品成功抓取到数据，等待更长时间再处理下一个物品
                 time.sleep(2) # 物品间隔

        print("\n批量抓取完成。")
