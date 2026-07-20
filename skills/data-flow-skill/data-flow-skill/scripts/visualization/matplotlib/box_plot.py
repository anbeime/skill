"""
箱线图（box plot）
特征：多组数据分布对比，4边可见箱体，y轴浅灰网格，中位线红色加粗
来源：学术统计图表风格，复用 bar_grouped_hatch 配色体系
"""

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# ── 全局样式（复用 bar_grouped_hatch 的 serif + usetex 风格）─────────────
plt.rcParams.update({
    'text.usetex': True,
    'font.family': 'serif',
    'font.serif': ['Computer Modern Roman', 'STIX Two Text', 'DejaVu Serif'],
    'axes.unicode_minus': False,
})

# ── 颜色 ──────────────────────────────────────────────────────
C_BOX   = '#5499C7'   # 箱体主色（蓝）
C_MED   = '#CC2200'   # 中位线（红，与 bar_paired_delta delta 色一致）
C_OUTL  = '#D651A0'   # 异常值（粉，与 scatter_tsne 一致）
C_WHISK = '#333333'   # 须线颜色

# ── 数据（请替换为你的数据）───────────────────────────────────
# 每组数据可以是 list 或 np.array
data = {
    'Method A': [23.5, 25.1, 24.8, 26.2, 27.0, 25.5, 24.9, 26.8, 25.0, 24.3],
    'Method B': [28.3, 29.1, 27.8, 30.2, 29.5, 28.9, 30.1, 29.0, 28.7, 29.3],
    'Ours':     [31.2, 32.5, 31.8, 33.1, 32.0, 31.5, 32.8, 33.4, 31.9, 32.2],
}

labels = list(data.keys())
values = [np.array(v) for v in data.values()]

# ── 参数配置 ─────────────────────────────────────────────────
TITLE   = r'\textbf{Distribution Comparison}'
XLABEL  = r'\textbf{Method}'
YLABEL  = r'\textit{Accuracy (\%)}'
YLIM    = (15, 40)
BOX_W   = 0.35

# ── 画布 ─────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(7.5, 5.0))

x_pos = np.arange(len(labels))

# 画箱线图
bp = ax.boxplot(
    values,
    positions=x_pos,
    widths=BOX_W,
    patch_artist=True,      # 允许填充颜色
    showmeans=True,        # 显示均值
    meanline=False,        # 均值用 marker，不用线
    whiskerprops=dict(color=C_WHISK, linewidth=1.2),
    capprops=dict(color=C_WHISK, linewidth=1.2),
    flierprops=dict(marker='o', markerfacecolor=C_OUTL, markersize=5,
                    markeredgecolor=C_WHISK, markeredgewidth=0.5),
    medianprops=dict(color=C_MED, linewidth=2.0),
    meanprops=dict(marker='D', markerfacecolor='white', markeredgecolor=C_WHISK,
                   markersize=5, markeredgewidth=0.8),
)

# 填充箱体颜色
for patch in bp['boxes']:
    patch.set_facecolor(C_BOX)
    patch.set_alpha(0.75)
    patch.set_edgecolor(C_WHISK)
    patch.set_linewidth(1.0)

# 隐藏 top/right spine（学术风格）
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#333333')
ax.spines['bottom'].set_color('#333333')
ax.spines['left'].set_linewidth(1.2)
ax.spines['bottom'].set_linewidth(1.2)

# y 轴网格（与 bar_grouped_hatch 一致）
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

# 标题
ax.set_title(TITLE, fontsize=13, pad=8)

# 图例（均值 marker 说明）
from matplotlib.lines import Line2D
legend_elements = [
    Line2D([0], [0], marker='D', color='white', markerfacecolor='white',
           markeredgecolor=C_WHISK, markersize=5, markeredgewidth=0.8,
           label=r'\textit{Mean}'),
    Line2D([0], [0], color=C_MED, linewidth=2.0, label=r'\textit{Median}'),
]
ax.legend(handles=legend_elements, fontsize=9, loc='upper right',
          frameon=True, facecolor='white', edgecolor='#CCCCCC')

# ── 保存 ─────────────────────────────────────────────────────
output_path = Path('output/figures/box_plot_repro.png')
output_path.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(output_path, dpi=300, facecolor='white', bbox_inches='tight')
plt.close(fig)
print(f'✅ saved: {output_path}')
