import pandas as pd
import backtrader as bt
import os
import matplotlib.pyplot as plt

# 配置 matplotlib 以支持中文显示
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei'] # 替换为你的系统上已安装的中文字体
plt.rcParams['axes.unicode_minus'] = False # 解决负号显示问题

class HandBoardStrategy(bt.Strategy):
    """
    策略：如果手套板块上涨，就购买大盘；如果手套板块下跌，就卖出大盘。
    """
    params = (
        ('hand_up_threshold', 0.005),   # 手套板块上涨阈值 (0.5%)
        ('hand_down_threshold', -0.005), # 手套板块下跌阈值 (-0.5%)
        ('printlog', True)              # 是否打印日志
    )

    def __init__(self):
        # 主数据（大盘）
        self.broad_data = self.datas[0]
        # 信号数据（手套板块）
        self.hand_data = self.datas[1]

        self.order = None  # 追踪待处理的订单
        self.buyprice = None
        self.buycomm = None

    def log(self, txt, dt=None):
        """记录策略日志"""
        dt = dt or self.datas[0].datetime.date(0)
        if self.p.printlog:
            print(f'{dt.isoformat()}, {txt}')

    def notify_order(self, order):
        """订单状态通知"""
        if order.status in [order.Submitted, order.Accepted]:
            # 订单已提交/接受，无需操作
            return

        # 订单已完成
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f'买入执行, 价格: {order.executed.price:.2f}, 成本: {order.executed.value:.2f}, 佣金: {order.executed.comm:.2f}'
                )
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            elif order.issell():
                self.log(
                    f'卖出执行, 价格: {order.executed.price:.2f}, 成本: {order.executed.value:.2f}, 佣金: {order.executed.comm:.2f}'
                )
            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('订单取消/保证金不足/拒绝')

        self.order = None # 清除待处理订单

    def notify_trade(self, trade):
        """交易状态通知"""
        if not trade.isclosed:
            return
        self.log(f'交易利润, 毛利 {trade.pnl:.2f}, 净利 {trade.pnlcomm:.2f}')

    def next(self):
        """策略核心逻辑"""
        # 确保没有待处理订单
        if self.order:
            return

        # 确保手套板块数据有足够的历史数据来计算涨跌幅
        if len(self.hand_data) > 1:
            current_hand_close = self.hand_data.close[0]
            prev_hand_close = self.hand_data.close[-1]

            hand_pct_change = 0
            if prev_hand_close != 0:
                hand_pct_change = (current_hand_close - prev_hand_close) / prev_hand_close

            # 如果手套板块上涨
            if hand_pct_change > self.p.hand_up_threshold:
                if not self.position:  # 如果没有持仓
                    self.log(f'买入信号, 大盘价格: {self.broad_data.close[0]:.2f}, 手套涨幅: {hand_pct_change:.4f}')
                    self.order = self.buy() # 买入大盘

            # 如果手套板块下跌
            elif hand_pct_change < self.p.hand_down_threshold:
                if self.position:  # 如果有持仓
                    self.log(f'卖出信号, 大盘价格: {self.broad_data.close[0]:.2f}, 手套涨幅: {hand_pct_change:.4f}')
                    self.order = self.sell() # 卖出大盘

def run_backtest():
    cerebro = bt.Cerebro()

    # 添加策略
    cerebro.addstrategy(HandBoardStrategy)

    # 加载大盘数据
    broad_filepath = os.path.join('board_data', '大盘_kline_data.csv')
    df_broad = pd.read_csv(broad_filepath, index_col='date', parse_dates=True)
    # 重命名列以符合 backtrader 的预期
    df_broad.index.name = 'datetime'
    df_broad.rename(columns={'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close', 'volume': 'volume'}, inplace=True)
    data_broad = bt.feeds.PandasData(dataname=df_broad)
    cerebro.adddata(data_broad, name='大盘')

    # 加载手套板块数据
    hand_filepath = os.path.join('board_data', '手套_kline_data.csv')
    df_hand = pd.read_csv(hand_filepath, index_col='date', parse_dates=True)
    # 重命名列以符合 backtrader 的预期
    df_hand.index.name = 'datetime'
    df_hand.rename(columns={'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close', 'volume': 'volume'}, inplace=True)
    data_hand = bt.feeds.PandasData(dataname=df_hand)
    cerebro.adddata(data_hand, name='手套') # 作为辅助数据

    # 设置初始资金
    cerebro.broker.setcash(100000.0)

    # 设置佣金 (例如，千分之一)
    cerebro.broker.setcommission(commission=0.001)

    # 打印开始时的资金
    print(f'初始资金: {cerebro.broker.getvalue():.2f}')

    # 运行回测
    cerebro.run()

    # 打印最终资金
    print(f'最终资金: {cerebro.broker.getvalue():.2f}')

    # 绘制结果
    print('正在绘制回测结果...')
    fig = cerebro.plot(style='candlestick', volume=True, figscale=1.5)
    # 保存图表为图片文件
    fig[0][0].savefig('backtest_result.png', dpi=300) # 将图表保存为PNG文件
    plt.show() # 显示图表

if __name__ == '__main__':
    run_backtest() 