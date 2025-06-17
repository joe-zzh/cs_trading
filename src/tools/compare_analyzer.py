import pandas as pd
import os
from typing import List, Dict, Any
from src.tools.data_tools import read_market_data
from src.utils.llm_client import LLMClient
import yaml
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("API_KEY")
# 读取配置
with open("config/config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)
llm_cfg = config["llm_api"]

llm = LLMClient(
    api_url=llm_cfg["api_url"],
    api_key=api_key,
    model=llm_cfg["model"]
)

def compare_market_trends(market_names: List[str]) -> Dict[str, Any]:
    """对比分析多个市场的趋势。"""
    all_market_data = {}
    for market_name in market_names:
        df = read_market_data(market_name, num_days=730) # 更新为num_days，并设置读取两年数据
        if df is not None and not df.empty:
            all_market_data[market_name] = df
        else:
            print(f"未找到或无法读取 {market_name} 的数据。")

    if len(all_market_data) < 2:
        return {"analysis": "至少需要两个市场才能进行对比分析。", "image_path": None}

    # 准备大模型分析的Prompt
    comparison_prompt_parts = []
    for name, df in all_market_data.items():
        recent_data = df.tail(30) # 仅用最近30天数据生成摘要，避免Prompt过长
        csv_str = recent_data.to_csv(index=False)
        comparison_prompt_parts.append(f"市场名称：{name}\n最近30天K线数据：\n{csv_str}\n")

    full_prompt = """
    你是一个专业的市场分析师，请根据以下提供的多个市场数据，对它们进行对比分析。
    请着重对比它们的近期走势、波动性、成交量变化，并指出它们的异同点，以及未来可能的发展趋势。
    
    以下是各个市场的数据：
    {}

    请用专业且易懂的语言进行分析。
    """.format("\n---\n".join(comparison_prompt_parts))

    try:
        response = llm.chat(
            messages=[
                {"role": "system", "content": "你是一个专业的市场分析师，擅长对比分析不同市场的趋势。"},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.7,
            max_tokens=2000 # 适当增加max_tokens以容纳对比分析内容
        )
        analysis_text = response["choices"][0]["message"]["content"]
        return {"analysis": analysis_text, "image_path": None} # 暂时没有图片
    except Exception as e:
        return {"analysis": f"进行对比分析时发生错误: {str(e)}", "image_path": None} 