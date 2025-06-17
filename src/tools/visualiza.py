import pandas as pd
import mplfinance as mpf
import os

def plot_kline(csv_path, save_path=None, title="K线图"):
    df = pd.read_csv(csv_path)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    df = df[['open', 'high', 'low', 'close', 'volume']]
    if save_path is None:
        save_path = os.path.splitext(csv_path)[0] + "_kline.png"
    mpf.plot(df, type='candle', volume=True, title=title, style='yahoo', savefig=save_path)
    return save_path