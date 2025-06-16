import requests

class LLMClient:
    def __init__(self, api_url, api_key, model, tools=None, headers=None):
        self.api_url = api_url
        self.api_key = api_key
        self.model = model
        self.tools = tools or []
        self.headers = headers or {"Authorization": f"Bearer {api_key}"}

    def chat(self, messages, stream=False, max_tokens=1024, temperature=0.7, top_p=0.7, **kwargs):
        data = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
        }
        if self.tools:
            data["tools"] = self.tools
        data.update(kwargs)
        resp = requests.post(self.api_url, headers=self.headers, json=data)
        resp.raise_for_status()
        return resp.json() 