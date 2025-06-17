import os
import chainlit as cl
from dotenv import load_dotenv
import yaml
from src.utils.llm_client import LLMClient
from src.agents.trend_agent import analyze_market_trend
from src.tools.compare_analyzer import compare_market_trends
from src.agents.tools_registry import get_tools
from langchain.agents import initialize_agent, AgentType
from langchain.chat_models import ChatOpenAI

load_dotenv()
api_key = os.getenv("API_KEY")
# 读取配置
with open("config/config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)
llm_cfg = config["llm_api"]

# 初始化LLM和工具
llm = ChatOpenAI(temperature=0, model=llm_cfg["model"])
tools = get_tools()

# 初始化Agent
agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

@cl.on_chat_start
def start_chat():
    cl.user_session.set("message_history", [
        {"role": "system", "content": "你是一个专业的市场分析师，可以分析市场趋势、回答金融相关问题。"}
    ])

@cl.on_message
async def main(message: cl.Message):
    user_input = message.content
    # 由Agent自动选择工具并应答
    try:
        response = agent.run(user_input)
        await cl.Message(content=response).send()
    except Exception as e:
        await cl.Message(content=f"出错: {e}").send() 