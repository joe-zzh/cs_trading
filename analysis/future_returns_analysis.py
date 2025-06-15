import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# 配置 matplotlib 以支持中文显示
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei'] # 替换为你的系统上已安装的中文字体
plt.rcParams['axes.unicode_minus'] = False # 解决负号显示问题

def analyze_future_returns_distribution(trigger_index_name, target_index_name, threshold_value, trigger_type, future_days, min_trigger_points=10):
    """
    分析当一个板块上涨或下跌时，另一个板块在未来指定天数的收益率概率分布。

    Args:
        trigger_index_name (str): 触发条件（上涨/下跌）的板块名称 (例如 '手套').
        target_index_name (str): 分析未来收益率的板块名称 (例如 '大盘').
        threshold_value (float): 触发板块涨跌的绝对百分比阈值 (例如 0.5 表示 0.5%).
        trigger_type (str): 触发类型 ('up' 或 'down').
        future_days (list): 包含未来天数的列表 (例如 [1, 5, 10]).
        min_trigger_points (int): 最小触发日期数量，低于此值不进行分析。
    Returns:
        tuple: (list: 包含每个未来天数结果的字典列表, dict: 原始收益率数据按天数分组), 如果数据不足则返回 ([], {}).
    """
    # print(f'正在分析当 {trigger_index_name} {trigger_type} {threshold_value}% 时，{target_index_name} 未来收益率的概率分布...')

    board_data_dir = 'board_data'
    trigger_filepath = os.path.join(board_data_dir, f'{trigger_index_name}_kline_data.csv')
    target_filepath = os.path.join(board_data_dir, f'{target_index_name}_kline_data.csv')

    if not os.path.exists(trigger_filepath):
        # print(f'错误: 找不到文件 {trigger_filepath}')
        return [], {}
    if not os.path.exists(target_filepath):
        # print(f'错误: 找不到文件 {target_filepath}')
        return [], {}

    # 读取数据
    df_trigger = pd.read_csv(trigger_filepath, index_col='date', parse_dates=True)
    df_target = pd.read_csv(target_filepath, index_col='date', parse_dates=True)

    # 处理重复日期，保留最后一条记录
    df_trigger = df_trigger[~df_trigger.index.duplicated(keep='last')]
    df_target = df_target[~df_target.index.duplicated(keep='last')]

    # 合并数据，确保日期对齐
    merged_df = pd.merge(df_trigger[['close']], df_target[['close']],
                         left_index=True, right_index=True, how='inner',
                         suffixes=(f'_{trigger_index_name}', f'_{target_index_name}'))

    # 计算触发板块的日涨跌幅 (百分比)
    merged_df[f'pct_change_{trigger_index_name}'] = merged_df[f'close_{trigger_index_name}'].pct_change() * 100

    if trigger_type == 'up':
        trigger_days_df = merged_df[merged_df[f'pct_change_{trigger_index_name}'] >= threshold_value].copy()
    elif trigger_type == 'down':
        trigger_days_df = merged_df[merged_df[f'pct_change_{trigger_index_name}'] <= -threshold_value].copy()
    else:
        print(f"不支持的触发类型: {trigger_type}")
        return [], {}

    if len(trigger_days_df) < min_trigger_points:
        # print(f'在 {trigger_index_name} {trigger_type} {threshold_value}% 或更多时，触发日期数量 ({len(trigger_days_df)}) 小于最小要求 ({min_trigger_points})，跳过分析。')
        return [], {}

    # print(f'找到 {len(trigger_days_df)} 个触发日期。')

    # 为目标板块计算未来的收益率
    all_dates = merged_df.index.to_list()
    date_to_pos = {date: i for i, date in enumerate(all_dates)}

    summary_results = []
    raw_returns_data = {} # 存储原始收益率数据，用于绘图

    for days in future_days:
        future_returns = []
        for trigger_date in trigger_days_df.index:
            current_pos = date_to_pos.get(trigger_date)
            if current_pos is None:
                continue 

            future_pos = current_pos + days
            if future_pos < len(all_dates):
                future_date = all_dates[future_pos]
                if future_date in merged_df.index:
                    current_close = merged_df.loc[trigger_date, f'close_{target_index_name}']
                    future_close = merged_df.loc[future_date, f'close_{target_index_name}']
                    if current_close != 0:
                        ret = ((future_close - current_close) / current_close) * 100
                        future_returns.append(ret)

        if future_returns:
            mean_return = pd.Series(future_returns).mean()
            std_return = pd.Series(future_returns).std()
            summary_results.append({
                'Trigger Index': trigger_index_name,
                'Target Index': target_index_name,
                'Trigger Threshold (%)': threshold_value,
                'Trigger Type': trigger_type,
                'Future Days': days,
                'Mean Return (%)': mean_return,
                'Std Dev Return (%)': std_return,
                'Num Triggers': len(trigger_days_df),
                'Num Observations': len(future_returns)
            })
            raw_returns_data[days] = future_returns # 存储原始列表
    return summary_results, raw_returns_data

