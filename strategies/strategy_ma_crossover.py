from strategy_base import StrategyBase
import backtrader as bt

class StrategyMACrossover(StrategyBase):
    """
    均线交叉策略：当快线（SMA）上穿慢线（SMA）时买入，下穿时卖出。
    继承 StrategyBase，并考虑 T+7 交易规则。
    """
    params = (
        ('fast_length', 10), # 快速均线周期
        ('slow_length', 30), # 慢速均线周期
        ('holding_days', 7), # 最小持有天数 (T+7 考虑)
        ('printlog', True),
    )

    def __init__(self):
        super().__init__()
        self.dataclose = self.datas[0].close
        self.order = None

        # 创建快线和慢线均线指标
        self.fast_ma = bt.indicators.SMA(self.dataclose, period=self.p.fast_length)
        self.slow_ma = bt.indicators.SMA(self.dataclose, period=self.p.slow_length)

        # 创建交叉指标：1表示快线上穿慢线，-1表示快线下穿慢线
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)

    def next(self):
        # 确保没有待处理订单
        if self.order:
            return

        current_bar_index = len(self) # 当前bar的索引

        # 检查是否持仓
        if not self.position: # 没有持仓，考虑买入
            # 如果快线上穿慢线
            if self.crossover[0] > 0: # 当前bar快线上穿慢线
                self.log(f'买入信号 (快线上穿慢线), 价格: {self.dataclose[0]:.2f}')
                self.order = self.buy()
        else: # 有持仓，考虑卖出
            # 首先检查是否满足 T+7 规则
            if self.can_sell_on_bar is not None and current_bar_index < self.can_sell_on_bar:
                # 未达到T+7，不能卖出
                return

            # 如果已满足 T+7 规则，则检查平仓条件
            # 如果快线下穿慢线
            if self.crossover[0] < 0: # 当前bar快线下穿慢线
                self.log(f'卖出信号 (快线下穿慢线), 价格: {self.dataclose[0]:.2f}')
                self.order = self.close() # 平仓 