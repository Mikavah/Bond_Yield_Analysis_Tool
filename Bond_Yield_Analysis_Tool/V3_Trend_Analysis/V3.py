# ---------------------- 1. 基础配置 ----------------------
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime
import tushare as ts
import os

# 解决中文乱码
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


# ---------------------- 2. 新增：历史数据存储与读取 ----------------------
def save_historical_data(new_data, file_path='bond_historical_data.xlsx'):
    """
    保存当日数据到历史Excel文件（自动去重、追加）
    """
    # 添加日期字段
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    new_data['日期'] = today

    # 如果文件不存在，创建新文件；如果存在，追加数据
    if os.path.exists(file_path):
        hist_data = pd.read_excel(file_path)
        # 去重：避免同一天重复保存
        hist_data = hist_data[~((hist_data['日期'] == today) & (hist_data['类型'] == new_data['类型']) & (
                    hist_data['期限(年)'] == new_data['期限(年)']))]
        hist_data = pd.concat([hist_data, new_data], ignore_index=True)
    else:
        hist_data = new_data

    # 保存到Excel
    hist_data.to_excel(file_path, index=False)
    print(f"✅ 历史数据已保存到：{file_path}")
    return hist_data


def get_historical_spread(file_path='bond_historical_data.xlsx', term=10):
    """
    获取近7天10年期国开-国债利差趋势
    """
    if not os.path.exists(file_path):
        # 无历史数据时生成模拟趋势
        dates = [(datetime.datetime.now() - datetime.timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)]
        spreads = [0.11, 0.12, 0.10, 0.13, 0.12, 0.14, 0.13]  # 模拟7天利差
        return pd.DataFrame({'日期': dates, '10Y利差(%)': spreads})

    # 读取历史数据计算利差
    hist_data = pd.read_excel(file_path)
    # 筛选10年期数据
    gov_10y = hist_data[(hist_data['期限(年)'] == term) & (hist_data['类型'] == '国债')]
    cdb_10y = hist_data[(hist_data['期限(年)'] == term) & (hist_data['类型'] == '国开债')]
    # 合并计算利差
    spread_df = pd.merge(gov_10y, cdb_10y, on=['日期', '期限(年)'], suffixes=('_国债', '_国开债'))
    spread_df['10Y利差(%)'] = spread_df['收益率(%)_国开债'] - spread_df['收益率(%)_国债']
    # 取近7天数据
    spread_df = spread_df.sort_values('日期').tail(7)
    return spread_df[['日期', '10Y利差(%)']]


# ---------------------- 3. 数据获取（保留原有逻辑+兜底） ----------------------
def get_bond_yield_data():
    """拉取实时数据，失败则用模拟数据"""
    ts.set_token('你的tushare_token')  # 替换成你的token
    pro = ts.pro_api()

    try:
        # 拉取实时数据（tushare标准接口）
        trade_date = \
        pro.trade_cal(exchange='SSE', is_open=1, end_date=datetime.datetime.now().strftime('%Y%m%d'))['cal_date'].iloc[
            -1]
        gov_codes = ['1000165', '1000166', '1000167', '1000168', '1000169', '1000170']
        cdb_codes = ['1000171', '1000172', '1000173', '1000174', '1000175', '1000176']
        terms = [1, 3, 5, 7, 10, 30]

        gov_data = []
        cdb_data = []
        for code, term in zip(gov_codes, terms):
            df = pro.cbond_yield(code=code, trade_date=trade_date)
            yield_val = df['yield'].values[0] if not df.empty else 0.0
            gov_data.append({'期限(年)': term, '收益率(%)': yield_val, '类型': '国债'})
        for code, term in zip(cdb_codes, terms):
            df = pro.cbond_yield(code=code, trade_date=trade_date)
            yield_val = df['yield'].values[0] if not df.empty else 0.0
            cdb_data.append({'期限(年)': term, '收益率(%)': yield_val, '类型': '国开债'})

        df = pd.DataFrame(gov_data + cdb_data)
        return df

    except Exception as e:
        # 模拟数据兜底
        print(f"实时数据拉取失败（原因：{e}），使用模拟数据～")
        data = {
            '期限(年)': [1, 3, 5, 7, 10, 30, 1, 3, 5, 7, 10, 30],
            '收益率(%)': [2.18, 2.35, 2.48, 2.61, 2.75, 2.98, 2.32, 2.49, 2.62, 2.75, 2.88, 3.11],
            '类型': ['国债'] * 6 + ['国开债'] * 6
        }
        return pd.DataFrame(data)


# ---------------------- 4. 新增：利差趋势分析+量化决策 ----------------------
def analyze_spread_trend(spread_df):
    """
    分析利差趋势，给出量化交易决策
    """
    # 计算关键指标
    latest_spread = spread_df['10Y利差(%)'].iloc[-1]  # 最新利差
    avg_spread = spread_df['10Y利差(%)'].mean()  # 7天均值
    max_spread = spread_df['10Y利差(%)'].max()  # 7天最大值
    min_spread = spread_df['10Y利差(%)'].min()  # 7天最小值
    # 计算分位数（0-1，越高说明当前利差越贵）
    quantile = (latest_spread - min_spread) / (max_spread - min_spread + 0.0001)  # 避免除0

    # 量化决策逻辑（机构常用分位数策略）
    if quantile > 0.8:
        decision = "卖出"
        reason = f"当前利差{latest_spread:.2f}%处于7天80%分位以上，国开债相对国债显著偏贵，建议卖出"
    elif quantile < 0.2:
        decision = "买入"
        reason = f"当前利差{latest_spread:.2f}%处于7天20%分位以下，国开债相对国债显著偏便宜，建议买入"
    else:
        decision = "持有"
        reason = f"当前利差{latest_spread:.2f}%处于7天20%-80%分位，无明确交易信号，建议持有"

    # 生成趋势分析结果
    trend_result = {
        '最新利差': latest_spread,
        '7天均值': avg_spread,
        '7天最高': max_spread,
        '7天最低': min_spread,
        '分位数': quantile,
        '交易决策': decision,
        '决策理由': reason
    }
    return trend_result


