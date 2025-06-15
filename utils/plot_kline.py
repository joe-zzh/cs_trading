import pandas as pd
import os
from pyecharts.charts import Kline, Line, Bar, Grid
from pyecharts import options as opts
from pyecharts.commons.utils import JsCode

class StockKlineChart:
    def __init__(self, df: pd.DataFrame, stock_code: str):
        """
        初始化 K 线图表对象
        :param df: 股票数据 DataFrame（包含"日期"，"开盘"，"收盘"，"最低"，"最高"，"成交量"）
        :param stock_code: 股票代码
        """
        self.df = df.sort_values("日期")  # 按日期排序，确保数据按时间顺序排列
        self.stock_code = stock_code  # 股票代码
        self.color_up = "#ef232a"# 阳线（上涨）颜色
        self.color_down = "#14b143"# 阴线（下跌）颜色
        self.ma_periods = [5, 10, 20]  # 移动平均线周期
        self.ma_colors = {5: "#FF0000", 10: "#0000FF", 20: "#00FF00"}  # 均线颜色

    def _prepare_data(self):
        """ 处理数据：提取 K 线数据、计算移动均线、设置成交量颜色 """
        self.dates = self.df['日期'].tolist()  # 提取日期列表
        self.kline_data = self.df[["开盘", "收盘", "最低", "最高"]].values.tolist()  # 提取 K 线数据

        # 计算移动平均线
        for period in self.ma_periods:
            self.df[f'MA{period}'] = (
                self.df['收盘']
                .rolling(window=period)
                .mean()
                .bfill()  # 处理 NaN 值（前向填充）
                .round(2)  # 保留两位小数
            )

        # 计算成交量颜色标记（1: 上涨, -1: 下跌）
        self.df['color'] = self.df.apply(
            lambda x: 1 if x['收盘'] >= x['开盘'] else -1,
            axis=1
        )
        self.df['index_vol'] = range(len(self.df))  # 给成交量数据添加索引

    def create_chart(self):
        """ 生成 K 线图表 """
        self._prepare_data()  # 处理数据

        # ================== K 线图配置 ==================
        kline = (
            Kline()
            .add_xaxis(self.dates)  # 设置 X 轴日期
            .add_yaxis(
                series_name="K线",  # K 线名称
                y_axis=self.kline_data,  # K 线数据（开盘、收盘、最低、最高）
                itemstyle_opts=opts.ItemStyleOpts(
                    color=self.color_up,  # 阳线颜色
                    color0=self.color_down  # 阴线颜色
                )
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(
                    title="股票K线走势图",  # 图表标题
                    subtitle=f"股票代码：{self.stock_code}",  # 副标题
                    pos_left="left"# 标题位置
                ),
                legend_opts=opts.LegendOpts(
                    is_show=True,  # 是否显示图例
                    pos_top=10,  # 图例位置（顶部）
                    pos_left="center"# 居中对齐
                ),
                xaxis_opts=opts.AxisOpts(
                    type_="category",  # X 轴类型（类别）
                    axislabel_opts=opts.LabelOpts(rotate=0),  # X 轴标签角度
                    splitline_opts=opts.SplitLineOpts(is_show=True)  # 是否显示网格线
                ),
                yaxis_opts=opts.AxisOpts(
                    is_scale=True,  # Y 轴是否自适应缩放
                    splitarea_opts=opts.SplitAreaOpts(
                        is_show=True,  # 是否显示网格背景
                        areastyle_opts=opts.AreaStyleOpts(opacity=1)  # 设置透明度
                    )
                ),
                tooltip_opts=opts.TooltipOpts(
                    trigger="axis",  # 触发方式：鼠标悬浮时显示
                    axis_pointer_type="cross",  # 坐标轴指示器类型（十字指示）
                ),
                datazoom_opts=[
                    opts.DataZoomOpts(
                        is_show=False,  # 是否显示数据缩放控件
                        type_="inside",  # 缩放类型：内部滑动
                        xaxis_index=[0, 1],  # 作用于 X 轴
                        range_start=80,  # 初始显示范围
                        range_end=100
                    ),
                    opts.DataZoomOpts(
                        is_show=True,  # 显示滑动条缩放
                        xaxis_index=[0, 1],
                        type_="slider",
                        pos_top="100%",  # 位置：底部
                        range_start=80,
                        range_end=100
                    )
                ],
                # 坐标轴指示器
                axispointer_opts=opts.AxisPointerOpts(
                    is_show=True,
                    link=[{"xAxisIndex": "all"}],
                    label=opts.LabelOpts(background_color="#777")
                )
            )
        )

        # ================== 移动平均线配置 ==================
        line = Line().add_xaxis(self.dates)
        for period in self.ma_periods:
            line.add_yaxis(
                series_name=f"MA{period}",
                y_axis=self.df[f'MA{period}'].tolist(),
                is_smooth=True,  # 平滑曲线
                symbol="none",  # 取消数据点标记
                linestyle_opts=opts.LineStyleOpts(
                    color=self.ma_colors[period],  # 颜色
                    width=2# 线宽
                ),
                label_opts=opts.LabelOpts(is_show=False)  # 隐藏数据标签
            )

        # 叠加 K 线和均线
        overlap_kline = kline.overlap(line)

        # ================== 成交量柱状图 ==================
        vol_bar = (
            Bar()
            .add_xaxis(self.dates)
            .add_yaxis(
                series_name="成交量",
                y_axis=self.df[['index_vol', '成交量', 'color']].values.tolist(),
                label_opts=opts.LabelOpts(is_show=False),  # 隐藏标签
                
            )
            .set_global_opts(
                xaxis_opts=opts.AxisOpts(
                    type_="category",
                    grid_index=1,
                    axislabel_opts=opts.LabelOpts(is_show=False),
                    axistick_opts=opts.AxisTickOpts(is_show=False),
                    splitline_opts=opts.SplitLineOpts(is_show=False)
                ),
                yaxis_opts=opts.AxisOpts(is_show=False),
                legend_opts=opts.LegendOpts(is_show=False),
                visualmap_opts=opts.VisualMapOpts(
                    is_show=False,
                    dimension=2,  # 颜色映射使用的维度（color）
                    series_index=4,  # 作用于第 5 个系列（成交量）
                    is_piecewise=True,  # 分段显示
                    pieces=[
                        {"value": 1, "color": self.color_up},  # 上涨颜色
                        {"value": -1, "color": self.color_down}  # 下跌颜色
                    ]
                )
            )
        )

        # ================== 组合图表 ==================
        grid = (
            Grid(init_opts=opts.InitOpts(
                width="98vw",
                height="95vh",
                animation_opts=opts.AnimationOpts(animation=False)  # 关闭动画
            ))
            .add(overlap_kline, grid_opts=opts.GridOpts(pos_top="10%", height="60%" ,pos_left="30px",pos_right="10px"))
            .add(vol_bar, grid_opts=opts.GridOpts(pos_top="73%", height="20%" ,pos_left="30px",pos_right="10px"))
        )

        return grid

    def render(self, file_path: str = "stock_kline.html"):
        """ 渲染并保存 K 线图 """
        chart = self.create_chart()
        chart.render(file_path)
        print(f"K 线图已保存为 {file_path}")

