from langchain.tools import Tool
from src.tools.data_tools import get_all_market_names, read_market_data, find_csv_file
from src.tools.analysis_tools import get_market_trend_prompt
from src.tools.visualiza import plot_kline
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
    csv_path = find_csv_file(market_name)
    if not csv_path:
        return {"analysis": f"未找到{market_name}的数据文件。", "image_path": None}

    df = read_market_data(market_name, num_days=730)
    if df is None:
        return {"analysis": f"读取{market_name}的数据文件失败。", "image_path": None}

    plot_dir = "./plot/kline"
    os.makedirs(plot_dir, exist_ok=True)
    image_filename = f"{market_name}_kline.png"
    image_path = os.path.join(plot_dir, image_filename)
    try:
        plot_kline(csv_path, save_path=image_path, title=f"{market_name} K线图")
    except Exception as e:
        return {"analysis": f"生成K线图时发生错误: {str(e)}", "image_path": None}

    prompt = get_market_trend_prompt(df, market_name)
    result = llm.chat([{"role": "user", "content": prompt}])
    analysis_text = result["choices"][0]["message"]["content"]
    
    return {"analysis": analysis_text, "image_path": image_path} 