import backtrader as bt
import backtrader.analyzers as btanalyzers

class StrategyBase(bt.Strategy):
    """
    所有策略的基类，提供通用功能：
    - 参数定义
    - 日志记录
    - 订单/交易通知
    - T+7 市场规则处理
    """
    params = (
        ('printlog', True),
        ('commission', 0.001), # 默认佣金
        ('initial_cash', 100000.0), # 默认初始资金
    )

    def log(self, txt, dt=None):
        """记录策略日志"""
        dt = dt or self.datas[0].datetime.date(0)
        if self.p.printlog:
            print(f'{dt.isoformat()}, {txt}')

    def notify_order(self, order):
        """处理订单通知"""
        if order.status in [order.Submitted, order.Accepted]:
            # 订单已提交/接受，无需处理
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
        """处理交易通知"""
        if not trade.isclosed:
            return
        self.log(f'交易利润, 毛利 {trade.pnl:.2f}, 净利 {trade.pnlcomm:.2f}')

    def __init__(self):
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.bar_executed = None
        self.holding_since = None # 记录持仓开始的bar索引
        self.can_sell_on_bar = None # 记录最早可以卖出的bar索引

    def next(self):
        # 基础策略不包含交易逻辑，由子类实现
        pass

    def start(self):
        # 在回测开始时打印初始资金
        self.log(f'初始资金: {self.broker.getcash():.2f}')

    def stop(self):
        # 在回测结束时打印最终资金
        self.log(f'最终资金: {self.broker.getvalue():.2f}') 