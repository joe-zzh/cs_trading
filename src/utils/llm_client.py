import requests
import json
from openai import OpenAI

# 从 config/config.yaml 加载配置
import yaml

with open("config/config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

llm_config = config["llm_api"]

class LLMClient:
    def __init__(self, api_url, api_key, model, tools=None):
        self.api_url = api_url
        self.api_key = api_key
        self.model = model
        self.tools = tools or []
        self.client = OpenAI(api_key=api_key, base_url=self.api_url)
        print("api_url:", api_url, type(api_url))

    def chat(self, messages, stream=False, max_tokens=1024, temperature=0.7, top_p=0.7, **kwargs):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            stream=stream,
            **kwargs
        )
        if stream:
            return response  # 生成器
        else:
            return response.model_dump()  # 返回dict

    def classify_intent(self, user_query: str) -> dict:
        """使用大模型分类用户意图并提取市场名称，返回字典。"""
        prompt = f"""
        请分析以下用户查询的意图，并提取所有相关的市场名称。
        如果用户要求进行市场分析或比较，请将意图标记为 "market_analysis"，并列出所有相关的市场名称。
        如果用户提出的是一般性问题，请将意图标记为 "general_question"，此时不要包含市场名称。

        请严格按照以下JSON格式返回结果，不要包含任何额外文字或解释：
        {{
          "intent": "<market_analysis|general_question>",
          "market_names": ["<市场名称1>", "<市场名称2>", ...] // 仅当intent为market_analysis时包含
        }}

        例如：

        用户查询: "分析一下大盘走势"
        {{
          "intent": "market_analysis",
          "market_names": ["大盘"]
        }}

        用户查询: "对比一下手枪和步枪的趋势"
        {{
          "intent": "market_analysis",
          "market_names": ["手枪", "步枪"]
        }}

        用户查询: "你好，最近CS饰品市场怎么样？"
        {{
          "intent": "general_question"
        }}

        用户查询: "{user_query}"
        """

        messages = [
            {"role": "system", "content": "你是一个意图识别专家，能够准确判断用户查询的意图，并提取相关实体。"},
            {"role": "user", "content": prompt}
        ]
        try:
            response = self.chat(messages, max_tokens=100, temperature=0.0)
            text_response = response["choices"][0]["message"]["content"].strip()
            
            # 尝试解析JSON
            try:
                parsed_response = json.loads(text_response)
                if "intent" in parsed_response:
                    return parsed_response
            except json.JSONDecodeError:
                print(f"LLM返回的不是有效JSON: {text_response}")
                
            # 如果JSON解析失败，尝试回退到旧的字符串解析方式，或直接返回默认
            if text_response.startswith("意图:"):
                intent = text_response.split(":", 1)[1].strip()
                if intent in ["market_analysis", "general_question"]:
                    return {"intent": intent, "market_names": []}

            return {"intent": "general_question", "market_names": []} # 默认 fallback

        except Exception as e:
            print(f"意图识别失败: {e}")
            return {"intent": "general_question", "market_names": []} # 失败时也默认 fallback