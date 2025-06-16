import requests
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
from src.utils.logger import setup_logger
import time

# 创建logger实例
logger = setup_logger("data_fetcher")

class DataFetcher:
    def __init__(self, config: Dict):
        """初始化数据获取器
        
        Args:
            config: 配置信息，包含headers等
        """
        self.config = config
        self.headers = config['request']['headers']
        self.base_url = config['data']['base_url']
        self.output_dir = Path(config['data']['output_dir'])
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("数据获取器初始化完成")

    def fetch_kline(self, api_url: str, params: Dict) -> List[Dict]:
        """获取K线数据
        
        Args:
            api_url: API地址
            params: 请求参数
            
        Returns:
            List[Dict]: K线数据列表
        """
        all_kline_data = []
        max_time_raw = params.get('maxTime', None)
        if not max_time_raw:
            current_max_time_seconds = int(time.time())
        else:
            current_max_time_seconds = int(max_time_raw)
        while True:
            params['timestamp'] = int(time.time() * 1000)
            params['maxTime'] = current_max_time_seconds
            try:
                if api_url.endswith('/kline') and 'statistics' in api_url:
                    response = requests.get(api_url, headers=self.headers, params=params)
                else:
                    response = requests.post(api_url, headers=self.headers, json=params)
                response.raise_for_status()
                data = response.json()
                if data.get('success') and data.get('data'):
                    kline_batch = data.get('data', [])
                    if not kline_batch:
                        break
                    all_kline_data.extend(kline_batch)
                    oldest_timestamp = int(kline_batch[0][0])
                    if oldest_timestamp >= current_max_time_seconds and len(kline_batch) > 0:
                        break
                    current_max_time_seconds = oldest_timestamp - 1
                    time.sleep(0.5)
                else:
                    break
            except Exception as e:
                logger.error(f"获取K线数据时发生错误: {str(e)}")
                break
        logger.info(f"成功获取{len(all_kline_data)}条K线数据: {api_url}")
        return all_kline_data

    def fetch_sections(self, type: str = "BROAD", level: int = 0, 
                      platform: str = "ALL", typeVal: str = "", 
                      typeDay: str = "1") -> List[Dict]:
        """获取板块列表
        
        Args:
            type: 板块类型
            level: 板块级别
            platform: 平台
            typeVal: 类型值
            typeDay: 天数类型
            
        Returns:
            List[Dict]: 板块列表
        """
        try:
            logger.info(f"开始获取板块列表: type={type}, level={level}")
            api_url = f"{self.base_url}/user/item/block/v1/next-level"
            payload = {
                "type": type,
                "level": level,
                "platform": platform,
                "typeVal": typeVal,
                "typeDay": typeDay,
                "timestamp": str(int(time.time() * 1000))
            }
            
            response = requests.post(api_url, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            if data.get('success') and data.get('data'):
                sections = data.get('data', [])
                logger.info(f"成功获取{len(sections)}个板块")
                # 使用logger输出板块信息
                logger.info("获取到的板块列表：")
                for i, section in enumerate(sections, 1):
                    logger.info(f"{i}. {section.get('nameZh', '未知板块')} (ID: {section.get('typeVal', '未知ID')})")
                return sections
            else:
                logger.error(f"获取板块列表失败: {data.get('msg')}")
                return []
                
        except Exception as e:
            logger.error(f"获取板块列表时发生错误: {str(e)}")
            return []

    def save_to_csv(self, data: list, filename: str) -> bool:
        try:
            if not data:
                logger.warning(f"没有数据需要保存: {filename}")
                return False
                
            # 直接按二维数组处理
            df = pd.DataFrame(data, columns=["date", "open", "close", "high", "low", "volume", "amount"])
            df["date"] = pd.to_datetime(df["date"].astype(int), unit="s").dt.strftime("%Y-%m-%d")
            df = df.sort_values("date")  # 按日期升序排序
            filepath = self.output_dir / filename
            df.to_csv(filepath, index=False)
            logger.info(f"成功保存数据到: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"保存数据到CSV时发生错误: {str(e)}")
            return False
