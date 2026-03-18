# ---------------------- 1. 基础配置（解决中文+导入库） ----------------------
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime
import tushare as ts  # 财经数据接口

# 解决中文乱码
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


# ---------------------- 2. 第一步：自动拉取实时国债收益率数据（修复接口） ----------------------
def get_bond_yield_data():
    """
    拉取中债登实时国债/国开债收益率数据（用tushare标准接口）
    返回：整理后的DataFrame
    """
    # 1. 设置tushare token（替换成个人token）
    ts.set_token('替换成自己的token')  # 这里替换成你复制的token
    pro = ts.pro_api()

    # 2. 拉取国债收益率数据（改用tushare标准接口：cbond_yield）
    try:
        # 获取最新交易日（避免非交易日无数据）
        trade_date = \
        pro.trade_cal(exchange='SSE', is_open=1, end_date=datetime.datetime.now().strftime('%Y%m%d'))['cal_date'].iloc[
            -1]

        # 国债收益率（中债国债收益率曲线：1年期、3年期、5年期、7年期、10年期、30年期）
        gov_codes = ['1000165', '1000166', '1000167', '1000168', '1000169', '1000170']  # 标准代码
        cdb_codes = ['1000171', '1000172', '1000173', '1000174', '1000175', '1000176']  # 国开债代码
        terms = [1, 3, 5, 7, 10, 30]

        gov_data = []
        cdb_data = []

        # 拉取国债数据
        for code, term in zip(gov_codes, terms):
            df = pro.cbond_yield(code=code, trade_date=trade_date)
            yield_val = df['yield'].values[0] if not df.empty else 0.0
            gov_data.append({'期限(年)': term, '收益率(%)': yield_val, '类型': '国债'})

        # 拉取国开债数据
        for code, term in zip(cdb_codes, terms):
            df = pro.cbond_yield(code=code, trade_date=trade_date)
            yield_val = df['yield'].values[0] if not df.empty else 0.0
            cdb_data.append({'期限(年)': term, '收益率(%)': yield_val, '类型': '国开债'})

        # 合并数据
        df = pd.DataFrame(gov_data + cdb_data)
        return df

    except Exception as e:
        # 备用方案：如果实时数据拉取失败，用模拟数据兜底
        print(f"实时数据拉取失败（原因：{e}），自动使用模拟数据～")
        data = {
            '期限(年)': [1, 3, 5, 7, 10, 30, 1, 3, 5, 7, 10, 30],
            '收益率(%)': [2.18, 2.35, 2.48, 2.61, 2.75, 2.98, 2.32, 2.49, 2.62, 2.75, 2.88, 3.11],
            '类型': ['国债'] * 6 + ['国开债'] * 6
        }
        return pd.DataFrame(data)


