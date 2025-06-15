import pandas as pd
import backtrader as bt
import backtrader.analyzers as btanalyzers
import os
import datetime
import matplotlib.pyplot as plt

# 配置 matplotlib 以支持中文显示
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

class DualBroadStrategy(bt.Strategy):
    params = (
        ('trigger_up_threshold', 0.5), # 触发板块上涨阈值 (%)
        ('trigger_down_threshold', -0.5), # 触发板块下跌阈值 (%)
        ('holding_days', 1), # 持有天数
        ('printlog', False)
    )

    def __init__(self):
        # 主数据 (目标板块)
        self.target_data = self.datas[0]
        # 信号数据 (触发板块)
        self.trigger_data = self.datas[1]

        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.holding_since = None # 记录持仓开始的日期
        self.can_sell_on_bar = None # 记录最早可以卖出的bar索引

        # 计算触发板块的涨跌幅
        self.trigger_pct_change = bt.ind.PctChange(self.trigger_data.close, period=1) * 100

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        if self.p.printlog:
            print(f'{dt.isoformat()}, {txt}')

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f'买入执行, 价格: {order.executed.price:.2f}, 成本: {order.executed.value:.2f}, 佣金: {order.executed.comm:.2f}'
                )
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
                self.holding_since = len(self) # 记录买入时的bar索引
                # T+7 规则：购买后第8天才能出售。如果购买在第X天（len(self)=X），则在第X+7天可以卖出。
                # 因此，最早可以卖出的bar索引是当前bar索引 + 7
                self.can_sell_on_bar = len(self) + 7 
            elif order.issell():
                self.log(
                    f'卖出执行, 价格: {order.executed.price:.2f}, 成本: {order.executed.value:.2f}, 佣金: {order.executed.comm:.2f}'
                )
                self.holding_since = None
                self.can_sell_on_bar = None
            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('订单取消/保证金不足/拒绝')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log(f'交易利润, 毛利 {trade.pnl:.2f}, 净利 {trade.pnlcomm:.2f}')

    def next(self):
        # 确保没有待处理订单
        if self.order:
            return

        # 确保数据有足够的历史数据来计算涨跌幅
        if len(self.trigger_data) > 1 and len(self.target_data) > 0:
            current_trigger_pct_change = self.trigger_pct_change[0]
            current_bar_index = len(self) # 当前bar的索引

            # 检查是否持仓
            if not self.position: # 没有持仓，考虑买入
                # 如果触发板块上涨达到阈值
                if current_trigger_pct_change >= self.p.trigger_up_threshold:
                    self.log(f'买入信号 (触发板块上涨 {current_trigger_pct_change:.2f}%), 目标价格: {self.target_data.close[0]:.2f}')
                    self.order = self.buy()
            else: # 有持仓，考虑卖出（止盈/止损或达到持有天数）
                # 首先检查是否满足 T+7 规则
                if self.can_sell_on_bar is not None and current_bar_index < self.can_sell_on_bar:
                    # 未达到T+7，不能卖出
                    return

                # 如果已满足 T+7 规则，则检查平仓条件
                # 检查是否达到用户定义的持有天数
                if self.holding_since is not None and (current_bar_index - self.holding_since) >= self.p.holding_days:
                    self.log(f'卖出信号 (达到总持有天数 {self.p.holding_days} 天), 目标价格: {self.target_data.close[0]:.2f}')
                    self.order = self.close() # 平仓
                # 或者如果触发板块下跌达到阈值，也可以考虑卖出（止损）
                elif current_trigger_pct_change <= self.p.trigger_down_threshold:
                    self.log(f'卖出信号 (触发板块下跌 {current_trigger_pct_change:.2f}%), 目标价格: {self.target_data.close[0]:.2f}')
                    self.order = self.close() # 平仓


