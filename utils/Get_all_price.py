from req import get_json
import json
with open("base_info/base_info_20250604_161925.json", "r") as f:
    data = json.load(f)

def get_all_price():
    for item in data:
        itemId = item["itemId"]
        price = get_json(itemId)
        print(price)

get_all_price()