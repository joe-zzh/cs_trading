import pandas as pd
import pandas_ta as ta # 导入pandas_ta库

def get_market_trend_prompt(df: pd.DataFrame, market_name: str) -> str:
    """构建包含技术指标的市场趋势分析Prompt"""
    # 确保df有足够的数据计算指标
    if len(df) < 26: # MACD需要至少26天数据
        return f"以下是{market_name}最近{len(df)}天的K线数据（date, open, close, high, low, volume, amount）：\n{df.to_csv(index=False)}\n数据不足，无法进行详细技术分析。请用中文简要分析该市场的趋势，并给出简要展望。"

    # 计算常用技术指标
    # 移动平均线
    df['MA5'] = df.ta.sma(close='close', length=5)
    df['MA10'] = df.ta.sma(close='close', length=10)
    df['MA20'] = df.ta.sma(close='close', length=20)

    # RSI
    df['RSI'] = df.ta.rsi(close='close', length=14)

    # 获取最新一天的指标数据
    # 使用.iloc[-1]获取最后一行，并处理可能存在的NaN值（计算指标初期可能出现）
    latest_data = df.iloc[-1]
    latest_date = latest_data['date'].strftime("%Y-%m-%d")
    latest_close = latest_data['close']
    prev_close = df.iloc[-2]['close'] if len(df) > 1 else latest_close
    change_pct = (latest_close - prev_close) / prev_close * 100 if prev_close != 0 else 0
    latest_volume = latest_data['volume']

    # 获取最近5天的技术指标数据，并格式化为字符串
    # 确保只取有效数据，dropna()处理pandas_ta计算初期的NaNs
    recent_indicator_data = df.tail(5).dropna(subset=['MA5', 'MA10', 'MA20', 'RSI'])
    
    ma_lines = []
    rsi_lines = []

    for index, row in recent_indicator_data.iterrows():
        date_str = row['date'].strftime("%Y-%m-%d")
        ma_lines.append(f"    - {date_str}: MA5={row['MA5']:.2f}, MA10={row['MA10']:.2f}, MA20={row['MA20']:.2f}")
        rsi_lines.append(f"    - {date_str}: RSI={row['RSI']:.2f}")

    ma_summary_str = "\n".join(ma_lines)
    rsi_summary_str = "\n".join(rsi_lines)

    # 生成技术指标摘要
    technical_summary = f"""
市场名称：{market_name}
最新日期：{latest_date}
最新收盘价：{latest_close:.2f}
日涨跌幅：{change_pct:.2f}%
最新成交量：{latest_volume}

技术指标趋势 (近{len(recent_indicator_data)}天)：
均线 (MA):
{ma_summary_str}

RSI (14周期):
{rsi_summary_str}
    """

    # 仅将最近30天的原始K线数据作为参考（避免Prompt过长）
    recent_kline_data_str = df.tail(30)[['date', 'open', 'close', 'high', 'low', 'volume', 'amount']].to_csv(index=False)

    prompt = f"""
    你是一个专业的市场分析师，请基于以下提供的市场基本信息、关键技术指标，以及作为参考的最近30天K线数据，对{market_name}的当前趋势进行详细分析，并给出简要展望。

    {technical_summary}

    参考K线数据 (最近30天)：
    {recent_kline_data_str}

    请从以下几个方面进行分析：
    1. 短期趋势（根据最新价格与短期均线判断）
    2. 中期趋势（根据均线交叉、MACD趋势判断）
    3. 关键支撑位和压力位（可根据历史价格和均线判断）
    4. 风险提示（如市场波动性、成交量变化）
    5. 投资建议（简洁明了）

    请用专业但易懂的中文进行分析，注意逻辑清晰，语言流畅。
    """
    return prompt