# ---------------------- 5. 升级：生成多维度分析日报 ----------------------
def generate_advanced_report(df):
    """
    生成含趋势分析+量化决策的高级日报
    """
    # 1. 保存历史数据
    hist_data = save_historical_data(df)
    # 2. 获取7天利差趋势
    spread_trend = get_historical_spread()
    # 3. 分析趋势+决策
    trend_analysis = analyze_spread_trend(spread_trend)

    # 拆分当日数据
    gov_bond = df[df['类型'] == '国债'].reset_index(drop=True)
    cdb_bond = df[df['类型'] == '国开债'].reset_index(drop=True)
    today = datetime.datetime.now().strftime('%Y-%m-%d')

    # 4. 画图（双图：当日曲线 + 利差趋势）
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12), facecolor='white')
    fig.suptitle(f'固收多维度分析报告（{today}）', fontsize=22, fontweight='bold', y=0.98)

    # 子图1：当日收益率曲线
    ax1.set_facecolor('#F8F9FA')
    ax1.plot(gov_bond['期限(年)'], gov_bond['收益率(%)'],
             color='#2E86AB', linewidth=3.5, marker='o', markersize=9,
             markerfacecolor='white', markeredgewidth=2, label='国债收益率曲线')
    ax1.plot(cdb_bond['期限(年)'], cdb_bond['收益率(%)'],
             color='#A23B72', linewidth=3.5, marker='s', markersize=9,
             markerfacecolor='white', markeredgewidth=2, label='国开债收益率曲线')
    ax1.set_title('当日收益率曲线', fontsize=18, fontweight='bold', pad=20)
    ax1.set_xlabel('期限（年）', fontsize=14, labelpad=10)
    ax1.set_ylabel('收益率（%）', fontsize=14, labelpad=10)
    ax1.set_xlim(0, 31)
    ax1.set_ylim(2.0, 3.2)
    ax1.set_xticks([1, 3, 5, 7, 10, 30])
    ax1.legend(loc='upper right', fontsize=12)
    ax1.grid(True, alpha=0.4)

    # 子图2：7天利差趋势
    ax2.set_facecolor('#F8F9FA')
    ax2.plot(spread_trend['日期'], spread_trend['10Y利差(%)'],
             color='#E63946', linewidth=4, marker='D', markersize=8,
             markerfacecolor='white', markeredgewidth=2)
    ax2.axhline(y=trend_analysis['7天均值'], color='#457B9D', linestyle='--', linewidth=2,
                label=f'7天均值：{trend_analysis["7天均值"]:.2f}%')
    ax2.set_title('近7天10年期国开-国债利差趋势', fontsize=18, fontweight='bold', pad=20)
    ax2.set_xlabel('日期', fontsize=14, labelpad=10)
    ax2.set_ylabel('利差（%）', fontsize=14, labelpad=10)
    ax2.tick_params(axis='x', rotation=45)
    ax2.legend(loc='upper right', fontsize=12)
    ax2.grid(True, alpha=0.4)

    # 保存图片
    img_path = f'固收高级分析报告_{today}.png'
    plt.tight_layout()
    plt.savefig(img_path, dpi=300, bbox_inches='tight')
    plt.show()

    # 5. 生成Excel版日报（机构常用）
    excel_path = f'固收高级分析报告_{today}.xlsx'
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        # 工作表1：当日收益率数据
        df.to_excel(writer, sheet_name='当日收益率', index=False)
        # 工作表2：7天利差趋势
        spread_trend.to_excel(writer, sheet_name='7天利差趋势', index=False)
        # 工作表3：交易决策
        decision_df = pd.DataFrame([trend_analysis])
        decision_df.to_excel(writer, sheet_name='量化交易决策', index=False)

    # 6. 控制台输出核心结论
    print("=" * 80)
    print(f"✅ 高级分析报告生成完成！")
    print(f"📊 图表保存路径：{img_path}")
    print(f"📋 Excel报告路径：{excel_path}")
    print("=" * 80)
    print("\n【核心交易决策】")
    print(f"📈 10年期国开-国债利差：{trend_analysis['最新利差']:.2f}%")
    print(f"📊 7天分位数：{trend_analysis['分位数']:.2f}（0=最便宜，1=最贵）")
    print(f"🔍 决策：{trend_analysis['交易决策']}")
    print(f"💡 理由：{trend_analysis['决策理由']}")


# ---------------------- 6. 主函数：一键运行 ----------------------
if __name__ == '__main__':
    print("🔍 正在拉取国债收益率数据...")
    bond_data = get_bond_yield_data()

    print("📈 正在生成多维度分析报告...")
    generate_advanced_report(bond_data)

    print("\n🎉 高级分析报告生成完成！可直接用于投研汇报/交易决策～")