import http.client
import json
from datetime import datetime
import os

def get_base_info(api_key, save_dir="data"):
    conn = http.client.HTTPSConnection("open.steamdt.com")
    
    # 准备请求头，添加认证信息
    headers = {
        'Authorization': f'Bearer {api_key}'
    }
    
    # 发送GET请求
    conn.request("GET", "/open/cs2/v1/base", "", headers)
    
    # 获取响应
    response = conn.getresponse()
    data = response.read()
    
    # 解码响应数据
    result = data.decode("utf-8")
    
    # 确保保存目录存在
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    # 生成文件名（使用当前时间戳）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(save_dir, f"base_info_{timestamp}.json")
    
    # 保存到文件
    try:
        # 尝试格式化JSON数据
        json_data = json.loads(result)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        print(f"数据已保存到文件: {filename}")
    except json.JSONDecodeError:
        # 如果不是JSON格式，直接保存原始数据
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(result)
        print(f"原始数据已保存到文件: {filename}")
    
    # 打印响应结果
    print("API返回结果:")
    print(result)
    
    # 关闭连接
    conn.close()

# 使用示例
if __name__ == "__main__":
    # 替换为你的API密钥
    API_KEY = "0b029273163946acabfb91980eba63e8"
    
    # 设置保存路径（可以是相对路径或绝对路径）
    SAVE_DIR = "base_info"  # 默认保存在当前目录下的data文件夹中
    # SAVE_DIR = "C:/Users/YourName/Documents/steam_data"  # 使用绝对路径
    
    get_base_info(API_KEY, SAVE_DIR) 