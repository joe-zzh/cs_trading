import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import openai  # 或其他大模型API
import os
from typing import List, Dict, Any

class TrendAnalyzer:
    def __init__(self, api_key: str = None):
        """初始化趋势分析器
        
        Args:
            api_key: 大模型API密钥，如果为None则从环境变量获取
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("需要提供API密钥")
        
        # 初始化API客户端
        openai.api_key = self.api_key

    def _prepare_data_summary(self, df: pd.DataFrame) -> str:
        """准备数据摘要供大模型分析
        
        Args:
            df: K线数据DataFrame
            
        Returns:
            str: 数据摘要文本
        """
        # 计算基本统计信息
        latest_date = df['date'].max()
        latest_close = df.iloc[-1]['close']
        prev_close = df.iloc[-2]['close']
        change_pct = (latest_close - prev_close) / prev_close * 100
        
        # 计算移动平均
        ma5 = df['close'].rolling(5).mean().iloc[-1]
        ma10 = df['close'].rolling(10).mean().iloc[-1]
        ma20 = df['close'].rolling(20).mean().iloc[-1]
        
        # 计算成交量变化
        volume_ma5 = df['volume'].rolling(5).mean().iloc[-1]
        latest_volume = df['volume'].iloc[-1]
        volume_change = (latest_volume - volume_ma5) / volume_ma5 * 100
        
        # 生成数据摘要
        summary = f"""
        数据统计摘要：
        最新日期：{latest_date}
        最新收盘价：{latest_close:.2f}
        日涨跌幅：{change_pct:.2f}%
        
        技术指标：
        5日均线：{ma5:.2f}
        10日均线：{ma10:.2f}
        20日均线：{ma20:.2f}
        
        成交量分析：
        最新成交量：{latest_volume}
        5日平均成交量：{volume_ma5:.2f}
        成交量变化：{volume_change:.2f}%
        """
        return summary

    def analyze_trend(self, 
                     df: pd.DataFrame, 
                     index_name: str,
                     days: int = 30) -> Dict[str, Any]:
        """分析指数趋势
        
        Args:
            df: K线数据DataFrame
            index_name: 指数名称
            days: 预测未来天数
            
        Returns:
            Dict: 包含分析结果的字典
        """
        # 准备数据摘要
        data_summary = self._prepare_data_summary(df)
        
        # 构建提示词
        prompt = f"""
        你是一个专业的市场分析师，请基于以下数据对{index_name}的未来{days}天趋势进行分析：

        {data_summary}

        请从以下几个方面进行分析：
        1. 短期趋势（1-7天）
        2. 中期趋势（8-30天）
        3. 关键支撑位和压力位
        4. 风险提示
        5. 投资建议

        请用专业但易懂的语言进行分析。
        """
        
        try:
            # 调用大模型API
            response = openai.ChatCompletion.create(
                model="gpt-4",  # 或其他适合的模型
                messages=[
                    {"role": "system", "content": "你是一个专业的市场分析师，擅长技术分析和趋势判断。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            analysis = response.choices[0].message.content
            
            return {
                "index_name": index_name,
                "analysis_date": datetime.now().strftime("%Y-%m-%d"),
                "analysis": analysis,
                "data_summary": data_summary
            }
            
        except Exception as e:
            return {
                "error": f"分析过程中出现错误: {str(e)}",
                "index_name": index_name,
                "analysis_date": datetime.now().strftime("%Y-%m-%d")
            }

    def batch_analyze(self, 
                     data_dir: str = "data/index",
                     days: int = 30) -> List[Dict[str, Any]]:
        """批量分析多个指数的趋势
        
        Args:
            data_dir: 数据目录
            days: 预测未来天数
            
        Returns:
            List[Dict]: 分析结果列表
        """
        results = []
        
        # 遍历数据目录下的所有CSV文件
        for file in os.listdir(data_dir):
            if file.endswith('.csv'):
                index_name = file.replace('.csv', '')
                file_path = os.path.join(data_dir, file)
                
                try:
                    # 读取数据
                    df = pd.read_csv(file_path)
                    df['date'] = pd.to_datetime(df['date'])
                    
                    # 分析趋势
                    result = self.analyze_trend(df, index_name, days)
                    results.append(result)
                    
                except Exception as e:
                    print(f"处理{index_name}时出错: {str(e)}")
                    continue
        
        return results

def main():
    # 使用示例
    analyzer = TrendAnalyzer()
    
    # 分析单个指数
    df = pd.read_csv("data/index/百战指数.csv")
    df['date'] = pd.to_datetime(df['date'])
    result = analyzer.analyze_trend(df, "百战指数")
    print(result['analysis'])
    
    # 批量分析所有指数
    results = analyzer.batch_analyze()
    for result in results:
        print(f"\n{result['index_name']}分析结果:")
        print(result['analysis'])

def get_market_trend_prompt(df, market_name):
    # 只取最近30天
    recent = df.tail(30)
    csv_str = recent.to_csv(index=False)
    prompt = f"""以下是{market_name}最近30天的K线数据（date, open, close, high, low, volume, amount）：
{csv_str}
请用中文分析该市场的趋势，并给出简要展望。"""
    return prompt

if __name__ == "__main__":
    main()
