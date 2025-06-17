import os
import pandas as pd
import difflib
from pypinyin import lazy_pinyin, Style
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
import numpy as np
import csv 
import io 
from collections import deque

def get_all_market_names(data_dir="data/kline"):
    names = set()
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            if file.endswith(".csv"):
                # 移除 .csv 后缀
                clean_name = file.replace(".csv", "")
                # 获取父文件夹名称作为潜在的市场分类，例如 'kline/印花/印花.csv' -> '印花'
                parent_folder = os.path.basename(root)
                if parent_folder != "kline" and parent_folder != "HOT": # 避免重复或顶层目录名
                    names.add(parent_folder)
                names.add(clean_name)
    return list(names)

def initialize_market_vectorstore(data_dir="data/kline"):
    """初始化市场名称的向量存储"""
    market_names = get_all_market_names(data_dir)
    if not market_names:
        return None

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = FAISS.from_texts(market_names, embeddings)
    return vectorstore

def fuzzy_match_market_name(market_name, data_dir="data/kline", threshold=0.6):
    """
    支持市场名的模糊匹配，包括拼音、首字母、相似度等。
    返回最优匹配的文件路径和匹配分数。
    """
    candidates = []
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            if file.endswith(".csv"):
                name = file.replace(".csv", "")
                # 1. 直接包含
                if market_name in name:
                    return os.path.join(root, file), 1.0
                # 2. 拼音全拼
                name_pinyin = ''.join(lazy_pinyin(name))
                market_pinyin = ''.join(lazy_pinyin(market_name))
                if market_pinyin and market_pinyin in name_pinyin:
                    candidates.append((os.path.join(root, file), 0.95))
                    continue
                # 3. 首字母
                name_initials = ''.join(lazy_pinyin(name, style=Style.FIRST_LETTER))
                market_initials = ''.join(lazy_pinyin(market_name, style=Style.FIRST_LETTER))
                if market_initials and market_initials in name_initials:
                    candidates.append((os.path.join(root, file), 0.9))
                    continue
                # 4. Levenshtein/相似度
                ratio = difflib.SequenceMatcher(None, market_name, name).ratio()
                if ratio > threshold:
                    candidates.append((os.path.join(root, file), ratio))
    if candidates:
        # 返回分数最高的
        return max(candidates, key=lambda x: x[1])
    return None, 0.0

def find_csv_file(market_name: str, data_dir="data/kline") -> str | None:
    """使用语义搜索和模糊匹配查找最相关的市场名对应的CSV文件路径。"""
    # 优先精确匹配，兼容旧逻辑
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            if file.endswith(".csv"):
                name = file.replace(".csv", "")
                if market_name == name or market_name in name:
                    return os.path.join(root, file)

    # 如果没有精确匹配，尝试语义搜索
    vectorstore = initialize_market_vectorstore(data_dir)
    if vectorstore:
        # 使用相似度搜索，k=1 表示返回最相似的一个
        docs = vectorstore.similarity_search(market_name, k=1)
        if docs:
            best_match_name = docs[0].page_content
            # 根据匹配到的市场名称再次遍历查找文件路径
            for root, dirs, files in os.walk(data_dir):
                for file in files:
                    if file.endswith(".csv") and file.replace(".csv", "") == best_match_name:
                        return os.path.join(root, file)

    return None

def read_market_data(market_name, data_dir="data/kline", num_days: int | None = None):
    csv_path = find_csv_file(market_name, data_dir)
    if not csv_path:
        return None
    
    if num_days is not None and num_days > 0:
        try:
            # 使用deque高效读取文件末尾的num_days行数据
            with open(csv_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            if len(lines) > num_days:
                # 保证header+末尾数据
                lines = [lines[0]] + lines[-num_days:]
            data_str = "".join(lines)
            print("header:", lines[0].strip())
            df = pd.read_csv(io.StringIO(data_str))
            print("df.columns:", df.columns.tolist())
            if 'date' not in df.columns:
                raise ValueError(f"CSV文件缺少'date'列，实际列名: {df.columns.tolist()}")
            # 确保日期是datetime类型并排序
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            return df
        except Exception as e:
            print(f"读取文件末尾数据失败: {e}")
            return None
    else:
        # 如果没有指定num_days，则读取整个文件
        df = pd.read_csv(csv_path)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
    return df