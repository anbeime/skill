"""
气泡图（bubble chart）
特征：x/y 平面 + size 编码第三维，圆形气泡，serif + usetex 风格
来源：继承 scatter_tsne_cluster 的聚类表达，加入第三维 size
"""

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# ── 全局样式（与 scatter_tsne_cluster 一致）───────────────────
plt.rcParams.update({
    'text.usetex': True,
    'font.family': 'serif',
    'font.serif': ['Computer Modern Roman', 'STIX Two Text', 'DejaVu Serif'],
    'axes.unicode_minus': False,
})

# ── 颜色（沿用 scatter_tsne 的语义色阶）──────────────────────
C_MAIN  = '#1B3D6E'   # 主类（深蓝）
C_CLASS = ['#6A4C93', '#D651A0', '#FF8A65', '#FFB74D', '#C888E8']

# ── 数据（请替换为你的数据）───────────────────────────────────
# x, y = 两个维度（位置），s = size（第三维），label = 图例标签，color = 颜色
bubbles = [
    {'x': 10,  'y': 20,  's': 80,  'label': 'Method A'},
    {'x': 15,  'y': 35,  's': 120, 'label': 'Method B'},
    {'x': 25,  'y': 15,  's': 200, 'label': 'Method C'},
    {'x': 30,  'y': 45,  's': 60,  'label': 'Method D'},
    {'x': 40,  'y': 30,  's': 150, 'label': 'Method E'},
    {'x': 35,  'y': 22,  's': 90,  'label': 'Method F'},
]

# 主方法名称（图例会加粗）
MAIN_METHOD = 'Method C'

# ── 参数配置 ─────────────────────────────────────────────────
TITLE    = r'\textbf{Bubble Chart: Accuracy vs Efficiency}'
XLABEL   = r'\textit{Accuracy (\%)}'
YLABEL   = r'\textit{Efficiency (speedup)}'
XLIM     = (5, 50)
YLIM     = (10, 55)
SIZE_MIN = 60
SIZE_MAX = 600
SIZE_SCALE = 'sqrt'   # 推荐 sqrt 避免大值主导

# ── size 映射函数 ────────────────────────────────────────────
def scale_size(s, vmin, vmax, smin, smax, mode='sqrt'):
    frac = (s - vmin) / (vmax - vmin) if vmax != vmin else 0.5
    if mode == 'sqrt':
        frac = np.sqrt(frac)
    return smin + frac * (smax - smin)

vmin = min(b['s'] for b in bubbles)
vmax = max(b['s'] for b in bubbles)

# ── 画布 ─────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8.0, 6.0))

# ── 画气泡 ─────────────────────────────────────────────────
for idx, b in enumerate(bubbles):
    color = C_MAIN if b['label'] == MAIN_METHOD else C_CLASS[idx % len(C_CLASS)]
    size  = scale_size(b['s'], vmin, vmax, SIZE_MIN, SIZE_MAX, SIZE_SCALE)
    is_main = b['label'] == MAIN_METHOD

    ax.scatter(
        b['x'], b['y'],
        s=size,
        c=color,
        alpha=0.65,
        edgecolors='white',
        linewidths=1.0,
        zorder=3,
        label=b['label'],
    )
    # 气泡内标签（仅大气泡）
    if size > 120:
        ax.text(
            b['x'], b['y'],
            b['label'].replace('Method ', 'M'),
            fontsize=7.5, ha='center', va='center',
            color='white', fontweight='bold' if is_main else 'normal',
            zorder=4,
        )

# ── 样式 ─────────────────────────────────────────────────────
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#333333')
ax.spines['bottom'].set_color('#333333')
ax.spines['left'].set_linewidth(0.9)
ax.spines['bottom'].set_linewidth(0.9)

# 点线网格（与 scatter_tsne 一致）
ax.grid(True, color='#E0E0E0', linewidth=0.6, linestyle=':', zorder=0)
ax.set_axisbelow(True)

# 刻度
ax.tick_params(length=4, direction='in', labelsize=10, color='#333333')

# 标签
ax.set_xlim(*XLIM)
ax.set_ylim(*YLIM)
ax.set_xlabel(XLABEL, fontsize=12)
ax.set_ylabel(YLABEL, fontsize=12)
ax.set_title(TITLE, fontsize=13, pad=10)

# ── 图例 ─────────────────────────────────────────────────────
# 排序：主方法在前
from matplotlib.lines import Line2D
legend_elements = []
labels_seen = []
for b in bubbles:
    if b['label'] in labels_seen:
        continue
    labels_seen.append(b['label'])
    color = C_MAIN if b['label'] == MAIN_METHOD else C_CLASS[list(bubbles).index(b) % len(C_CLASS)]
    is_main = b['label'] == MAIN_METHOD
    size = scale_size(b['s'], vmin, vmax, SIZE_MIN, SIZE_MAX, SIZE_SCALE)
    legend_elements.append(
        Line2D([0], [0], marker='o', color='white',
               markerfacecolor=color, markersize=np.sqrt(size) / 3.5,
               markeredgecolor='white', markeredgewidth=0.5,
               label=b['label'],
               linewidth=0)
    )

leg = ax.legend(
    handles=legend_elements,
    fontsize=9,
    loc='upper left',
    bbox_to_anchor=(1.01, 1.0),
    frameon=True,
    facecolor='white',
    edgecolor='#CCCCCC',
    labelspacing=0.4,
    handlelength=1.0,
    borderaxespad=0.3,
)
for text in leg.get_texts():
    if text.get_text() == MAIN_METHOD:
        text.set_fontweight('bold')

# ── 保存 ─────────────────────────────────────────────────────
output_path = Path('output/figures/bubble_chart_repro.png')
output_path.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(output_path, dpi=300, facecolor='white', bbox_inches='tight')
plt.close(fig)
print(f'✅ saved: {output_path}')
