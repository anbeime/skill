"""
小提琴图（violin plot）
特征：数据密度分布可视化，内部叠加 mini box plot（中位线+四分位线）
来源：学术统计图表风格，与 box_plot 共用配色体系
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path

# ── 全局样式（与 box_plot 完全一致）────────────────────────────
plt.rcParams.update({
    'text.usetex': True,
    'font.family': 'serif',
    'font.serif': ['Computer Modern Roman', 'STIX Two Text', 'DejaVu Serif'],
    'axes.unicode_minus': False,
})

# ── 颜色（与 box_plot 一致）──────────────────────────────────
C_VIOLIN = '#5499C7'   # 小提琴主体（蓝）
C_BOX    = '#1B3D6E'   # 内部叠加箱体（深蓝）
C_MED    = '#CC2200'   # 中位线（红）
C_OUTL   = '#D651A0'   # 异常值（粉）

# ── 数据（请替换为你的数据）───────────────────────────────────
data = {
    'Method A': [23.5, 25.1, 24.8, 26.2, 27.0, 25.5, 24.9, 26.8, 25.0, 24.3],
    'Method B': [28.3, 29.1, 27.8, 30.2, 29.5, 28.9, 30.1, 29.0, 28.7, 29.3],
    'Ours':     [31.2, 32.5, 31.8, 33.1, 32.0, 31.5, 32.8, 33.4, 31.9, 32.2],
}

labels = list(data.keys())
values = [np.array(v) for v in data.values()]

# ── 参数配置 ─────────────────────────────────────────────────
TITLE   = r'\textbf{Distribution Comparison (Violin)}'
XLABEL  = r'\textbf{Method}'
YLABEL  = r'\textit{Accuracy (\%)}'
YLIM    = (15, 40)
VIOLIN_ALPHA = 0.6

# ── 画布 ─────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(7.5, 5.0))

x_pos = np.arange(len(labels))

# 画小提琴
vp = ax.violinplot(
    values,
    positions=x_pos,
    widths=0.5,
    showmeans=False,
    showmedians=False,
)

# 设置小提琴颜色和透明度
for i, body in enumerate(vp['bodies']):
    body.set_facecolor(C_VIOLIN)
    body.set_alpha(VIOLIN_ALPHA)
    body.set_edgecolor('#333333')
    body.set_linewidth(1.0)

# 隐藏须线和caps（保留小提琴形状）
for partname in ('cbars', 'cmins', 'cmaxes'):
    parts = vp.get(partname)
    if parts is not None:
        parts.set_visible(False)

# ── 内部叠加 mini box plot ──────────────────────────────────
# 手动计算四分位和中位线
def get_stats(arr):
    arr = np.sort(arr)
    q1 = np.percentile(arr, 25)
    med = np.percentile(arr, 50)
    q3 = np.percentile(arr, 75)
    iqr = q3 - q1
    lo = max(arr.min(), q1 - 1.5 * iqr)
    hi = min(arr.max(), q3 + 1.5 * iqr)
    return lo, q1, med, q3, hi

for i, (xi, vals) in enumerate(zip(x_pos, values)):
    lo, q1, med, q3, hi = get_stats(vals)
    bw = 0.12  # mini box 宽度

    # 箱体（透明深蓝）
    ax.fill_between(
        [xi - bw, xi + bw], [q1, q1], [q3, q3],
        color=C_BOX, alpha=0.6, zorder=4
    )
    # 中位线（红色加粗）
    ax.plot([xi - bw, xi + bw], [med, med],
            color=C_MED, linewidth=2.0, zorder=5)
    # 须线（连接箱体上下端）
    ax.plot([xi, xi], [lo, q1], color='#333333', linewidth=1.2, zorder=4)
    ax.plot([xi, xi], [q3, hi], color='#333333', linewidth=1.2, zorder=4)
    # 须线端点横线
    ax.plot([xi - bw * 0.6, xi + bw * 0.6], [lo, lo], color='#333333', lw=1.2, zorder=4)
    ax.plot([xi - bw * 0.6, xi + bw * 0.6], [hi, hi], color='#333333', lw=1.2, zorder=4)

# ── 样式 ─────────────────────────────────────────────────────
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#333333')
ax.spines['bottom'].set_color('#333333')
ax.spines['left'].set_linewidth(1.2)
ax.spines['bottom'].set_linewidth(1.2)

# y 轴网格（与 bar_grouped_hatch / box_plot 一致）
ax.yaxis.grid(True, color='#EBEBEB', linewidth=0.7, linestyle='--', zorder=0)
ax.set_axisbelow(True)

# 刻度
ax.tick_params(length=4, direction='in', labelsize=10)

# 标签
ax.set_xticks(x_pos)
ax.set_xticklabels(labels, fontsize=11)
ax.set_xlabel(XLABEL, fontsize=11)
ax.set_ylabel(YLABEL, fontsize=11)
ax.set_ylim(*YLIM)
ax.set_title(TITLE, fontsize=13, pad=8)

# 图例
from matplotlib.lines import Line2D
legend_elements = [
    Line2D([0], [0], color=C_MED, linewidth=2.0, label=r'\textit{Median}'),
    mpatches.Patch(facecolor=C_VIOLIN, alpha=VIOLIN_ALPHA, edgecolor='#333333',
                   label=r'\textit{Density}'),
]
ax.legend(handles=legend_elements, fontsize=9, loc='upper right',
          frameon=True, facecolor='white', edgecolor='#CCCCCC')

# ── 保存 ─────────────────────────────────────────────────────
output_path = Path('output/figures/violin_plot_repro.png')
output_path.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(output_path, dpi=300, facecolor='white', bbox_inches='tight')
plt.close(fig)
print(f'✅ saved: {output_path}')
