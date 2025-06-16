def get_market_trend_prompt(df, market_name):
    recent = df.tail(30)
    csv_str = recent.to_csv(index=False)
    prompt = f"""以下是{market_name}最近30天的K线数据（date, open, close, high, low, volume, amount）：\n{csv_str}\n请用中文分析该市场的趋势，并给出简要展望。"""
    return prompt 