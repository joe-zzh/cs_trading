import os
import pandas as pd

def get_all_market_names(data_dir="data/kline"):
    names = set()
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            if file.endswith(".csv"):
                names.add(file.replace(".csv", ""))
    return list(names)

def find_csv_file(market_name, data_dir="data/kline"):
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            if file.endswith(".csv") and market_name in file:
                return os.path.join(root, file)
    return None

def read_market_data(market_name, data_dir="data/kline"):
    csv_path = find_csv_file(market_name, data_dir)
    if not csv_path:
        return None
    df = pd.read_csv(csv_path)
    return df 