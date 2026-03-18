# ---------------------- 1. 导入库+样式+字体 ----------------------
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# ---------------------- 2. 读取数据 ----------------------
df = pd.read_excel('day1_data.xlsx')
gov_bond = df[df['类型'] == '国债'].reset_index(drop=True)
cdb_bond = df[df['类型'] == '国开债'].reset_index(drop=True)

# ---------------------- 3. 画图 ----------------------
fig, ax = plt.subplots(figsize=(12, 7))
ax.plot(gov_bond['期限(年)'], gov_bond['收益率(%)'],
        color='#1F77B4', linewidth=3, marker='o', markersize=8, label='国债收益率曲线')
ax.plot(cdb_bond['期限(年)'], cdb_bond['收益率(%)'],
        color='#D62728', linewidth=3, marker='s', markersize=8, label='国开债收益率曲线')

ax.set_title('国债VS国开债收益率曲线（2026-03）', fontsize=18, fontweight='bold', pad=25)
ax.set_xlabel('期限（年）', fontsize=14, fontweight='medium')
ax.set_ylabel('收益率（%）', fontsize=14, fontweight='medium')
ax.set_xlim(0, 31)
ax.set_ylim(2.0, 3.2)

gov_10y = gov_bond.loc[gov_bond['期限(年)']==10, '收益率(%)'].values[0]
cdb_10y = cdb_bond.loc[cdb_bond['期限(年)']==10, '收益率(%)'].values[0]
ax.text(10.5, gov_10y + 0.03, f'国债10Y：{gov_10y}%', fontsize=11, color='#1F77B4')
ax.text(10.5, cdb_10y + 0.03, f'国开10Y：{cdb_10y}%', fontsize=11, color='#D62728')

ax.legend(loc='upper right', fontsize=12)
ax.grid(True, alpha=0.4)
plt.tight_layout()
plt.savefig('国债国开债收益率曲线.png', dpi=300, bbox_inches='tight')
plt.show()

# ---------------------- 4. 利差计算+阈值判断（核心修改） ----------------------
print("=== 核心利差计算结果 ===")
# 10年期国开-国债利差
spread_cdb_gov_10y = cdb_10y - gov_10y
print(f"10年期国开-国债利差：{spread_cdb_gov_10y:.2f}%")
# 国债10Y-1Y利差
gov_1y = gov_bond.loc[gov_bond['期限(年)']==1, '收益率(%)'].values[0]
spread_gov_10y_1y = gov_10y - gov_1y
print(f"国债10Y-1Y期限利差：{spread_gov_10y_1y:.2f}%")
# 国开30Y-10Y利差
cdb_30y = cdb_bond.loc[cdb_bond['期限(年)']==30, '收益率(%)'].values[0]
spread_cdb_30y_10y = cdb_30y - cdb_10y
print(f"国开债30Y-10Y期限利差：{spread_cdb_30y_10y:.2f}%")

# ---------------------- 5. 利差判断（改阈值就能看到差别） ----------------------
# 阈值1：0.10（原数值）
print("\n【阈值=0.10时的判断】")
if spread_cdb_gov_10y > 0.10:
    print(f"10年期国开-国债利差{spread_cdb_gov_10y:.2f}% > 0.10% → 国开债相对国债偏贵")
else:
    print(f"10年期国开-国债利差{spread_cdb_gov_10y:.2f}% ≤ 0.10% → 国开债相对国债偏便宜")

# 阈值2：0.15（你修改后的数值）
print("\n【阈值=0.15时的判断】")
if spread_cdb_gov_10y > 0.15:
    print(f"10年期国开-国债利差{spread_cdb_gov_10y:.2f}% > 0.15% → 国开债相对国债偏贵")
else:
    print(f"10年期国开-国债利差{spread_cdb_gov_10y:.2f}% ≤ 0.15% → 国开债相对国债偏便宜")