def plot_future_returns_distribution_single_scenario(
    trigger_index_name, target_index_name, threshold_value, trigger_type, future_days, results_data
):
    """
    绘制单个场景的未来收益率分布图。
    results_data 是一个字典，其中键是 future_days，值是收益率列表。
    """
    num_plots = len(future_days)
    fig, axes = plt.subplots(num_plots, 1, figsize=(10, 5 * num_plots))
    if num_plots == 1:
        axes = [axes] # 确保 axes 是可迭代的，即使只有一个子图

    fig.suptitle(f'当 {trigger_index_name} {trigger_type} {threshold_value}% 时，{target_index_name} 未来收益率分布', fontsize=16)

    for i, days in enumerate(future_days):
        returns = results_data.get(days, []) # 获取此 future_day 的原始收益率
        if not returns:
            axes[i].set_title(f'{target_index_name} 未来 {days} 天收益率分布 (无数据)')
            axes[i].set_xlabel('收益率 (%)')
            axes[i].set_ylabel('频率')
            continue

        sns.histplot(returns, kde=True, ax=axes[i], bins=30, color='lightgreen')
        axes[i].set_title(f'{target_index_name} 未来 {days} 天收益率分布')
        axes[i].set_xlabel('收益率 (%)')
        axes[i].set_ylabel('频率')
        # 添加统计信息
        mean_return = pd.Series(returns).mean()
        std_return = pd.Series(returns).std()
        axes[i].text(0.05, 0.95, f'''均值: {mean_return:.2f}%
标准差: {std_return:.2f}%''',
                     transform=axes[i].transAxes, fontsize=10, verticalalignment='top')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plot_filename = f'future_returns_distribution_{trigger_index_name}_{trigger_type}_{target_index_name}.png'
    plt.savefig(plot_filename, dpi=300)
    print(f'图表已保存到 {plot_filename}')
    plt.show()

