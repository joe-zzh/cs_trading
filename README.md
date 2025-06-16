# K线数据获取工具

这是一个用于获取K线数据的Python工具，支持获取所有板块的K线数据，并支持增量更新。

## 功能特点

- 支持获取所有板块的K线数据
- 支持增量更新最新数据
- 数据保存为CSV格式
- 完整的日志记录
- 配置文件管理

## 项目结构

```
.
├── config/             # 配置文件目录
│   └── config.yaml    # 主配置文件
├── data/              # 数据目录
│   ├── raw/          # 原始数据
│   └── processed/    # 处理后的数据
├── logs/              # 日志目录
├── scripts/           # 脚本目录
│   └── main.py       # 主入口脚本
├── src/               # 源代码目录
│   ├── data/         # 数据处理相关代码
│   │   ├── fetcher.py
│   │   └── storage.py
│   └── utils/        # 工具函数
│       └── logger.py
├── requirements.txt   # 项目依赖
└── README.md         # 项目说明
```

## 安装

1. 克隆项目到本地
2. 安装依赖：
```bash
pip install -r requirements.txt
```

## 使用方法

1. 配置
   - 编辑 `config/config.yaml` 文件，设置必要的配置项

2. 运行
   - 获取所有数据：
   ```bash
   python scripts/main.py --mode all
   ```
   - 获取最新数据：
   ```bash
   python scripts/main.py --mode latest
   ```

## 数据格式

CSV文件包含以下字段：
- date: 日期（YYYY-MM-DD格式）
- open: 开盘价
- close: 收盘价
- high: 最高价
- low: 最低价
- volume: 成交量
- amount: 成交额

## 日志

日志文件保存在 `logs/app.log`，记录程序运行过程中的重要信息和错误。 