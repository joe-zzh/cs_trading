from strategy_base import StrategyBase
import backtrader as bt

class StrategyRSIBollinger(StrategyBase):
    """
    RSI和布林带策略：
    - RSI低于超卖线且价格低于布林带下轨时买入。
    - RSI高于超买线或价格高于布林带上轨时卖出。
    继承 StrategyBase，并考虑 T+7 交易规则。
    """
    params = (
        ('rsi_period', 14),
        ('bb_period', 20),
        ('bb_dev', 2),
        ('oversold', 30),
        ('overbought', 70),
        ('holding_days', 7), # 最小持有天数 (T+7 考虑)
        ('printlog', True),
    )

    def __init__(self):
        super().__init__()
        self.dataclose = self.datas[0].close
        self.order = None

        # 创建RSI指标
        self.rsi = bt.indicators.RSI(self.dataclose, period=self.p.rsi_period)

        # 创建布林带指标
        self.bbands = bt.indicators.BollingerBands(
            self.dataclose, period=self.p.bb_period, devfactor=self.p.bb_dev
        )

    def next(self):
        # 确保没有待处理订单
        if self.order:
            return

        current_bar_index = len(self) # 当前bar的索引

        # 检查是否持仓
        if not self.position: # 没有持仓，考虑买入
            # 如果RSI低于超卖线 并且 价格低于布林带下轨
            if self.rsi[0] < self.p.oversold and self.dataclose[0] <= self.bbands.lines.bot[0]:
                self.log(f'买入信号 (RSI超卖 & 价格低于布林带下轨), 价格: {self.dataclose[0]:.2f}')
                self.order = self.buy()
        else: # 有持仓，考虑卖出
            # 首先检查是否满足 T+7 规则
            if self.can_sell_on_bar is not None and current_bar_index < self.can_sell_on_bar:
                # 未达到T+7，不能卖出
                return

            # 如果已满足 T+7 规则，则检查平仓条件
            # 如果RSI高于超买线 或者 价格高于布林带上轨
            if self.rsi[0] > self.p.overbought or self.dataclose[0] >= self.bbands.lines.top[0]:
                self.log(f'卖出信号 (RSI超买 或 价格高于布林带上轨), 价格: {self.dataclose[0]:.2f}')
                self.order = self.close() # 平仓 