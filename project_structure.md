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