if __name__ == '__main__':
    # 假设这是从 board.py 中获取的板块列表
    sections_to_scrape = [
        {"section_type": "BROAD", "type_val": 2, "block_name": "大盘"},
        {"section_type": "HOT", "type_val": 1401696786733232128, "block_name": "多普勒指数"},
        {"section_type": "HOT", "type_val": 1402501509110038528, "block_name": "千战指数"},
        {"section_type": "HOT", "type_val": 1368024613355786240, "block_name": "百战指数"},
        {"section_type": "HOT", "type_val": 1368076160637956096, "block_name": "探员指数"},
        {"section_type": "HOT", "type_val": 1355763711064055808, "block_name": "挂件指数"},
        {"section_type": "ITEM_TYPE", "type_val": "CSGO_Tool_Sticker", "block_name": "印花"},
        {"section_type": "ITEM_TYPE", "type_val": "Type_Hands", "block_name": "手套"},
        {"section_type": "ITEM_TYPE", "type_val": "CSGO_Type_Knife", "block_name": "刀"},
        {"section_type": "ITEM_TYPE", "type_val": "CSGO_Type_WeaponCase", "block_name": "武器箱"}
    ]

    all_analysis_results = []
    future_days_to_analyze = [1, 5, 10] # 分析未来 1, 5, 10 天
    threshold_percentage = 0.5 # 触发涨跌的绝对阈值 0.5%
    trigger_types = ['up', 'down']

    # 定义一个示例场景，用于在所有 CSV 保存后绘制图表
    example_plot_scenario = {
        'trigger_name': '手套',
        'target_name': '大盘',
        'trigger_type': 'up'
    }
    example_raw_returns_data = None

    for trigger_section in sections_to_scrape:
        trigger_name = trigger_section['block_name']
        for target_section in sections_to_scrape:
            target_name = target_section['block_name']

            if trigger_name == target_name: # 避免自己分析自己
                continue

            for tr_type in trigger_types:
                print(f'正在分析: 当 {trigger_name} {tr_type}时，{target_name} 未来收益率...')
                results_summary, raw_returns = analyze_future_returns_distribution(
                    trigger_index_name=trigger_name,
                    target_index_name=target_name,
                    threshold_value=threshold_percentage,
                    trigger_type=tr_type,
                    future_days=future_days_to_analyze
                )
                if results_summary:
                    all_analysis_results.extend(results_summary)
                    # 如果是示例场景，则保存其原始收益率数据
                    if (trigger_name == example_plot_scenario['trigger_name'] and
                        target_name == example_plot_scenario['target_name'] and
                        tr_type == example_plot_scenario['trigger_type']):
                        example_raw_returns_data = raw_returns

    if all_analysis_results:
        # 将结果从长格式转换为宽格式
        processed_results = []
        # 首先根据组合键（Trigger Index, Target Index, Trigger Threshold, Trigger Type）进行分组
        grouped_data = {}
        for res in all_analysis_results:
            key = (res['Trigger Index'], res['Target Index'], res['Trigger Threshold (%)'], res['Trigger Type'])
            if key not in grouped_data:
                grouped_data[key] = {
                    'Trigger Index': res['Trigger Index'],
                    'Target Index': res['Target Index'],
                    'Trigger Threshold (%)': res['Trigger Threshold (%)'],
                    'Trigger Type': res['Trigger Type'],
                    'Num Triggers': res['Num Triggers'] # 触发次数对于同一组是相同的
                }
            # 添加每个 Future Days 的收益率和标准差列
            grouped_data[key][f'{res["Future Days"]}_Mean_Return (%)'] = res['Mean Return (%)']
            grouped_data[key][f'{res["Future Days"]}_Std_Dev (%)'] = res['Std Dev Return (%)']
        
        # 将分组后的数据转换为列表，以便创建DataFrame
        for key, value_dict in grouped_data.items():
            processed_results.append(value_dict)

        results_df = pd.DataFrame(processed_results)
        
        output_dir = 'future_returns_by_target'
        os.makedirs(output_dir, exist_ok=True)

        target_indices = results_df['Target Index'].unique()
        for target_idx in target_indices:
            for tr_type in trigger_types:
                df_target_type = results_df[(results_df['Target Index'] == target_idx) & (results_df['Trigger Type'] == tr_type)]
                if not df_target_type.empty:
                    output_csv_path = os.path.join(output_dir, f'{target_idx}_future_returns_summary_{tr_type}.csv')
                    df_target_type.to_csv(output_csv_path, index=False, encoding='utf-8')
                    print(f'分析结果已保存到 {output_csv_path}')
    else:
        print('没有生成任何分析结果。')

    # 绘制示例图表
    if example_raw_returns_data:
        print(f"\n正在绘制示例图表: 当 {example_plot_scenario['trigger_name']} {example_plot_scenario['trigger_type']}时，{example_plot_scenario['target_name']} 未来收益率分布...")
        plot_future_returns_distribution_single_scenario(
            trigger_index_name=example_plot_scenario['trigger_name'],
            target_index_name=example_plot_scenario['target_name'],
            threshold_value=threshold_percentage,
            trigger_type=example_plot_scenario['trigger_type'],
            future_days=future_days_to_analyze,
            results_data=example_raw_returns_data
        ) 