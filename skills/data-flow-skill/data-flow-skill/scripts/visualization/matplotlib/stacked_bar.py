"""
堆叠柱状图（stacked bar chart）
特征：每列堆叠多个组分，展示结构占比，蓝灰递进色阶
来源：学术论文中展示组成结构或任务分解
"""

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# ── 全局样式 ─────────────────────────────────────────────────────
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['DejaVu Sans', 'Arial', 'Helvetica'],
    'text.usetex': False,
})

# ── 颜色（蓝灰递进色阶）──────────────────────────────────────
C_LAYERS = [
    '#D3D3D3',   # 底层（最浅灰）
    '#A8C8E8',   # 第二层（浅钢蓝）
    '#5499C7',   # 第三层（中蓝）
    '#1B3D6E',   # 顶层（深蓝，主组分）
]

# ── 数据（请替换为你的数据）───────────────────────────────────
categories = ['Task A', 'Task B', 'Task C', 'Task D', 'Task E']

# 每层一个 dict，key = 组分名，value = 该组分在每个 category 的数值
components = {
    'Base Model':  [20, 25, 15, 30, 22],
    'Feature Ex':  [35, 30, 40, 25, 33],
    'Fusion':      [45, 45, 45, 45, 45],
}

# ── 参数配置 ─────────────────────────────────────────────────
TITLE   = r'Performance Breakdown by Task'
YLABEL  = r'Score'
YLIM    = (0, 110)
BAR_W   = 0.5
BOTTOM_GAP = 0.05

# ── 数据解析 ─────────────────────────────────────────────────
component_names = list(components.keys())
n_groups  = len(categories)
x_center = np.arange(n_groups)

# 转为 numpy 数组
vals_list = [np.array(components[name]) for name in component_names]

# 检查：每列总量不能超过 YLIM[1]
col_sums = sum(vals_list)
if col_sums.max() > YLIM[1]:
    import warnings
    warnings.warn(f'堆叠总量 {col_sums.max()} 超过 YLIM[1]={YLIM[1]}，已自动扩展 YLIM')

# ── 画布 ─────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8.0, 5.0))

# ── 堆叠绘图 ─────────────────────────────────────────────────
# bottom 从 0 开始，每层累加
bottom = np.zeros(n_groups)

colors = C_LAYERS[:len(component_names)]

for i, (name, vals) in enumerate(zip(component_names, vals_list)):
    bars = ax.bar(
        x_center, vals,
        width=BAR_W,
        bottom=bottom,
        color=colors[i],
        edgecolor='white',
        linewidth=0.5,
        label=name,
        zorder=2,
    )
    # 底部累加
    bottom += vals

# ── 样式 ─────────────────────────────────────────────────────
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#333333')
ax.spines['bottom'].set_color('#333333')
ax.spines['left'].set_linewidth(0.9)
ax.spines['bottom'].set_linewidth(0.9)

# y 轴网格（与 bar_grouped_hatch 一致）
ax.yaxis.grid(True, color='#EBEBEB', linewidth=0.7, linestyle='--', zorder=0)
ax.set_axisbelow(True)

# 刻度
ax.tick_params(length=3, direction='out', labelsize=9)

# 标签
ax.set_xticks(x_center)
ax.set_xticklabels(categories, fontsize=10)
ax.set_ylabel(YLABEL, fontsize=10)
ax.set_ylim(*YLIM)
ax.set_title(TITLE, fontsize=12, fontweight='bold', color='#333333', pad=8)

# 图例
leg = ax.legend(
    fontsize=9,
    loc='upper right',
    bbox_to_anchor=(1.01, 1.0),
    frameon=True,
    facecolor='white',
    edgecolor='#CCCCCC',
    labelspacing=0.35,
    handlelength=1.5,
    handletextpad=0.5,
    borderaxespad=0.3,
)

# ── 保存 ─────────────────────────────────────────────────────
output_path = Path('output/figures/stacked_bar_repro.png')
output_path.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(output_path, dpi=300, facecolor='white', bbox_inches='tight')
plt.close(fig)
print(f'✅ saved: {output_path}')
