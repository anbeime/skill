"""
平行坐标图（parallel coordinates）
特征：多垂直轴，每条线代表一个方法在多个维度上的表现
来源：经典多维方法对比图表，学术和工程场景通用
"""

import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import numpy as np

# ── 全局样式 ─────────────────────────────────────────────────────
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['DejaVu Sans', 'Arial', 'Helvetica'],
    'text.usetex': False,
})

# ── 颜色 ──────────────────────────────────────────────────────
C_MAIN   = '#1B3D6E'   # 主方法（深蓝）
C_BASE   = '#A8C8E8'   # baseline（浅钢蓝）
C_OTHERS = ['#5499C7', '#2CA02C', '#D651A0', '#FF7F0E']

# ── 数据（请替换为你的数据）───────────────────────────────────
# 维度名称
dimensions = ['Accuracy', 'Latency', 'Memory', 'FLOPs', 'Robustness']

# 方法 -> 各维度值（建议先归一化到 [0, 1]，或传入 raw 值由脚本自动归一化）
data = {
    'Method A': [0.82, 0.45, 0.60, 0.55, 0.70],
    'Method B': [0.75, 0.60, 0.50, 0.65, 0.80],
    'Ours':     [0.88, 0.35, 0.70, 0.40, 0.85],
    'Baseline': [0.70, 0.80, 0.40, 0.80, 0.60],
}

# 若传入 raw 值（非归一化），设为 False
NORMALIZED = True

# 主方法名称（图例中会突出显示）
MAIN_METHOD = 'Ours'

# ── 参数配置 ──────────────────────────────────────────────────
TITLE     = r'Method Comparison on Multiple Dimensions'
YLABEL    = 'Normalized Score'
LEFT      = 0.10
RIGHT     = 0.92
TOP       = 0.14
AXIS_COL  = '#333333'
AXIS_LW   = 0.8
GRID_COL  = '#EBEBEB'
GRID_LW   = 0.6
TICK_LEN  = 3
LINE_LW   = 1.8
ALPHA     = 0.75

# ── 归一化（如果数据不是 [0,1] 范围）─────────────────────────
if not NORMALIZED:
    all_vals = []
    for vals in data.values():
        all_vals.extend(vals)
    vmin, vmax = min(all_vals), max(all_vals)
    data = {k: [(v - vmin) / (vmax - vmin) for v in vals] for k, vals in data.items()}

# ── 布局 ─────────────────────────────────────────────────────
n_dims = len(dimensions)
n_methods = len(data)
x_pos = np.linspace(0, 1, n_dims)   # 每个维度在 x 轴上的位置（0~1 归一化）

# 颜色分配
def get_color(method_name, idx):
    if method_name == MAIN_METHOD:
        return C_MAIN
    elif method_name == 'Baseline':
        return C_BASE
    else:
        return C_OTHERS[idx % len(C_OTHERS)]

# ── 画布 ─────────────────────────────────────────────────────
fig_w = 9.0
fig_h = 5.5
fig, ax = plt.subplots(figsize=(fig_w, fig_h))

ax.set_xlim(0, 1)
ax.set_ylim(0, 1)

# ── 画垂直轴 ─────────────────────────────────────────────────
for xi in x_pos:
    ax.plot([xi, xi], [0, 1], color=AXIS_COL, lw=AXIS_LW, zorder=1)

# 水平参考线（y 轴网格）
for y_ref in np.arange(0.2, 1.0, 0.2):
    ax.axhline(y_ref, color=GRID_COL, lw=GRID_LW, linestyle='--', zorder=0)

# ── 画每条线 ─────────────────────────────────────────────────
colors = []
for idx, (method, vals) in enumerate(data.items()):
    color = get_color(method, idx)
    colors.append(color)
    lw = LINE_LW if method == MAIN_METHOD else LINE_LW - 0.4
    ax.plot(
        x_pos, vals,
        color=color,
        lw=lw,
        alpha=ALPHA if method != MAIN_METHOD else 1.0,
        zorder=3,
        label=method,
    )
    # 数据点
    ax.scatter(
        x_pos, vals,
        color=color,
        s=30 if method == MAIN_METHOD else 18,
        zorder=4,
        edgecolors='white',
        linewidths=0.5,
    )

# ── 坐标轴标签 ───────────────────────────────────────────────
for xi, dim in zip(x_pos, dimensions):
    ax.text(xi, -0.06, dim, fontsize=10, ha='center', va='top', color='#333333')

ax.set_ylabel(YLABEL, fontsize=10, color='#333333')
ax.set_title(TITLE, fontsize=12, fontweight='bold', color='#333333', pad=10)

# ── 样式 ─────────────────────────────────────────────────────
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.spines['bottom'].set_visible(False)

ax.tick_params(length=TICK_LEN, direction='out', labelsize=8)
ax.set_xticks([])
ax.set_yticks(np.arange(0.2, 1.0, 0.2))
ax.set_yticklabels([f'{int(v*100)}%' for v in np.arange(0.2, 1.0, 0.2)], fontsize=8)
ax.grid(False)

# ── 图例 ─────────────────────────────────────────────────────
legend_elements = []
for method, vals in data.items():
    color = get_color(method, list(data.keys()).index(method))
    is_main = (method == MAIN_METHOD)
    lw = LINE_LW if is_main else LINE_LW - 0.4
    legend_elements.append(
        mlines.Line2D([0], [0], color=color, lw=lw,
                      alpha=ALPHA if not is_main else 1.0,
                      label=method,
                      marker='o', markersize=4,
                      markerfacecolor=color, markeredgecolor='white',
                      markeredgewidth=0.3)
    )

leg = ax.legend(
    handles=legend_elements,
    fontsize=9,
    loc='upper right',
    bbox_to_anchor=(1.01, 1.0),
    frameon=True,
    facecolor='white',
    edgecolor='#CCCCCC',
    labelspacing=0.4,
    handlelength=2.0,
)
for text in leg.get_texts():
    if text.get_text() == MAIN_METHOD:
        text.set_fontweight('bold')

# ── 保存 ─────────────────────────────────────────────────────
from pathlib import Path

output_path = Path('output/figures/parallel_coordinates_repro.png')
output_path.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(output_path, dpi=300, facecolor='white', bbox_inches='tight')
plt.close(fig)
print(f'✅ saved: {output_path}')
