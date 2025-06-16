import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
from src.utils.logger import setup_logger

# 创建logger实例
logger = setup_logger("data_storage")

class DataStorage:
    def __init__(self, config: Dict):
        """初始化数据存储器
        
        Args:
            config: 配置信息
        """
        self.config = config
        self.raw_dir = Path(config['data']['output_dir'])
        self.processed_dir = Path(config['data']['processed_dir'])
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("数据存储器初始化完成")

    def load_csv(self, filename: str) -> Optional[pd.DataFrame]:
        """加载CSV文件
        
        Args:
            filename: 文件名
            
        Returns:
            Optional[pd.DataFrame]: 加载的数据，如果失败则返回None
        """
        try:
            filepath = self.raw_dir / filename
            if not filepath.exists():
                logger.warning(f"文件不存在: {filepath}")
                return None
                
            df = pd.read_csv(filepath)
            logger.info(f"成功加载数据: {filepath}")
            return df
            
        except Exception as e:
            logger.error(f"加载CSV文件时发生错误: {str(e)}")
            return None

    def save_processed(self, df: pd.DataFrame, filename: str) -> bool:
        """保存处理后的数据
        
        Args:
            df: 要保存的数据
            filename: 文件名
            
        Returns:
            bool: 是否保存成功
        """
        try:
            if df is None or df.empty:
                logger.warning(f"没有数据需要保存: {filename}")
                return False
                
            filepath = self.processed_dir / filename
            df.to_csv(filepath, index=False)
            logger.info(f"成功保存处理后的数据: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"保存处理后的数据时发生错误: {str(e)}")
            return False

    def append_to_csv(self, df: pd.DataFrame, filename: str) -> bool:
        """追加数据到CSV文件
        
        Args:
            df: 要追加的数据
            filename: 文件名
            
        Returns:
            bool: 是否追加成功
        """
        try:
            if df is None or df.empty:
                logger.warning(f"没有数据需要追加: {filename}")
                return False
                
            filepath = self.raw_dir / filename
            
            # 如果文件存在，读取现有数据
            if filepath.exists():
                existing_df = pd.read_csv(filepath)
                # 合并数据并去重
                df = pd.concat([existing_df, df]).drop_duplicates(subset=['date'])
                # 按日期排序
                df = df.sort_values('date')
            
            # 保存合并后的数据
            df.to_csv(filepath, index=False)
            logger.info(f"成功追加数据到: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"追加数据到CSV时发生错误: {str(e)}")
            return False
