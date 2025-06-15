import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# 配置 matplotlib 以支持中文显示
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei'] # 替换为你的系统上已安装的中文字体
plt.rcParams['axes.unicode_minus'] = False # 解决负号显示问题

def analyze_dual_broad_correlation(index1_name, index2_name):
    """
    分析两个板块的涨跌幅相关性，并可视化其概率分布。

    Args:
        index1_name (str): 第一个板块的名称 (例如 '大盘').
        index2_name (str): 第二个板块的名称 (例如 '多普勒指数').
    """
    print(f'正在分析 {index1_name} 和 {index2_name} 的相关性...')

    board_data_dir = 'board_data'
    index1_filepath = os.path.join(board_data_dir, f'{index1_name}_kline_data.csv')
    index2_filepath = os.path.join(board_data_dir, f'{index2_name}_kline_data.csv')

    if not os.path.exists(index1_filepath):
        print(f'错误: 找不到文件 {index1_filepath}')
        return
    if not os.path.exists(index2_filepath):
        print(f'错误: 找不到文件 {index2_filepath}')
        return

    # 读取数据
    df1 = pd.read_csv(index1_filepath, index_col='date', parse_dates=True)
    df2 = pd.read_csv(index2_filepath, index_col='date', parse_dates=True)

    # 处理重复日期，保留最后一条记录
    df1 = df1[~df1.index.duplicated(keep='last')]
    df2 = df2[~df2.index.duplicated(keep='last')]

    # 计算涨跌幅
    df1['pct_change'] = df1['close'].pct_change() * 100 # 百分比形式
    df2['pct_change'] = df2['close'].pct_change() * 100 # 百分比形式

    # 合并数据
    # 使用内连接确保只有两个板块都有数据的日期才被考虑
    merged_df = pd.merge(df1[['pct_change']], df2[['pct_change']],
                         left_index=True, right_index=True, how='inner',
                         suffixes=(f'_{index1_name}', f'_{index2_name}'))

    # 删除涨跌幅为 NaN 的行 (通常是第一行)
    merged_df.dropna(inplace=True)

    if merged_df.empty:
        print('没有共同的数据点，无法进行分析。')
        return

    # 计算相关系数
    correlation = merged_df[f'pct_change_{index1_name}'].corr(merged_df[f'pct_change_{index2_name}'])
    print(f'{index1_name} 和 {index2_name} 涨跌幅的相关系数: {correlation:.4f}')

    # --- 可视化 --- 

    # 创建一个新的图形，包含两个子图：直方图和联合分布图
    fig, axes = plt.subplots(1, 2, figsize=(18, 7))
    fig.suptitle(f'{index1_name} 与 {index2_name} 涨跌幅概率分布及相关性分析', fontsize=16)

    # 1. 绘制第一个板块的涨跌幅直方图
    sns.histplot(merged_df[f'pct_change_{index1_name}'], kde=True, ax=axes[0], color='skyblue', bins=50)
    axes[0].set_title(f'{index1_name} 涨跌幅分布')
    axes[0].set_xlabel('涨跌幅 (%)')
    axes[0].set_ylabel('频率')

    # 2. 绘制第二个板块的涨跌幅直方图 (在同一个子图中，或者可以考虑单独的子图)
    # 这里为了简洁，我们可以直接在联合分布图中看到它们的分布
    # 如果需要独立展示，可以这样：
    # fig2, ax2 = plt.subplots(figsize=(10, 6))
    # sns.histplot(merged_df[f'pct_change_{index2_name}'], kde=True, ax=ax2, color='lightcoral', bins=50)
    # ax2.set_title(f'{index2_name} 涨跌幅分布')
    # ax2.set_xlabel('涨跌幅 (%)')
    # ax2.set_ylabel('频率')
    # plt.show()

    # 3. 绘制两个板块涨跌幅的联合分布图 (散点图 + 核密度估计)
    # 使用 seaborn.jointplot 可以自动创建散点图和边缘直方图/KDE图
    # 这里为了在一个 fig 中，我们使用 scatterplot 和 kdeplot 组合
    sns.scatterplot(x=f'pct_change_{index1_name}', y=f'pct_change_{index2_name}', data=merged_df, ax=axes[1], alpha=0.6)
    sns.kdeplot(x=f'pct_change_{index1_name}', y=f'pct_change_{index2_name}', data=merged_df, ax=axes[1], cmap='viridis', fill=True)
    axes[1].set_title(f'{index1_name} 与 {index2_name} 涨跌幅联合分布')
    axes[1].set_xlabel(f'{index1_name} 涨跌幅 (%)')
    axes[1].set_ylabel(f'{index2_name} 涨跌幅 (%)')

    # 在联合分布图上添加相关系数文本
    axes[1].text(0.05, 0.95, f'相关系数: {correlation:.4f}',
                 transform=axes[1].transAxes, fontsize=12, verticalalignment='top')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95]) # 调整布局，防止标题重叠
    plt.savefig(f'correlation_{index1_name}_{index2_name}.png', dpi=300)
    plt.show()

if __name__ == '__main__':
    # 示例用法，分析大盘和多普勒指数
    analyze_dual_broad_correlation('大盘', '多普勒指数') 