def plot_kline_data(block_name="挂件指数", data_dir="board_data"):
    filepath = os.path.join(data_dir, f"{block_name}_kline_data.csv")
    
    if not os.path.exists(filepath):
        print(f"错误: 文件 {filepath} 不存在。")
        return

    try:
        df = pd.read_csv(filepath)
        
        # 确保日期列存在并转换为 datetime
        if 'date' not in df.columns:
            print(f"错误: 文件 {filepath} 缺少 'date' 列。")
            return
        df['date'] = pd.to_datetime(df['date'])
        
        # 重命名列以符合 StockKlineChart 的要求
        df.rename(columns={
            'date': '日期',
            'open': '开盘',
            'high': '最高',
            'low': '最低',
            'close': '收盘',
            'volume': '成交量'
        }, inplace=True)

        # 确保所有必需的列都存在
        required_cols = ['日期', '开盘', '收盘', '最低', '最高', '成交量']
        if not all(col in df.columns for col in required_cols):
            print(f"错误: 文件 {filepath} 缺少绘制 K 线图所需的列 ({', '.join(required_cols)})。")
            return

        print(f"正在为 {block_name} 生成 K 线图...")

        # 使用 StockKlineChart 类生成图表
        chart_generator = StockKlineChart(df, block_name)
        chart_generator.render(file_path=f"{block_name}_kline.html")
        print(f"{block_name} 的 K 线图已生成。")

    except Exception as e:
        print(f"处理文件 {filepath} 或生成 K 线图时发生错误: {e}")

if __name__ == "__main__":
    plot_kline_data(block_name="挂件指数") 