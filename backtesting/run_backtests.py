import backtrader as bt
import backtrader.analyzers as btanalyzers
import pandas as pd
import os
import matplotlib.pyplot as plt # 导入 matplotlib.pyplot

from strategy_momentum_dual_broad import StrategyMomentumDualBroad
from strategy_ma_crossover import StrategyMACrossover
from strategy_rsi_bollinger import StrategyRSIBollinger

def load_data(file_name, directory='board_data'):
    """加载K线数据"""
    filepath = os.path.join(directory, file_name)
    df = pd.read_csv(filepath, index_col='date', parse_dates=True)
    df = df[~df.index.duplicated(keep='last')] # 去重，保留最新数据
    df.index.name = 'datetime'
    # 确保列名与backtrader期望的一致
    df.rename(columns={'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close', 'volume': 'volume'}, inplace=True)
    return bt.feeds.PandasData(dataname=df)

def run_strategy(strategy_class, data_feeds, strategy_params=None, initial_cash=100000.0, commission=0.001, plot=False, plot_filename=None):
    """运行单个策略的回测并返回结果"""
    cerebro = bt.Cerebro()

    # 设置初始资金和佣金
    cerebro.broker.setcash(initial_cash)
    cerebro.broker.setcommission(commission=commission)

    # 添加数据源
    for data_feed in data_feeds:
        cerebro.adddata(data_feed)

    # 添加策略
    if strategy_params:
        cerebro.addstrategy(strategy_class, **strategy_params)
    else:
        cerebro.addstrategy(strategy_class)

    # 添加分析器
    cerebro.addanalyzer(btanalyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(btanalyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(btanalyzers.Returns, _name='returns', tann=0) # 总收益率，非年化
    cerebro.addanalyzer(btanalyzers.TradeAnalyzer, _name='trade_analyzer') # 交易分析器

    print(f"\n--- 运行策略: {strategy_class.__name__} ---")
    results = cerebro.run()

    # 提取分析结果
    strat = results[0]
    sharpe_ratio = strat.analyzers.sharpe.get_analysis().get('sharperatio', float('nan'))
    max_drawdown = strat.analyzers.drawdown.get_analysis().get('maxdrawdown', float('nan'))
    total_return = strat.analyzers.returns.get_analysis().get('rtot', float('nan')) * 100 # 转换为百分比

    trade_metrics = strat.analyzers.trade_analyzer.get_analysis()
    total_trades = trade_metrics.total.closed if hasattr(trade_metrics, 'total') and hasattr(trade_metrics.total, 'closed') else 0
    win_trades = trade_metrics.won.total if hasattr(trade_metrics, 'won') and hasattr(trade_metrics.won, 'total') else 0
    loss_trades = trade_metrics.lost.total if hasattr(trade_metrics, 'lost') and hasattr(trade_metrics.lost, 'total') else 0
    win_rate = (win_trades / total_trades) * 100 if total_trades > 0 else 0

    final_value = cerebro.broker.getvalue()

    if plot:
        if plot_filename:
            # 将图表保存为文件
            cerebro.plot(style='candlestick', barup='green', bardown='red', figscale=2.0,
                         savefig=True, filename=plot_filename)
            print(f"图表已保存到: {plot_filename}")
        else:
            # 显示图表
            print("正在显示图表...")
            cerebro.plot(style='candlestick', barup='green', bardown='red')

    return {
        'Strategy': strategy_class.__name__,
        'Total Return (%)': total_return,
        'Sharpe Ratio': sharpe_ratio,
        'Max Drawdown (%)': max_drawdown,
        'Final Portfolio Value': final_value,
        'Total Trades': total_trades,
        'Win Trades': win_trades,
        'Loss Trades': loss_trades,
        'Win Rate (%)': win_rate,
        ** (strategy_params if strategy_params else {}), # 将策略参数也包含在结果中
    }

def run_optimization(strategy_class, data_feeds, param_ranges, initial_cash=100000.0, commission=0.001, output_filename='optimization_results.csv'):
    """运行策略的参数优化"""
    cerebro = bt.Cerebro(optreturn=False) # Keep optreturn=False to get full strategy objects for analyzers

    # 设置初始资金和佣金
    cerebro.broker.setcash(initial_cash)
    cerebro.broker.setcommission(commission=commission)

    # 添加数据源
    for data_feed in data_feeds:
        cerebro.adddata(data_feed)

    # 添加策略进行优化
    cerebro.optstrategy(
        strategy_class,
        **param_ranges
    )

    # 添加分析器
    cerebro.addanalyzer(btanalyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(btanalyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(btanalyzers.Returns, _name='returns', tann=0)
    cerebro.addanalyzer(btanalyzers.TradeAnalyzer, _name='trade_analyzer')

    print(f"\n--- 正在对策略: {strategy_class.__name__} 进行参数优化 ---")
    optimized_runs = cerebro.run(maxcpus=1) # Use maxcpus=1 to avoid multiprocessing issues if any

    results_list = []
    for run in optimized_runs:
        for strategy in run:
            sharpe_ratio = strategy.analyzers.sharpe.get_analysis().get('sharperatio', float('nan'))
            max_drawdown = strategy.analyzers.drawdown.get_analysis().get('maxdrawdown', float('nan'))
            total_return = strategy.analyzers.returns.get_analysis().get('rtot', float('nan')) * 100

            trade_metrics = strategy.analyzers.trade_analyzer.get_analysis()
            total_trades = trade_metrics.total.closed if hasattr(trade_metrics, 'total') and hasattr(trade_metrics.total, 'closed') else 0
            win_trades = trade_metrics.won.total if hasattr(trade_metrics, 'won') and hasattr(trade_metrics.won, 'total') else 0
            loss_trades = trade_metrics.lost.total if hasattr(trade_metrics, 'lost') and hasattr(trade_metrics.lost, 'total') else 0
            win_rate = (win_trades / total_trades) * 100 if total_trades > 0 else 0

            # 获取策略参数
            params_dict = {key: getattr(strategy.p, key) for key in strategy.p._getkwargs()} # 获取所有参数

            results_list.append({
                'Strategy': strategy_class.__name__,
                'Total Return (%)': total_return,
                'Sharpe Ratio': sharpe_ratio,
                'Max Drawdown (%)': max_drawdown,
                'Total Trades': total_trades,
                'Win Trades': win_trades,
                'Loss Trades': loss_trades,
                'Win Rate (%)': win_rate,
                **params_dict
            })

    results_df = pd.DataFrame(results_list)
    if not results_df.empty:
        results_df_sorted = results_df.sort_values(by='Total Return (%)', ascending=False).reset_index(drop=True)
        print('\n优化结果 (按总收益率降序排列):')
        print(results_df_sorted.to_string())

        results_df_sorted.to_csv(output_filename, index=False, encoding='utf-8')
        print(f'\n优化结果已保存到 {output_filename}')
    else:
        print('没有生成任何优化结果。')

if __name__ == '__main__':
    # 初始资金和佣金 (所有策略共享)
    initial_cash = 100000.0
    commission = 0.001

    # 加载数据
    broad_data = load_data('大盘_kline_data.csv')
    gloves_data = load_data('手套_kline_data.csv')

    # --- 为 StrategyMomentumDualBroad 进行参数优化 --- 
    momentum_dual_broad_param_ranges = {
        'trigger_up_threshold': [0.1, 0.5, 1.0, 1.5, 2.0],
        'trigger_down_threshold': [-0.1, -0.5, -1.0, -1.5, -2.0],
        'stop_loss_pct': [3.0, 5.0, 7.0, 10.0],
        'take_profit_pct': [5.0, 10.0, 15.0, 20.0],
        'holding_days': [7, 10, 15, 20],
        'printlog': False,
    }

    run_optimization(
        StrategyMomentumDualBroad,
        data_feeds=[broad_data, gloves_data],
        param_ranges=momentum_dual_broad_param_ranges,
        initial_cash=initial_cash,
        commission=commission,
        output_filename='optimization_results_momentum_dual_broad.csv'
    )

    # --- 运行 StrategyMACrossover --- 
    # 复制 broad_data，因为 bt.Cerebro 会消耗数据
    ma_crossover_data = load_data('大盘_kline_data.csv')
    ma_crossover_params = {
        'fast_length': 10,
        'slow_length': 30,
        'holding_days': 7,
        'printlog': False,
    }
    results_ma = run_strategy(
        StrategyMACrossover,
        data_feeds=[ma_crossover_data],
        strategy_params=ma_crossover_params,
        initial_cash=initial_cash,
        commission=commission,
        plot=False # 不绘制其他策略的图表，避免中断
    )

    # --- 运行 StrategyRSIBollinger --- 
    # 复制 broad_data
    rsi_bollinger_data = load_data('大盘_kline_data.csv')
    rsi_bollinger_params = {
        'rsi_period': 14,
        'bb_period': 20,
        'bb_dev': 2,
        'oversold': 30,
        'overbought': 70,
        'holding_days': 7,
        'printlog': False,
    }
    results_rsi_bb = run_strategy(
        StrategyRSIBollinger,
        data_feeds=[rsi_bollinger_data],
        strategy_params=rsi_bollinger_params,
        initial_cash=initial_cash,
        commission=commission,
        plot=False
    )

    # --- 打印所有策略的汇总结果 --- 
    print("\n--- 所有策略汇总结果 ---")
    results_df = pd.DataFrame([results_ma, results_rsi_bb])
    # 重新排序和选择列，使输出更整洁
    display_columns = [
        'Strategy',
        'Total Return (%)',
        'Sharpe Ratio',
        'Max Drawdown (%)',
        'Final Portfolio Value',
        'Total Trades',
        'Win Trades',
        'Loss Trades',
        'Win Rate (%)',
    ]
    # 添加策略特有参数
    for param in ['fast_length', 'slow_length', 'rsi_period', 'bb_period', 'bb_dev', 'oversold', 'overbought']:
        if param in results_df.columns:
            display_columns.append(param)

    print(results_df[list(dict.fromkeys(display_columns))].sort_values(by='Total Return (%)', ascending=False).to_string())

    # 保存汇总结果到CSV
    output_filename = 'all_strategies_summary.csv'
    results_df.to_csv(output_filename, index=False, encoding='utf-8')
    print(f'\n所有策略汇总结果已保存到 {output_filename}') 