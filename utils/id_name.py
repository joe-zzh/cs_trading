import json

with open("C:/CS/base_info/base_info.json", "r", encoding="utf-8") as f:
    base_info = json.load(f)

itemid_map = {}

for item in base_info["data"]:
    platform_list = item.get("platformList", [])
    if platform_list:
        first_id = platform_list[0].get("itemId")
        if first_id:
            itemid_map[first_id] = {
                "name": item.get("name", ""),
                "market_hash_name": item.get("marketHashName", "")
            }

with open("C:/CS/base_info/itemid_map.json", "w", encoding="utf-8") as f:
    json.dump(itemid_map, f, ensure_ascii=False, indent=2)

print(f"已生成 itemid_map.json，共 {len(itemid_map)} 个物品")