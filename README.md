# CS饰品量化投研AI助手 & K线数据获取工具

这是一个集成了K线数据抓取、AI趋势分析、对话式前端的量化投研AI助手项目，支持本地数据的智能分析与自然语言交互。

## 功能特点

- 支持递归抓取所有板块及子板块的K线数据，分级存储为CSV
- 支持增量更新最新数据
- 集成大模型API，自动生成市场趋势分析
- Chainlit现代化对话前端，支持自然语言提问
- 市场名模糊匹配与智能感知，用户表述不清也能自动查找数据
- 多轮对话与专业金融问答
- 配置与敏感信息分离，安全可靠
- 完整的日志记录

## 项目结构

```
.
├── config/             # 配置文件目录
│   └── config.yaml    # 主配置文件
├── data/              # 数据目录（K线CSV等）
├── logs/              # 日志目录
├── scripts/           # 数据抓取脚本
│   └── main.py       # 主入口脚本
├── src/               # 源代码目录
│   ├── agents/       # 智能体与分析工具
│   ├── tools/        # 数据与分析工具
│   └── utils/        # 通用工具
├── frontend/          # Chainlit前端入口
│   └── chainlit_app.py
├── requirements.txt   # 项目依赖
├── .env               # 环境变量（API_KEY等，需自行创建）
└── README.md         # 项目说明
```

## 安装

1. 克隆项目到本地
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 配置 `.env` 文件，内容示例：
   ```
   API_KEY=你的大模型API密钥
   ```
4. 配置 `config/config.yaml`，设置大模型API地址、模型名等参数。

## 数据抓取用法

- 获取所有数据：
  ```bash
  python scripts/main.py --mode all
  ```
- 仅更新最新数据：(已经获取全部数据后使用)
  ```bash
  python scripts/main.py --mode latest
  ```

## AI助手与前端用法

1. 启动Chainlit前端：
   ```bash
   chainlit run frontend/chainlit_app.py
   ```
2. 浏览器访问 http://localhost:8000
3. 在输入框输入你的问题，如：
   - "请分析大盘走势"
   - "帮我解读XX板块的近期趋势"
4. AI助手会自动模糊匹配市场名，查找本地数据并返回专业分析。(未实现)

## 数据格式

CSV文件包含以下字段：
- date: 日期（YYYY-MM-DD格式）
- open: 开盘价
- close: 收盘价
- high: 最高价
- low: 最低价
- volume: 成交量
- amount: 成交额