def run_optimization():
    cerebro = bt.Cerebro(optreturn=False) 

    # Add analyzers to collect metrics
    cerebro.addanalyzer(btanalyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(btanalyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(btanalyzers.Returns, _name='returns', tann=0) # Total returns, not annualized

    # Define optimization ranges
    trigger_up_thresholds = [0.1, 0.5, 1.0, 1.5, 2.0]
    trigger_down_thresholds = [0.1, 0.5, 1.0, 1.5, 2.0]
    # T+7 市场，最小持有天数应为 7，我们优化的是在此基础上的额外持有天数或总持有天数
    # 这里将 holding_days_range 定义为总持有天数，必须 >= 7
    holding_days_range = [7, 8, 10, 15, 20] # 至少持有7天，然后可以尝试更长的持有期

    # Define which broad/block to use for trigger and target
    trigger_block_name = '手套'
    target_block_name = '大盘'

    # Load target data (main data)
    target_filepath = os.path.join('board_data', f'{target_block_name}_kline_data.csv')
    df_target = pd.read_csv(target_filepath, index_col='date', parse_dates=True)
    df_target = df_target[~df_target.index.duplicated(keep='last')]
    df_target.index.name = 'datetime'
    df_target.rename(columns={'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close', 'volume': 'volume'}, inplace=True)
    data_target = bt.feeds.PandasData(dataname=df_target)
    cerebro.adddata(data_target, name=target_block_name)

    # Load trigger data (signal data)
    trigger_filepath = os.path.join('board_data', f'{trigger_block_name}_kline_data.csv')
    df_trigger = pd.read_csv(trigger_filepath, index_col='date', parse_dates=True)
    df_trigger = df_trigger[~df_trigger.index.duplicated(keep='last')]
    df_trigger.index.name = 'datetime'
    df_trigger.rename(columns={'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close', 'volume': 'volume'}, inplace=True)
    data_trigger = bt.feeds.PandasData(dataname=df_trigger)
    cerebro.adddata(data_trigger, name=trigger_block_name)

    # Add strategy for optimization
    strats = cerebro.optstrategy(
        DualBroadStrategy,
        trigger_up_threshold=trigger_up_thresholds,
        trigger_down_threshold=[-t for t in trigger_down_thresholds], # 将下跌阈值转换为负值
        holding_days=holding_days_range
    )

    # Set initial cash and commission
    cerebro.broker.setcash(100000.0)
    cerebro.broker.setcommission(commission=0.001)

    print(f'正在对 {trigger_block_name} 触发 {target_block_name} 的策略进行优化 (T+7 市场规则已考虑)...')
    # Run optimization
    optimized_runs = cerebro.run(maxcpus=1) # Use maxcpus=1 to avoid multiprocessing issues if any

    # Process results
    results_list = []
    for run in optimized_runs:
        for strategy in run:
            sharpe_ratio = strategy.analyzers.sharpe.get_analysis().get('sharperatio', float('nan'))
            max_drawdown = strategy.analyzers.drawdown.get_analysis().get('maxdrawdown', float('nan'))
            total_return = strategy.analyzers.returns.get_analysis().get('rtot', float('nan'))

            results_list.append({
                'Trigger Index': trigger_block_name,
                'Target Index': target_block_name,
                'Trigger Up Threshold (%)': strategy.p.trigger_up_threshold,
                'Trigger Down Threshold (%)': strategy.p.trigger_down_threshold,
                'Holding Days': strategy.p.holding_days,
                'Total Return (%)': total_return * 100,
                'Sharpe Ratio': sharpe_ratio,
                'Max Drawdown (%)': max_drawdown
            })

    # Convert results to DataFrame and sort
    results_df = pd.DataFrame(results_list)
    if not results_df.empty:
        results_df_sorted = results_df.sort_values(by='Total Return (%)', ascending=False).reset_index(drop=True)
        print('\n优化结果 (按总收益率降序排列):')
        print(results_df_sorted)

        output_filename = f'optimization_results_{trigger_block_name}_to_{target_block_name}_T7.csv'
        results_df_sorted.to_csv(output_filename, index=False, encoding='utf-8')
        print(f'\n优化结果已保存到 {output_filename}')
    else:
        print('没有生成任何优化结果。')

if __name__ == '__main__':
    run_optimization() 