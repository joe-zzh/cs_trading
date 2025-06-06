import requests
import json
import time
import os

def get_json(itemId, platform_name, save_dir="./data"):
    """
    尝试使用给定的 itemId 和 platform='BUFF' 参数从接口抓取数据。
    返回接口返回的 JSON 数据。
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
    # 注意：这里的 platform 参数固定为 "BUFF"
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
        # 增加超时，避免请求卡住
        resp = requests.post(url, headers=headers, params=params, data=data, timeout=10)
        resp.raise_for_status() # 检查HTTP状态码，如果不是2xx则抛出异常
        response_data = resp.json()

        # 打印接口返回的原始数据（前200字符），用于调试
        print(f"  尝试 {platform_name} itemId {itemId} 返回（前200字符）：{resp.text[:200]}...")

        # 判断是否成功抓取到有效数据 (例如：success为true且data非空)
        # 你可能需要根据实际接口返回结构调整这里的判断条件
        if response_data.get("success") is True and response_data.get("data"):
             # 确保保存目录存在
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, f"{itemId}.json")
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(response_data, f, ensure_ascii=False, indent=2)
            print(f"  ✅ 成功抓取并保存数据到 {save_path}")
            return response_data # 返回数据表示成功
        else:
            print(f"  尝试 {platform_name} itemId {itemId} 返回空数据或失败响应。")
            return None # 返回None表示失败或无数据

    except requests.exceptions.RequestException as e:
        print(f"  尝试 {platform_name} itemId {itemId} 请求失败: {e}")
        return None
    except json.JSONDecodeError:
        print(f"  尝试 {platform_name} itemId {itemId} 返回内容不是有效的 JSON。")
        return None


if __name__ == "__main__":
    with open("C:/CS/base_info/base_info.json", "r", encoding="utf-8") as f:
        base_info = json.load(f)

    items_data = base_info.get("data", []) # 从data字段获取物品列表

    for idx, item in enumerate(items_data):
        item_name = item.get("name", "未知物品")
        platform_list = item.get("platformList", [])
        print(f"\n正在处理物品：{item_name} ({idx+1}/{len(items_data)})")

        found_data = False # 标志是否已找到有效数据

        if not platform_list:
            print(f"  {item_name} 没有平台信息，跳过。")
            continue

        for platform in platform_list:
            platform_name = platform.get("name", "未知平台")
            platform_item_id = platform.get("itemId")

            if platform_item_id:
                print(f"  正在尝试使用 {platform_name} 的 itemId: {platform_item_id}")
                # 调用 get_json，并传入平台名称用于打印日志
                response_data = get_json(platform_item_id, platform_name)

                if response_data: # 如果 get_json 返回了数据 (表示成功)
                    found_data = True
                    break # 找到数据了，跳出当前物品的平台循环
                else:
                    time.sleep(0.5) # 尝试失败，稍微等待再试下一个平台ID

            else:
                print(f"  {platform_name} 没有 itemId，跳过。")

        if not found_data:
            print(f"  {item_name} 尝试所有平台 itemId 后仍未抓取到有效数据。")
