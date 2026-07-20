"""
日历热力图（calendar heatmap）
特征：六边形网格（hexbin），按日/周展示时序活跃度，蓝色冷色阶
来源：参考 GitHub contribution graph 风格，适合展示每日活跃度、提交量等
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from matplotlib.colors import BoundaryNorm
from matplotlib.cm import ScalarMappable
import matplotlib.colorbar as cbar

# ── 全局样式 ─────────────────────────────────────────────────────
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['DejaVu Sans', 'Arial', 'Helvetica'],
    'text.usetex': False,
})

# ── 颜色 ────────────────────────────────────────────────────────
C_LOW   = '#EBF5FB'   # 最浅蓝（接近 0）
C_MID   = '#5499C7'   # 中蓝
C_HIGH  = '#1B3D6E'   # 深蓝（最高值）
C_WEEKEND = '#F5F5F5'  # 周末列底色

# ── 数据（请替换为你的数据）───────────────────────────────────
# 格式：{ 'YYYY-MM-DD': value }  或 pd.DataFrame
raw_data = {
    '2024-01-02': 3, '2024-01-03': 7, '2024-01-04': 12, '2024-01-05': 5,
    '2024-01-08': 8, '2024-01-09': 14, '2024-01-10': 6, '2024-01-11': 9,
    '2024-01-12': 4, '2024-01-15': 11, '2024-01-16': 18, '2024-01-17': 7,
    '2024-01-18': 5, '2024-01-19': 3, '2024-01-22': 9, '2024-01-23': 15,
    '2024-01-24': 22, '2024-01-25': 11, '2024-01-26': 6,
    '2024-01-29': 8, '2024-01-30': 13, '2024-01-31': 7,
    '2024-02-01': 5, '2024-02-02': 9, '2024-02-05': 14, '2024-02-06': 18,
    '2024-02-07': 11, '2024-02-08': 6, '2024-02-09': 4, '2024-02-12': 8,
    '2024-02-13': 16, '2024-02-14': 21, '2024-02-15': 9, '2024-02-16': 5,
    '2024-02-19': 7, '2024-02-20': 12, '2024-02-21': 19, '2024-02-22': 14,
    '2024-02-23': 8, '2024-02-26': 6, '2024-02-27': 11, '2024-02-28': 17,
    '2024-02-29': 9,
    '2024-03-01': 4, '2024-03-04': 8, '2024-03-05': 13, '2024-03-06': 16,
    '2024-03-07': 10, '2024-03-08': 5, '2024-03-11': 7, '2024-03-12': 14,
    '2024-03-13': 20, '2024-03-14': 12, '2024-03-15': 6, '2024-03-18': 9,
    '2024-03-19': 15, '2024-03-20': 18, '2024-03-21': 11, '2024-03-22': 7,
    '2024-03-25': 5, '2024-03-26': 10, '2024-03-27': 14, '2024-03-28': 19,
    '2024-03-29': 8,
}

# ── 参数配置 ──────────────────────────────────────────────────
START_DATE = '2024-01-01'
END_DATE   = '2024-03-31'
TITLE      = 'Daily Activity'
CBAR_LABEL = 'Contributions'
C_MAP      = 'Blues'          # matplotlib 内置蓝白渐变

# Hexbin 参数：每个格子代表一天
# x = 该日期属于第几周（从 START_DATE 起算）
# y = 星期几（0=Mon, 1=Tue, ..., 6=Sun）
# 这样每列是一周，每天一个六边形格子
CELL_SIZE  = 0.65    # inches

# ── 数据解析 ──────────────────────────────────────────────────
if isinstance(raw_data, dict):
    df = pd.DataFrame([
        {'date': pd.to_datetime(d, errors='coerce'), 'value': v}
        for d, v in raw_data.items()
    ]).dropna()
else:
    df = raw_data.copy()
    df['date'] = pd.to_datetime(df['date'], errors='coerce')

# 过滤日期范围
start = pd.to_datetime(START_DATE)
end   = pd.to_datetime(END_DATE)
df = df[(df['date'] >= start) & (df['date'] <= end)].copy()

# 补全缺失日期（value=0）
full_index = pd.date_range(start, end, freq='D')
df_full = pd.DataFrame({'date': full_index})
df_full['value'] = df_full['date'].map(
    df.set_index('date')['value']
).fillna(0).values

# 计算 x=周序号, y=星期几（0=Mon）
df_full['weekday'] = df_full['date'].dt.weekday  # Mon=0, Sun=6
df_full['days_since_start'] = (df_full['date'] - start).dt.days
df_full['week'] = df_full['days_since_start'] // 7

# 取出坐标和值
x  = df_full['week'].values.astype(float)
y  = df_full['weekday'].values.astype(float)
C  = df_full['value'].values.astype(float)

# 计算色阶边界
vmin = 0
vmax = max(C.max() * 1.05, 1)
N_LEVELS = 5
levels = np.linspace(vmin, vmax, N_LEVELS + 1)
norm = BoundaryNorm(levels, N_LEVELS)
cmap = plt.get_cmap(C_MAP)

# 计算画布尺寸
num_weeks = int(df_full['week'].max()) + 1
fig_w = num_weeks * CELL_SIZE + 1.2   # 左侧周标签 + 色轴
fig_h = 7 * CELL_SIZE + 0.8            # 7天 + 顶部月份标签

# ── 画布 ─────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(fig_w, fig_h))

# 画六边形热力图
hb = ax.hexbin(
    x, y, C,
    gridsize=int(num_weeks),
    cmap=cmap,
    norm=norm,
    linewidths=0.3,
    edgecolors='white',
    mincnt=0,
    zorder=2,
)

# 周末列淡灰底色（周六=5, 周日=6）
for week_i in range(num_weeks):
    for dy, day_label in enumerate(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']):
        y_pos = dy
        if y_pos in (5, 6):  # Sat or Sun
            col_color = C_WEEKEND
            rect = mpatches.FancyBboxPatch(
                (week_i - 0.5, y_pos - 0.5),
                1, 1,
                boxstyle='square,pad=0',
                facecolor=col_color,
                edgecolor='none',
                zorder=1
            )
            ax.add_patch(rect)

# ── 样式 ─────────────────────────────────────────────────────
# 月份标签（放在顶部）
months_shown = {}
for _, row in df_full.iterrows():
    month = row['date'].month
    week_i = row['week']
    if month not in months_shown:
        months_shown[month] = week_i

month_names = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
for month_num, week_start in sorted(months_shown.items(), key=lambda x: x[1]):
    ax.text(
        week_start, 7.1,
        month_names[month_num],
        fontsize=9.5, ha='left', va='bottom',
        color='#333333', fontweight='normal',
    )
    ax.axvline(week_start, color='#CCCCCC', lw=0.5, zorder=0)

# 左侧周标签
ax.text(-0.7, 3, 'Week', fontsize=8, ha='right', va='center', color='#666666')

# 左侧天数标签（每隔一天显示）
DAY_LABELS = ['Mon', '', 'Wed', '', 'Fri', '', '']
for i, lbl in enumerate(DAY_LABELS):
    if lbl:
        ax.text(-0.02, i, lbl, fontsize=8, ha='right', va='center', color='#666666')

# 隐藏 top/right spine，L 形
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#333333')
ax.spines['bottom'].set_color('#333333')
ax.spines['left'].set_linewidth(0.9)
ax.spines['bottom'].set_linewidth(0.9)

# 刻度
ax.tick_params(length=3, direction='out', labelsize=8)
ax.set_xticks([])
ax.set_yticks(range(7))
ax.set_yticklabels([])
ax.set_xlim(-0.5, num_weeks + 0.5)
ax.set_ylim(-0.5, 7.0)
ax.set_aspect('equal')
ax.grid(False)

# ── Colorbar ─────────────────────────────────────────────────
cbar_ax = fig.add_axes([0.93, 0.15, 0.025, 0.7])
cb = fig.colorbar(
    ScalarMappable(norm=norm, cmap=cmap),
    cax=cbar_ax,
    orientation='vertical',
    shrink=0.7,
)
cb.set_label(CBAR_LABEL, fontsize=9)
cb.ax.tick_params(labelsize=8)

# ── 标题 ─────────────────────────────────────────────────────
ax.set_title(TITLE, fontsize=12, fontweight='bold', color='#333333', pad=6)

# ── 保存 ─────────────────────────────────────────────────────
from pathlib import Path

output_path = Path('output/figures/calendar_heatmap_repro.png')
output_path.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(output_path, dpi=300, facecolor='white', bbox_inches='tight')
plt.close(fig)
print(f'✅ saved: {output_path}')