# ---------------------- 3. 第二步：生成交易日报（图表+分析） ----------------------
def generate_trading_report(df):
    """
    生成固收交易日报
    """
    # 拆分数据
    gov_bond = df[df['类型'] == '国债'].reset_index(drop=True)
    cdb_bond = df[df['类型'] == '国开债'].reset_index(drop=True)

    # 1. 画图
    fig, ax = plt.subplots(figsize=(14, 8), facecolor='white')
    ax.set_facecolor('#F8F9FA')

    # 画曲线
    ax.plot(gov_bond['期限(年)'], gov_bond['收益率(%)'],
            color='#2E86AB', linewidth=3.5, marker='o', markersize=9,
            markerfacecolor='white', markeredgewidth=2, label='国债收益率曲线')
    ax.plot(cdb_bond['期限(年)'], cdb_bond['收益率(%)'],
            color='#A23B72', linewidth=3.5, marker='s', markersize=9,
            markerfacecolor='white', markeredgewidth=2, label='国开债收益率曲线')

    # 标题/坐标轴
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    ax.set_title(f'国债VS国开债收益率曲线（{today}）', fontsize=20, fontweight='bold', pad=30)
    ax.set_xlabel('期限（年）', fontsize=16, fontweight='medium', labelpad=15)
    ax.set_ylabel('收益率（%）', fontsize=16, fontweight='medium', labelpad=15)

    # 坐标轴优化
    ax.set_xlim(0, 31)
    ax.set_ylim(2.0, 3.2)
    ax.set_xticks([1, 3, 5, 7, 10, 30])
    ax.tick_params(labelsize=12)

    # 关键点位标注
    gov_10y = gov_bond.loc[gov_bond['期限(年)'] == 10, '收益率(%)'].values[0]
    cdb_10y = cdb_bond.loc[cdb_bond['期限(年)'] == 10, '收益率(%)'].values[0]
    ax.text(10.8, gov_10y + 0.04, f'国债10Y：{gov_10y:.2f}%', fontsize=13, color='#2E86AB')
    ax.text(10.8, cdb_10y + 0.04, f'国开10Y：{cdb_10y:.2f}%', fontsize=13, color='#A23B72')

    # 图例/网格
    ax.legend(loc='upper right', fontsize=14, frameon=True, shadow=True)
    ax.grid(True, alpha=0.4)

    # 保存图片
    img_path = f'固收交易日报_{today}.png'
    plt.tight_layout()
    plt.savefig(img_path, dpi=300, bbox_inches='tight')
    plt.show()

    # 2. 计算核心利差
    gov_1y = gov_bond.loc[gov_bond['期限(年)'] == 1, '收益率(%)'].values[0]
    cdb_30y = cdb_bond.loc[cdb_bond['期限(年)'] == 30, '收益率(%)'].values[0]

    spread_cdb_gov_10y = cdb_10y - gov_10y  # 国开-国债利差
    spread_gov_10y_1y = gov_10y - gov_1y  # 国债10Y-1Y利差
    spread_cdb_30y_10y = cdb_30y - cdb_10y  # 国开30Y-10Y利差

    # 3. 生成文字分析
    report_content = f"""
# 固收交易日报（{today}）
## 一、核心收益率数据
- 国债1年期：{gov_1y:.2f}% | 国债10年期：{gov_10y:.2f}%
- 国开10年期：{cdb_10y:.2f}% | 国开30年期：{cdb_30y:.2f}%

## 二、关键利差分析
1. 10年期国开-国债利差：{spread_cdb_gov_10y:.2f}%
   - 判断：{'国开债相对国债偏贵' if spread_cdb_gov_10y > 0.10 else '国开债相对国债偏便宜'}
2. 国债10Y-1Y期限利差：{spread_gov_10y_1y:.2f}%
   - 判断：{'收益率曲线陡峭，多头占优' if spread_gov_10y_1y > 0.5 else '收益率曲线平坦，震荡行情'}
3. 国开债30Y-10Y期限利差：{spread_cdb_30y_10y:.2f}%

## 三、交易建议
1. {f'当前国开-国债利差{spread_cdb_gov_10y:.2f}%，建议逢高减持国开债' if spread_cdb_gov_10y > 0.10 else f'当前国开-国债利差{spread_cdb_gov_10y:.2f}%，可逢低配置国开债'}
2. 关注10年期国债收益率能否站稳{gov_10y:.2f}%，跌破则谨慎操作
3. 30Y-10Y利差{spread_cdb_30y_10y:.2f}%，{'长端配置价值较高' if spread_cdb_30y_10y > 0.2 else '长端性价比一般'}
    """

    # 4. 保存日报到本地
    report_path = f'固收交易日报_{today}.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)

    # 5. 控制台输出
    print("=" * 80)
    print(f"✅ 交易日报生成完成！")
    print(f"📊 图表保存路径：{img_path}")
    print(f"📝 文字报告保存路径：{report_path}")
    print("=" * 80)
    print(report_content)


# ---------------------- 4. 主函数：一键运行 ----------------------
if __name__ == '__main__':
    # 步骤1：拉取数据
    print("🔍 正在拉取实时国债收益率数据...")
    bond_data = get_bond_yield_data()

    # 步骤2：生成日报
    print("📈 正在生成交易日报...")
    generate_trading_report(bond_data)

    print("\n🎉 日报生成完成！可直接用于工作汇报/交易复盘～")
