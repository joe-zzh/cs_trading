from langchain.tools import Tool
from src.tools.data_tools import get_all_market_names, read_market_data
from src.tools.analysis_tools import get_market_trend_prompt
from src.utils.llm_client import LLMClient
import yaml
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("API_KEY")

with open("config/config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)
llm_cfg = config["llm_api"]
llm = LLMClient(
    api_url=llm_cfg["api_url"],
    api_key=api_key,
    model=llm_cfg["model"]
)

def analyze_market_trend(market_name):
    df = read_market_data(market_name)
    if df is None:
        return f"未找到{market_name}的数据文件。"
    prompt = get_market_trend_prompt(df, market_name)
    result = llm.chat([{"role": "user", "content": prompt}])
    return result["choices"][0]["message"]["content"]

tools = [
    Tool(
        name="AnalyzeMarketTrend",
        func=analyze_market_trend,
        description="分析指定市场的趋势"
    )
] 