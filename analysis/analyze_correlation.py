import pandas as pd
import os
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

def analyze_correlation(data_dir="board_data"):
    """
    Analyzes the correlation between each sub-section index and the main board index,
    and plots a heatmap of all inter-block correlations.
    """
    # 配置 matplotlib 以支持中文显示
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei'] # 替换为你的系统上已安装的中文字体
    plt.rcParams['axes.unicode_minus'] = False # 解决负号显示问题

    all_data = {}
    
    # Load all CSV files
    for filename in os.listdir(data_dir):
        if filename.endswith(".csv"):
            filepath = os.path.join(data_dir, filename)
            block_name = filename.replace("_kline_data.csv", "")
            
            try:
                df = pd.read_csv(filepath)
                if 'date' in df.columns and 'close' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
                    # Remove duplicate dates, keeping the last (most recent) entry
                    df = df.drop_duplicates(subset=['date'], keep='last')
                    df = df.set_index('date')
                    
                    # 计算每日涨跌幅
                    df['daily_return'] = df['close'].pct_change()
                    
                    # 存储涨跌幅数据
                    all_data[block_name] = df['daily_return']
                    print(f"成功加载文件: {filename}")
                else:
                    print(f"文件 {filename} 缺少 'date' 或 'close' 列，跳过。")
            except Exception as e:
                print(f"读取文件 {filename} 时发生错误: {e}")

    if not all_data:
        print("未找到任何 K 线图数据文件进行分析。")
        return

    # Create a combined DataFrame
    combined_df = pd.DataFrame(all_data)

    # 丢弃包含 NaN 值的行，因为 pct_change() 会在第一行生成 NaN
    combined_df.dropna(inplace=True)

    # Ensure '大盘' (Main Board) data exists
    if '大盘' not in combined_df.columns:
        print("未找到 '大盘' 数据，无法计算相关性。")
        # 继续执行以计算其他板块的相关性，但会跳过与大盘的直接比较

    # ==================================================================
    # 计算所有板块之间的相关矩阵
    correlation_matrix = combined_df.corr()

    print("\n--- 所有板块相关矩阵 (基于涨跌幅) ---")
    print(correlation_matrix)

    # 绘制热力图
    plt.figure(figsize=(10, 8))
    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', fmt=".2f", linewidths=.5)
    plt.title('各板块涨跌幅相关性热力图')
    plt.tight_layout()
    plt.savefig('block_correlation_heatmap.png')
    plt.show()
    print("相关性热力图已保存为 block_correlation_heatmap.png")

    # ==================================================================
    # 如果大盘数据存在，仍然打印与大盘的单项相关性
    if '大盘' in combined_df.columns:
        main_board_data = combined_df['大盘']
        print("\n--- 与大盘的相关性分析结果 (基于涨跌幅) ---")
        for block_name, series in combined_df.items():
            if block_name != '大盘':
                correlation = series.corr(main_board_data)
                print(f"{block_name} 与 大盘 的相关性: {correlation:.4f}")

if __name__ == "__main__":
    analyze_correlation() 