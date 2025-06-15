from strategy_base import StrategyBase
import backtrader as bt

class StrategyMomentumDualBroad(StrategyBase):
    """
    基于手套板块（触发）和大盘（目标）相关性的动量策略。
    包含 T+7 交易规则，并增加了止损和止盈。
    """

    params = (
        ('trigger_up_threshold', 0.5),  # 触发板块上涨百分比阈值
        ('trigger_down_threshold', -0.5), # 触发板块下跌百分比阈值 (负值)
        ('holding_days', 7), # 最小持有天数 (T+7 考虑)
        ('stop_loss_pct', 5.0), # 止损百分比 (例如 5.0 表示 5%)
        ('take_profit_pct', 10.0), # 止盈百分比 (例如 10.0 表示 10%)
        ('printlog', True),
    )

    def __init__(self):
        super().__init__()
        # 确保传入了两个数据源
        if len(self.datas) < 2:
            raise ValueError("策略需要至少两个数据源：目标数据和触发数据")

        self.target_data = self.datas[0] # 大盘数据
        self.trigger_data = self.datas[1] # 手套板块数据

        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.bar_executed = None

        # 计算触发板块的涨跌幅
        self.trigger_pct_change = bt.indicators.PctChange(self.trigger_data.close, period=1) * 100

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
                # 计算当前收益率 (相对于买入价格)
                current_return_pct = ((self.target_data.close[0] - self.buyprice) / self.buyprice) * 100

                # 检查是否达到用户定义的持有天数
                if self.holding_since is not None and (current_bar_index - self.holding_since) >= self.p.holding_days:
                    self.log(f'卖出信号 (达到总持有天数 {self.p.holding_days} 天), 当前收益: {current_return_pct:.2f}%, 目标价格: {self.target_data.close[0]:.2f}')
                    self.order = self.close() # 平仓
                # 检查止损
                elif self.p.stop_loss_pct > 0 and current_return_pct <= -self.p.stop_loss_pct:
                    self.log(f'卖出信号 (止损触发, 收益: {current_return_pct:.2f}%), 目标价格: {self.target_data.close[0]:.2f}')
                    self.order = self.close() # 平仓
                # 检查止盈
                elif self.p.take_profit_pct > 0 and current_return_pct >= self.p.take_profit_pct:
                    self.log(f'卖出信号 (止盈触发, 收益: {current_return_pct:.2f}%), 目标价格: {self.target_data.close[0]:.2f}')
                    self.order = self.close() # 平仓
                # 或者如果触发板块下跌达到阈值，也可以考虑卖出（作为额外的平仓条件，而不是止损）
                elif current_trigger_pct_change <= self.p.trigger_down_threshold:
                    self.log(f'卖出信号 (触发板块下跌 {current_trigger_pct_change:.2f}%, 目标价格: {self.target_data.close[0]:.2f}')
                    self.order = self.close() # 平仓 