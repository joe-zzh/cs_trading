import os
import chainlit as cl
from dotenv import load_dotenv
import yaml
from src.utils.llm_client import LLMClient
from src.agents.trend_agent import analyze_market_trend

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

@cl.on_chat_start
def start_chat():
    cl.user_session.set("message_history", [
        {"role": "system", "content": "你是一个专业的市场分析师，可以分析市场趋势、回答金融相关问题。"}
    ])

@cl.on_message
async def main(message: cl.Message):
    user_input = message.content
    message_history = cl.user_session.get("message_history")

    # 简单关键词判断，自动调用本地分析
    if ("分析" in user_input) and ("大盘" in user_input or "板块" in user_input):
        # 提取市场名，默认支持"分析大盘"或"分析XX板块"
        if "大盘" in user_input:
            market_name = "大盘"
        else:
            # 尝试提取"XX板块"
            import re
            match = re.search(r"分析(.+?)板块", user_input)
            market_name = match.group(1) + "板块" if match else "板块"
        answer = analyze_market_trend(market_name)
    else:
        message_history.append({"role": "user", "content": user_input})
        result = llm.chat(message_history)
        answer = result["choices"][0]["message"]["content"]
        message_history.append({"role": "assistant", "content": answer})

    await cl.Message(content=answer).send() 