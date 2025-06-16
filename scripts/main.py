import argparse
import yaml
from pathlib import Path
import sys
import re
import os

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
os.chdir(project_root)
sys.path.append(str(project_root))

from src.data.fetcher import DataFetcher
from src.data.storage import DataStorage
from src.utils.logger import setup_logger
import pandas as pd

# 创建logger实例
logger = setup_logger("main")

HOT_SECTIONS = [
    {"type": "HOT", "typeVal": "1368024613355786240", "level": 0, "nameZh": "百战指数"},
    {"type": "HOT", "typeVal": "1402501509110038528", "level": 0, "nameZh": "千战指数"},
    {"type": "HOT", "typeVal": "1401696786733232128", "level": 0, "nameZh": "多普勒指数"},
    {"type": "HOT", "typeVal": "1401697417900486656", "level": 0, "nameZh": "伽玛多普勒指数"},
    {"type": "HOT", "typeVal": "1355758503748096000", "level": 0, "nameZh": "原皮指数"},
]

def load_config() -> dict:
    """加载配置文件
    
    Returns:
        dict: 配置信息
    """
    try:
        config_path = project_root / "config" / "config.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        logger.info("成功加载配置文件")
        return config
    except Exception as e:
        logger.error(f"加载配置文件时发生错误: {str(e)}")
        raise

def safe_name(name):
    """去除文件/文件夹名中的特殊字符"""
    return re.sub(r'[\\/:*?"<>|]', '_', name)

def fetch_section_and_children_kline(fetcher, storage, section, parent_path="", level=0):
    section_name = section.get('nameZh')
    section_id = section.get('typeVal')
    section_type = section.get('type', 'BROAD')
    section_level = section.get('level', level)
    if not section_id or not section_name:
        return

    # 拼接当前板块的目录
    safe_section_name = safe_name(section_name)
    current_path = os.path.join(parent_path, safe_section_name) if parent_path else safe_section_name
    full_dir = os.path.join(fetcher.output_dir, current_path)
    os.makedirs(full_dir, exist_ok=True)

    logger.info(f"开始获取板块 {section_name} 的K线数据")
    api_url = f"{fetcher.base_url}/user/item/block/v1/kline"
    params = {
        "type": section_type,
        "level": section_level,
        "typeVal": section_id,
        "klineType": "2",
        "platform": "ALL",
        "timestamp": 0,
        "maxTime": ""
    }
    kline_data = fetcher.fetch_kline(api_url, params)
    filename = os.path.join(current_path, f"{safe_section_name}.csv")
    if fetcher.save_to_csv(kline_data, filename):
        logger.info(f"成功保存板块 {section_name} 的K线数据")
    else:
        logger.error(f"保存板块 {section_name} 的K线数据失败")

    # 只递归到level=1
    if section_level < 1:
        children = fetcher.fetch_sections(
            type=section_type,
            level=section_level + 1,
            platform="ALL",
            typeVal=section_id,
            typeDay="1"
        )
        for child in children:
            fetch_section_and_children_kline(fetcher, storage, child, parent_path=current_path, level=section_level + 1)


def fetch_all_sections(fetcher: DataFetcher, storage: DataStorage):
    """递归获取所有板块及其子板块的K线数据，自动分级存储"""
    try:
        sections = fetcher.fetch_sections()
        if not sections:
            logger.error("获取板块列表失败")
            return
        for section in sections:
            fetch_section_and_children_kline(fetcher, storage, section, parent_path="", level=0)
    except Exception as e:
        logger.error(f"获取所有板块K线数据时发生错误: {str(e)}")

def fetch_latest_data(fetcher: DataFetcher, storage: DataStorage):
    """获取最新数据
    
    Args:
        fetcher: 数据获取器
        storage: 数据存储器
    """
    try:
        # 获取所有板块
        sections = fetcher.fetch_sections()
        if not sections:
            logger.error("获取板块列表失败")
            return
            
        # 遍历每个板块获取最新K线数据
        for section in sections:
            section_id = section.get('id')
            section_name = section.get('name')
            if not section_id or not section_name:
                continue
                
            logger.info(f"开始获取板块 {section_name} 的最新K线数据")
            
            # 构建API URL和参数
            api_url = f"{fetcher.base_url}/user/item/block/v1/kline"
            params = {
                "id": section_id,
                "type": "1"  # 日K线
            }
            
            # 获取K线数据
            kline_data = fetcher.fetch_kline(api_url, params)
            if not kline_data:
                logger.warning(f"获取板块 {section_name} 的最新K线数据失败")
                continue
                
            # 转换为DataFrame
            df = pd.DataFrame(kline_data)
            if df.empty:
                continue
                
            # 追加数据
            filename = f"{section_name}.csv"
            if storage.append_to_csv(df, filename):
                logger.info(f"成功追加板块 {section_name} 的最新K线数据")
            else:
                logger.error(f"追加板块 {section_name} 的最新K线数据失败")
                
    except Exception as e:
        logger.error(f"获取最新数据时发生错误: {str(e)}")

def fetch_market(fetcher, storage):
    """抓取大盘K线数据"""
    api_url = f"{fetcher.base_url}/user/statistics/v1/kline"
    params = {
        "type": "2",
        "timestamp": 0,
        "maxTime": ""
    }
    kline_data = fetcher.fetch_kline(api_url, params)
    filename = "大盘.csv"
    if fetcher.save_to_csv(kline_data, filename):
        logger.info("已抓取大盘K线数据")
    else:
        logger.warning("未获取到大盘K线数据")

def fetch_hot_sections(fetcher, storage):
    """抓取热门板块K线数据，统一存储在kline/HOT目录下"""
    api_url = f"{fetcher.base_url}/user/item/block/v1/kline"
    hot_dir = os.path.join(fetcher.output_dir, "HOT")
    os.makedirs(hot_dir, exist_ok=True)
    for section in HOT_SECTIONS:
        params = {
            "type": section["type"],
            "level": section["level"],
            "typeVal": section["typeVal"],
            "klineType": "2",
            "platform": "ALL",
            "timestamp": 0,
            "maxTime": ""
        }
        kline_data = fetcher.fetch_kline(api_url, params)
        safe_section_name = safe_name(section['nameZh'])
        filename = os.path.join("HOT", f"{safe_section_name}.csv")
        if fetcher.save_to_csv(kline_data, filename):
            logger.info(f"已抓取{section['nameZh']}K线数据")
        else:
            logger.warning(f"未获取到{section['nameZh']}K线数据")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="K线数据获取工具")
    parser.add_argument("--mode", choices=["all", "latest"], default="all",
                      help="运行模式：all-获取所有数据，latest-获取最新数据")
    args = parser.parse_args()
    
    try:
        # 加载配置
        config = load_config()
        
        # 初始化数据获取器和存储器
        fetcher = DataFetcher(config)
        storage = DataStorage(config)
        
        # 根据模式执行相应操作
        if args.mode == "all":
            fetch_market(fetcher, storage)
            fetch_hot_sections(fetcher, storage)
            fetch_all_sections(fetcher, storage)
        else:
            fetch_latest_data(fetcher, storage)
            
    except Exception as e:
        logger.error(f"程序执行出错: {str(e)}")
        raise

if __name__ == "__main__":
    main()
