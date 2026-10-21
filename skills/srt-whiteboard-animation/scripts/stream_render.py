#!/usr/bin/env python3
"""
流式笔迹动画 - 单图渲染入口

把一张彩色图片渲染成「笔尖沿连续轨迹滑行、边走边落墨」的白板动画。
全程分三个段落：
  起笔(ink)   笔尖沿墨迹流铺下黑色线稿
  添彩(color) 同一条轨迹回头，笔尖换上原色把画面点亮
  凝视(gaze)  收笔后停留，展示完整原图

与“逐格跳变”的做法不同：本渲染器把绘制顺序视作笔尖的运动折线，
在相邻落点之间做插值，墨刷随笔尖滑动连续落墨，形成连贯的笔迹流。
"""
from __future__ import annotations

import argparse
import datetime
import math
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import cv2
import numpy as np

# ──────────────────────────────────────────────────────────────
# 资源定位
# ──────────────────────────────────────────────────────────────
_SCRIPT_DIR = Path(__file__).resolve().parent
_ASSETS_DIR = _SCRIPT_DIR.parent / "assets"
DEFAULT_HAND_PNG = _ASSETS_DIR / "drawing-hand.png"


def _imread_any(path: str | Path, flags: int = cv2.IMREAD_COLOR) -> np.ndarray | None:
    """
    读取图片，兼容含中文/空格等非 ASCII 字符的 Windows 路径。
    先用 np.fromfile 读字节，再交给 cv2.imdecode 解码，
    绕过 cv2.imread 对非 ASCII 路径的兼容性问题。
    """
    raw = np.fromfile(str(path), dtype=np.uint8)
    if raw.size == 0:
        return None
    return cv2.imdecode(raw, flags)


# ──────────────────────────────────────────────────────────────
# 渲染参数集中处
# ──────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Config:
    fps: int = 60                  # 高频输出让笔尖移动更接近连续书写
    grid_edge: int = 10            # 更小的网格减少线稿揭示的块状感
    sample_step: int = 2           # 笔尖轨迹的像素采样间距
    cap_long_edge: int = 1080      # 输入图长边上限
    brush_radius: int = 40         # 添彩阶段圆形墨刷半径
    ink_weight: int = 2            # 线稿段权重：为观察笔迹留出更多时间
    color_weight: int = 1          # 添彩段权重
    gaze_seconds: float = 3.0      # 凝视段基准秒数
    ink_threshold: int = 10        # 像素灰度低于此值视为“墨迹”
    ink_reveal_radius: int = 4     # 笔尖每段轨迹可揭示线稿的半径
    target_hand_height: int = 493  # 手部素材缩放后的目标高度（按 1080p 调校）
    # 笔尖在素材中的归一化坐标（0..1），决定落墨点对齐到素材的哪个像素。
    # 内置 drawing-hand.png 裁剪后，笔尖落在图像左上角，故锚点取 (0, 0)。
    # 这里描述的是真实落墨接触点，而非手部图像的外框。
    tip_anchor_x: float = 0.0
    tip_anchor_y: float = 0.0
    canvas_hex: str = "#F6F1E3"    # 画布底色
    match_bg: bool = True          # 把原图背景染成画布底色，使起笔/上色背景一致
    match_bg_threshold: int = 28   # 与原图背景色差异小于此值视为背景（BGR 三通道和）
    steps_per_frame: int = 4       # 每帧推进的落点数基准
    # ── contour-wipe 上色模式专用 ──
    color_fill: str = "contour-wipe"  # 上色风格: "contour-wipe" 轮廓感知自上而下扫描(默认) | "brush" 沿轨迹刷
    wipe_decay: float = 0.86       # 阻力场逐行向下衰减系数（半衰期≈4.6px）
    wipe_delay_ratio: float = 0.04  # 轮廓处前沿被扣减的像素比例（×h，钳制到[12,52]）
    wipe_blocks: int = 18          # 笔尖横向来回扫动的趟数
    # ── 起笔段自适应停顿（模拟"换笔呼吸"节奏）──
    # pause_mode: "heavy" 明显停顿(默认)；"auto" 按内容密度自动分档；"off" 关闭停顿；"light" 少量
    pause_mode: str = "heavy"
    pause_ratio_heavy: float = 0.03   # 低密度(慢节奏)停顿比例：约 3% 帧用作停顿
    pause_ratio_light: float = 0.008  # 中密度停顿比例：约 0.8%
    # 密度分档阈值：用"每格帧数"(frames_per_cell) 衡量动画时长相对内容的富余度。
    # >= heavy_fpc 有大段富余 → heavy 档(多停顿)；>= light_fpc 适中 → light 档；
    # < light_fpc 内容密集、时长紧张 → 不停顿。
    pause_heavy_fpc: float = 0.7
    pause_light_fpc: float = 0.4
    # ── 笔迹路径模式 ──
    # ink_path_mode: "grid" 网格格中心插值(默认) | "skeleton" 骨架级像素追踪
    ink_path_mode: str = "grid"
    skeleton_min_points: int = 8        # 骨架笔画最少点数（过滤碎片）
    skeleton_resample_spacing: float = 2.5  # 骨架重采样间距（像素）


# ──────────────────────────────────────────────────────────────
# 小工具
# ──────────────────────────────────────────────────────────────
def _hex_to_bgr(hex_color: str) -> np.ndarray:
    digits = hex_color.lstrip("#")
    if len(digits) != 6:
        raise ValueError(f"非法颜色值: {hex_color}")
    r = int(digits[0:2], 16)
    g = int(digits[2:4], 16)
    b = int(digits[4:6], 16)
    return np.array([b, g, r], dtype=np.uint8)


def _bounding_box(mask: np.ndarray) -> tuple[tuple[int, int], tuple[int, int]]:
    ys, xs = np.where(mask > 0)
    if len(xs) == 0:
        return (0, 0), (0, 0)
    return (int(xs.min()), int(ys.min())), (int(xs.max()), int(ys.max()))


# ──────────────────────────────────────────────────────────────
# 墨迹格分块
# ──────────────────────────────────────────────────────────────
def _to_grid_blocks(image: np.ndarray, edge: int) -> np.ndarray:
    """把 HxW（x C）图像切成 (行数, 列数, edge, edge[, C]) 的分块视图。"""
    image = np.ascontiguousarray(image)
    h, w = image.shape[:2]
    if h % edge or w % edge:
        raise ValueError(f"图像尺寸 {w}x{h} 必须是 {edge} 的整数倍")
    rows, cols = h // edge, w // edge
    if image.ndim == 2:
        return image.reshape(rows, edge, cols, edge).transpose(0, 2, 1, 3)
    return image.reshape(rows, edge, cols, edge, image.shape[2]).transpose(0, 2, 1, 3, 4)


def _active_mask(threshold_map: np.ndarray, edge: int, threshold: int) -> np.ndarray:
    """哪些网格含墨迹：块内存在灰度低于阈值的像素即为真。"""
    blocks = _to_grid_blocks(threshold_map, edge)
    return np.any(blocks < threshold, axis=(2, 3))


# ──────────────────────────────────────────────────────────────
# 墨迹流聚类 + 密度梯度游走
# ──────────────────────────────────────────────────────────────
def _label_components(active: np.ndarray) -> tuple[np.ndarray, int]:
    """对墨迹格做 8 连通连通域标记，返回 (标签图, 域数)。"""
    n, labels = cv2.connectedComponents(active.astype(np.uint8), connectivity=8)
    return labels, n - 1  # 去掉背景标签 0


def _component_cells(labels: np.ndarray, label: int) -> list[tuple[int, int]]:
    coords = np.argwhere(labels == label)
    return [(int(r), int(c)) for r, c in coords]


def _merge_small_components(
    components: list[list[tuple[int, int]]],
    merge_threshold: int,
) -> list[list[tuple[int, int]]]:
    """
    把小连通域（格数 ≤ merge_threshold）合并到空间最近的大连通域。
    避免大量 1-2 格的碎片穿插在大块文字之间，导致“画一块字没画完就跳走”。
    若没有大连通域可并入，则保留原样（不丢弃任何墨迹）。
    """
    if not components:
        return components
    big = [c for c in components if len(c) > merge_threshold]
    small = [c for c in components if len(c) <= merge_threshold]
    if not small or not big:
        return components

    # 预算每个大区域的质心
    centroids = []
    for cells in big:
        rs = [c[0] for c in cells]
        cs = [c[1] for c in cells]
        centroids.append((sum(rs) / len(rs), sum(cs) / len(cs)))

    # 每个小碎片并入最近的大区域
    merged = [list(cells) for cells in big]  # 拷贝，可追加
    for cells in small:
        rs = [c[0] for c in cells]
        cs = [c[1] for c in cells]
        cr = sum(rs) / len(rs)
        cc = sum(cs) / len(cs)
        best = min(
            range(len(big)),
            key=lambda i: (centroids[i][0] - cr) ** 2 + (centroids[i][1] - cc) ** 2,
        )
        merged[best].extend(cells)
    return merged


def _bounds(cells: Sequence[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _split_bridge_connected_component(
    cells: list[tuple[int, int]],
    min_side_cells: int = 20,
) -> list[list[tuple[int, int]]]:
    """Split a very wide component when it is connected only by a thin bridge.

    A baseline, arrow, or stray outline can join separate objects into one
    connected component.  Drawing that component with one nearest-neighbour
    walk makes the pen alternate between those objects.  Valleys in the
    vertical ink projection are reliable weak-bridge signals at grid scale.
    """
    if len(cells) < min_side_cells * 2:
        return [cells]

    min_row, min_col, max_row, max_col = _bounds(cells)
    height = max_row - min_row + 1
    width = max_col - min_col + 1
    if width < 16 or height < 10:
        return [cells]

    counts = {col: 0 for col in range(min_col, max_col + 1)}
    for _, col in cells:
        counts[col] += 1
    valley_limit = max(3, int(np.ceil(height * 0.30)))
    edge_guard = 4
    valleys: list[tuple[int, int]] = []
    start: int | None = None
    for col in range(min_col, max_col + 2):
        low = col <= max_col and counts[col] <= valley_limit
        if low and start is None:
            start = col
        elif not low and start is not None:
            end = col - 1
            if (
                end - start + 1 >= 2
                and start > min_col + edge_guard
                and end < max_col - edge_guard
            ):
                valleys.append((start, end))
            start = None
    if not valleys:
        return [cells]

    # Prefer the broadest empty corridor.  It is much less likely to be an
    # internal detail of a character than a one-column dip.
    start, end = max(valleys, key=lambda band: (band[1] - band[0], -band[0]))
    cut = (start + end) // 2
    left = [cell for cell in cells if cell[1] <= cut]
    right = [cell for cell in cells if cell[1] > cut]
    if len(left) < min_side_cells or len(right) < min_side_cells:
        return [cells]
    return (
        _split_bridge_connected_component(left, min_side_cells)
        + _split_bridge_connected_component(right, min_side_cells)
    )


def _split_bridge_connected_components(
    components: list[list[tuple[int, int]]],
) -> list[list[tuple[int, int]]]:
    return [
        piece
        for cells in components
        for piece in _split_bridge_connected_component(cells)
    ]


def _boxes_touch(
    first: tuple[int, int, int, int],
    second: tuple[int, int, int, int],
    margin: int = 2,
) -> bool:
    """Whether two component boxes belong to the same visual region."""
    a_top, a_left, a_bottom, a_right = first
    b_top, b_left, b_bottom, b_right = second
    return not (
        a_right + margin < b_left
        or b_right + margin < a_left
        or a_bottom + margin < b_top
        or b_bottom + margin < a_top
    )


def _group_adjacent_stroke_groups(
    groups: list[tuple[str, list[tuple[int, int]]]],
) -> list[list[tuple[str, list[tuple[int, int]]]]]:
    """Keep overlapping label parts and outline pieces in one draw region."""
    regions: list[list[tuple[str, list[tuple[int, int]]]]] = []
    boxes: list[tuple[int, int, int, int]] = []
    for group in groups:
        group_box = _bounds(group[1])
        touching = [index for index, box in enumerate(boxes) if _boxes_touch(group_box, box)]
        if not touching:
            regions.append([group])
            boxes.append(group_box)
            continue
        target = touching[0]
        regions[target].append(group)
        top, left, bottom, right = boxes[target]
        boxes[target] = (
            min(top, group_box[0]), min(left, group_box[1]),
            max(bottom, group_box[2]), max(right, group_box[3]),
        )
        # Merge any regions newly bridged by the expanded box.
        for index in reversed(touching[1:]):
            regions[target].extend(regions.pop(index))
            other = boxes.pop(index)
            top, left, bottom, right = boxes[target]
            boxes[target] = (
                min(top, other[0]), min(left, other[1]),
                max(bottom, other[2]), max(right, other[3]),
            )
    return regions


def classify_stroke_groups(
    active: np.ndarray,
) -> list[tuple[str, list[tuple[int, int]]]]:
    """Classify connected ink regions as a main subject, text, or local contour."""
    labels, count = _label_components(active)
    components = [
        _component_cells(labels, label)
        for label in range(1, count + 1)
    ]
    components = [cells for cells in components if cells]
    if not components:
        return []

    # A long ground line may connect a mountain, a character, and a crowd.
    # Split that weak connection before any region ordering is decided.
    components = _split_bridge_connected_components(components)

    # 合并小碎片到最近的大区域，避免碎片打断大块文字的连续绘制
    total_cells = sum(len(c) for c in components)
    merge_threshold = max(3, int(total_cells * 0.005))
    components = _merge_small_components(components, merge_threshold)

    subject_index = max(range(len(components)), key=lambda index: len(components[index]))
    groups: list[tuple[str, list[tuple[int, int]], tuple[int, int, int]]] = []
    for index, cells in enumerate(components):
        min_row, min_col, max_row, max_col = _bounds(cells)
        height = max_row - min_row + 1
        width = max_col - min_col + 1
        density = len(cells) / (height * width)
        if index == subject_index:
            kind, rank = "subject", 0
        elif height >= 2 and width / height >= 2.2 and density >= 0.5:
            kind, rank = "text", 1
        else:
            kind, rank = "contour", 2
        groups.append((kind, cells, (rank, min_row, min_col)))

    groups.sort(key=lambda group: group[2])
    return [(kind, cells) for kind, cells, _ in groups]


def _density_seed(cells: Sequence[tuple[int, int]], radius: int = 2) -> tuple[int, int]:
    """挑局部邻居最密的格子作为起笔点，模拟“从墨最浓处下笔”。"""
    cell_set = set(cells)
    best = cells[0]
    best_score = -1
    for (r, c) in cells:
        score = sum(
            1
            for dr in range(-radius, radius + 1)
            for dc in range(-radius, radius + 1)
            if (r + dr, c + dc) in cell_set
        )
        if score > best_score:
            best_score = score
            best = (r, c)
    return best


def _gradient_walk(cells: Sequence[tuple[int, int]]) -> list[tuple[int, int]]:
    """
    密度梯度引导的贪心游走：从密度最高的种子格出发，每步选择
    “未访问邻居中局部密度最高、且与来向夹角最小”的格子，
    形成“尽量沿着墨迹、少折返”的连续笔迹。
    无邻居可达时跳到全局最近的未访问格继续。
    """
    if not cells:
        return []

    cell_set = set(cells)
    seed = _density_seed(cells)
    visited: set[tuple[int, int]] = {seed}
    path: list[tuple[int, int]] = [seed]
    current = seed
    prev_dir = (0, 0)

    while len(visited) < len(cells):
        neighbors = [
            (r, c)
            for dr in (-1, 0, 1)
            for dc in (-1, 0, 1)
            if (dr or dc)
            and (r := current[0] + dr, c := current[1] + dc) in cell_set
            and (r, c) not in visited
        ]
        if neighbors:
            def cost(cell: tuple[int, int]) -> tuple:
                # 邻居越多越好（负号取最小）、方向变化越小越好、最后按位置稳定排序
                local = sum(
                    1
                    for dr in (-1, 0, 1)
                    for dc in (-1, 0, 1)
                    if (cell[0] + dr, cell[1] + dc) in cell_set
                    and (cell[0] + dr, cell[1] + dc) not in visited
                )
                step = (cell[0] - current[0], cell[1] - current[1])
                turn = (step[0] - prev_dir[0]) ** 2 + (step[1] - prev_dir[1]) ** 2
                return (-local, turn, cell[0], cell[1])

            nxt = min(neighbors, key=cost)
        else:
            # 断笔：跳到最近的未访问格
            unvisited = [cell for cell in cells if cell not in visited]
            nxt = min(
                unvisited,
                key=lambda cell: (
                    (cell[0] - current[0]) ** 2 + (cell[1] - current[1]) ** 2,
                    cell[0],
                    cell[1],
                ),
            )

        prev_dir = (nxt[0] - current[0], nxt[1] - current[1])
        path.append(nxt)
        visited.add(nxt)
        current = nxt

    return path


def _nearest_neighbor_order(
    cells: Sequence[tuple[int, int]], seed: tuple[int, int]
) -> list[tuple[int, int]]:
    """从 seed 出发，每步走最近的未访问格，形成连续笔迹。"""
    if not cells:
        return []
    remaining = list(cells)
    ordered: list[tuple[int, int]] = []
    current = seed if seed in remaining else remaining[0]
    while remaining:
        ordered.append(current)
        remaining.remove(current)
        if not remaining:
            break
        current = min(
            remaining,
            key=lambda cell: (cell[0] - ordered[-1][0]) ** 2
            + (cell[1] - ordered[-1][1]) ** 2,
        )
    return ordered


def _text_scan_order(
    cells: Sequence[tuple[int, int]], segment_cols: int = 4
) -> list[tuple[int, int]]:
    """
    文字区域的专用画法：横向按段扫描，模拟写字。
    把格子按列切成若干段（每段 segment_cols 列宽），段间按列从左到右；
    段内用最近邻沿墨迹连续走（而非栅栏式逐行扫），避免“画过一块没画满、
    跳到下一段又从顶部开始”的回头补笔感。
    """
    if not cells:
        return []
    if segment_cols < 1:
        segment_cols = 1
    left_col = min(col for _, col in cells)
    # 按“起始列 // segment_cols”分桶，桶号小（靠左）的先画
    buckets: dict[int, list[tuple[int, int]]] = {}
    for cell in cells:
        bucket_key = (cell[1] - left_col) // segment_cols
        buckets.setdefault(bucket_key, []).append(cell)

    ordered: list[tuple[int, int]] = []
    prev_tail: tuple[int, int] | None = None
    for key in sorted(buckets):
        seg_cells = buckets[key]
        # 段的起点：尽量靠近上一段出口，减少段间跳笔
        if prev_tail is not None:
            seed = min(
                seg_cells,
                key=lambda cell: (cell[0] - prev_tail[0]) ** 2
                + (cell[1] - prev_tail[1]) ** 2,
            )
        else:
            seed = min(seg_cells, key=lambda cell: (cell[0], cell[1]))
        seg_order = _nearest_neighbor_order(seg_cells, seed)
        ordered.extend(seg_order)
        prev_tail = seg_order[-1]
    return ordered


def _order_stream_by_kind(
    kind: str, cells: list[tuple[int, int]]
) -> list[tuple[int, int]]:
    """按区域类型选画法：文字横向按段扫，主体/轮廓走密度游走。"""
    if kind == "text":
        return _text_scan_order(cells)
    return _gradient_walk(cells)


def _chain_region_paths(
    groups: list[tuple[str, list[tuple[int, int]]]],
) -> list[tuple[int, int]]:
    """Finish every component in one visual region before leaving it."""
    paths = [_order_stream_by_kind(kind, cells) for kind, cells in groups]
    remaining = [path for path in paths if path]
    ordered: list[tuple[int, int]] = []
    tail: tuple[int, int] | None = None
    while remaining:
        if tail is None:
            pick_index = 0  # groups retain subject/text/contour priority.
        else:
            pick_index = min(
                range(len(remaining)),
                key=lambda index: min(
                    (remaining[index][0][0] - tail[0]) ** 2
                    + (remaining[index][0][1] - tail[1]) ** 2,
                    (remaining[index][-1][0] - tail[0]) ** 2
                    + (remaining[index][-1][1] - tail[1]) ** 2,
                ),
            )
        path = remaining.pop(pick_index)
        if tail is not None and len(path) > 1:
            head_distance = (path[0][0] - tail[0]) ** 2 + (path[0][1] - tail[1]) ** 2
            end_distance = (path[-1][0] - tail[0]) ** 2 + (path[-1][1] - tail[1]) ** 2
            if end_distance < head_distance:
                path.reverse()
        ordered.extend(path)
        tail = path[-1]
    return ordered


def cluster_ink_streams(active: np.ndarray) -> list[list[tuple[int, int]]]:
    """
    把墨迹格按语义聚成若干条墨流：主体(subject) → 文字(text) → 局部轮廓(contour)，
    每条内部按类型选画法（文字按段扫、其余密度游走）；
    墨流之间按“出口到入口最近邻”动态串联，必要时整条反向，减少跳笔。
    返回的是已串联排序好的多条笔迹流。
    """
    if not active.any():
        return []
    groups = classify_stroke_groups(active)
    # A stream is now a complete visual region, not merely one connected
    # component.  Thus a label's border, its characters, and its arrow cannot
    # be interrupted by a different object that happens to be closer.
    regions = _group_adjacent_stroke_groups(groups)
    streams = [_chain_region_paths(region) for region in regions]
    streams = [s for s in streams if s]
    if not streams:
        return []

    # 串联：主体（第一支）开局，之后每次挑入口离当前出口最近的墨流，
    # 并视情况把该墨流整体反向，使其起点更靠近上一支的出口。
    ordered: list[list[tuple[int, int]]] = []
    remaining = list(streams)
    tail: tuple[int, int] | None = None
    while remaining:
        if tail is None:
            pick_idx = 0  # classify 已把主体排在最前
        else:
            def dist_to_tail(stream: list[tuple[int, int]]) -> int:
                head = stream[0]
                return (head[0] - tail[0]) ** 2 + (head[1] - tail[1]) ** 2
            pick_idx = min(range(len(remaining)), key=lambda i: dist_to_tail(remaining[i]))
        pick = remaining.pop(pick_idx)
        # 视情况反向：若尾离 pick 的终点比离起点更近，则反向
        if tail is not None and len(pick) > 1:
            head = pick[0]
            end = pick[-1]
            d_end = (end[0] - tail[0]) ** 2 + (end[1] - tail[1]) ** 2
            d_head = (head[0] - tail[0]) ** 2 + (head[1] - tail[1]) ** 2
            if d_end < d_head:
                pick = pick[::-1]
        ordered.append(pick)
        tail = pick[-1]
    return ordered


def flatten_streams(streams: list[list[tuple[int, int]]]) -> list[tuple[int, int]]:
    return [cell for stream in streams for cell in stream]


# ──────────────────────────────────────────────────────────────
# 笔尖 / 手部覆盖
# ──────────────────────────────────────────────────────────────
def _load_hand(path: Path, target_h: int) -> tuple[np.ndarray, np.ndarray] | None:
    """
    读入手部素材并按目标高度等比缩放。
    优先用 alpha 通道做蒙版；无 alpha 时回退到“近白即背景”检测。
    返回 (手部BGR, 归一化蒙版[0..1])，失败返回 None。
    """
    if not path.exists():
        return None
    raw = _imread_any(path, cv2.IMREAD_UNCHANGED)
    if raw is None:
        return None

    if raw.ndim == 3 and raw.shape[2] == 4:
        hand = raw[:, :, :3]
        mask = raw[:, :, 3]
    else:
        hand = raw
        gray = cv2.cvtColor(hand, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY_INV)

    # 裁到有效区
    (x0, y0), (x1, y1) = _bounding_box(mask)
    if x1 <= x0 or y1 <= y0:
        return None
    hand = hand[y0:y1 + 1, x0:x1 + 1]
    mask = mask[y0:y1 + 1, x0:x1 + 1]

    scale = target_h / hand.shape[0]
    new_w = max(1, int(round(hand.shape[1] * scale)))
    interp = cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR
    hand = cv2.resize(hand, (new_w, target_h), interpolation=interp)
    mask = cv2.resize(mask, (new_w, target_h), interpolation=interp)
    mask = mask.astype(np.float32) / 255.0

    # 蒙版外区域置黑，便于后续按蒙版混合
    hand[mask <= 0] = 0
    return hand, mask


def _procedural_tip(target_h: int) -> tuple[np.ndarray, np.ndarray]:
    """
    兜底笔尖：程序化画一支记号笔（笔杆渐变 + 圆头柔边 + 落影）。
    不依赖任何外部图片，素材缺失时也能出图。
    """
    w = max(1, int(target_h * 0.34))
    h = target_h
    rgba = np.zeros((h, w, 4), dtype=np.uint8)

    # 落影：一条偏移的暗带，柔化后垫底
    shadow = np.zeros((h, w), dtype=np.uint8)
    cv2.rectangle(shadow, (3, int(h * 0.06)), (w - 2, int(h * 0.62)), 90, thickness=-1)
    shadow = cv2.GaussianBlur(shadow, (15, 15), 0)
    rgba[:, :, 3] = shadow

    # 笔杆：从亮到暗的竖向渐变
    for y in range(h):
        t = y / max(1, h - 1)
        shade = int(220 - 130 * t)
        rgba[y, :, 0:3] = (shade, shade, shade + 10)
    cv2.rectangle(rgba, (4, int(h * 0.04)), (w - 4, int(h * 0.58)), (0, 0, 0), thickness=1)

    # 圆头笔尖（暖色，模拟油墨）
    tip_cy = int(h * 0.70)
    cv2.circle(rgba, (w // 2, tip_cy), max(3, w // 4), (70, 90, 230), thickness=-1)

    # 用圆头 + 笔杆外轮廓合成 alpha 蒙版
    body_mask = np.zeros((h, w), dtype=np.uint8)
    cv2.rectangle(body_mask, (3, int(h * 0.04)), (w - 3, tip_cy), 255, thickness=-1)
    cv2.circle(body_mask, (w // 2, tip_cy), max(3, w // 4), 255, thickness=-1)
    body_mask = cv2.GaussianBlur(body_mask, (7, 7), 0)

    hand = rgba[:, :, :3]
    mask = np.maximum(rgba[:, :, 3], body_mask).astype(np.float32) / 255.0
    hand[mask <= 0] = 0
    return hand, mask


class TipOverlay:
    """把笔尖/手部贴到画布上，让指定的“笔尖锚点”对齐落墨点，带 alpha 混合。"""

    def __init__(
        self,
        hand: np.ndarray,
        mask: np.ndarray,
        tip_anchor_x: float = 0.0,
        tip_anchor_y: float = 0.0,
    ) -> None:
        self.hand = hand
        self.mask = mask
        self.h, self.w = hand.shape[:2]
        self.mask_inv = 1.0 - mask
        # 笔尖在素材中的像素坐标（落墨点要与之对齐）
        # Map normalized anchors exactly onto the source image's pixel range.
        self.tip_px = int(round((self.w - 1) * np.clip(tip_anchor_x, 0.0, 1.0)))
        self.tip_py = int(round((self.h - 1) * np.clip(tip_anchor_y, 0.0, 1.0)))

    def stamp(self, canvas: np.ndarray, x: int, y: int) -> np.ndarray:
        """让素材的笔尖锚点对齐到画布坐标 (x, y)（即落墨点）。"""
        # 素材左上角 = 落墨点 - 笔尖偏移
        anchor_x = x - self.tip_px
        anchor_y = y - self.tip_py
        h_canvas, w_canvas = canvas.shape[:2]

        x0 = max(0, anchor_x)
        y0 = max(0, anchor_y)
        x1 = min(w_canvas, anchor_x + self.w)
        y1 = min(h_canvas, anchor_y + self.h)
        if x1 <= x0 or y1 <= y0:
            return canvas

        sx0 = x0 - anchor_x
        sy0 = y0 - anchor_y
        sx1 = sx0 + (x1 - x0)
        sy1 = sy0 + (y1 - y0)

        region = canvas[y0:y1, x0:x1]
        hand_region = self.hand[sy0:sy1, sx0:sx1]
        mask_region = self.mask[sy0:sy1, sx0:sx1]
        inv_region = self.mask_inv[sy0:sy1, sx0:sx1]

        for c in range(3):
            region[:, :, c] = (
                region[:, :, c] * inv_region + hand_region[:, :, c] * mask_region
            )
        canvas[y0:y1, x0:x1] = region
        return canvas


# ──────────────────────────────────────────────────────────────
# 墨刷
# ──────────────────────────────────────────────────────────────
def _feathered_disk(radius: int) -> np.ndarray:
    """生成半径 r、边缘高斯羽化的圆形蒙版，值域 0..1。"""
    y, x = np.ogrid[-radius:radius + 1, -radius:radius + 1]
    dist = np.sqrt(x * x + y * y).astype(np.float32)
    return np.clip(1.0 - (dist - radius * 0.75) / (radius * 0.25), 0.0, 1.0)


# ──────────────────────────────────────────────────────────────
# contour-wipe 上色工具
# ──────────────────────────────────────────────────────────────
def _ease_in_out_sine(t: float | np.ndarray) -> float | np.ndarray:
    """正弦缓动：起止慢、中间快。输入标量或数组，输出同形。"""
    return -(np.cos(np.pi * t) - 1.0) / 2.0


def _build_wipe_wave(width: int) -> np.ndarray:
    """
    预计算双频正弦波边界，让揭示前沿不是平直线而是水波起伏。
    返回 (W,) float32 数组，值域大致 [-1.35, 1.35]。
    """
    wave_px1 = max(24.0, width / 20.0)
    wave_px2 = max(8.0, width / 72.0)
    xs = np.arange(width, dtype=np.float32)
    return np.sin(xs / wave_px1) + 0.35 * np.sin(xs / wave_px2 + 1.7)


# ──────────────────────────────────────────────────────────────
# 骨架级笔画追踪（移植自 whiteboard-video-engine preprocess.py）
# Zhang-Suen 细化 → 8邻接最直边追踪 → 像素级有序笔画
# ──────────────────────────────────────────────────────────────
_SKEL_NEIGHBORS_8 = [
    (-1, -1), (0, -1), (1, -1),
    (-1, 0),           (1, 0),
    (-1, 1),  (0, 1),  (1, 1),
]


def _zhang_suen_skeleton(mask: np.ndarray, max_iterations: int = 160) -> np.ndarray:
    """
    Zhang-Suen 两子迭代细化，把二值前景掩码细化到 1px 宽骨架。
    输入：bool/uint8 二维数组（True/1 = 前景笔迹）。
    输出：bool 骨架图，同形。
    """
    img = np.pad(mask.astype(np.uint8), 1, mode="constant")
    for _ in range(max_iterations):
        changed = False
        for step in (0, 1):
            p2, p3, p4 = img[:-2, 1:-1], img[:-2, 2:], img[1:-1, 2:]
            p5, p6, p7 = img[2:, 2:], img[2:, 1:-1], img[2:, :-2]
            p8, p9 = img[1:-1, :-2], img[:-2, :-2]
            center = img[1:-1, 1:-1]
            neighbors = [p2, p3, p4, p5, p6, p7, p8, p9]
            # 0→1 转换数（顺时针环绕）
            transitions = sum(
                (neighbors[i] == 0) & (neighbors[(i + 1) % 8] == 1) for i in range(8)
            )
            count = sum(neighbors)
            if step == 0:
                marker = (
                    (center == 1) & (count >= 2) & (count <= 6)
                    & (transitions == 1)
                    & ((p2 * p4 * p6) == 0) & ((p4 * p6 * p8) == 0)
                )
            else:
                marker = (
                    (center == 1) & (count >= 2) & (count <= 6)
                    & (transitions == 1)
                    & ((p2 * p4 * p8) == 0) & ((p2 * p6 * p8) == 0)
                )
            if np.any(marker):
                center[marker] = 0
                changed = True
        if not changed:
            break
    return img[1:-1, 1:-1].astype(bool)


def _skel_neighbors(skel: np.ndarray, point: tuple[int, int]) -> list[tuple[int, int]]:
    """
    返回骨架点 point 的有效 8 邻接邻居。
    关键：当对角邻居与当前点之间已有正交桥时，跳过该对角邻居，
    避免 T 型/十字交叉处的三角形碎笔画，同时保留真正的纯对角中心线。
    """
    x, y = point
    h, w = skel.shape
    result: list[tuple[int, int]] = []
    for dx, dy in _SKEL_NEIGHBORS_8:
        nx, ny = x + dx, y + dy
        if not (0 <= nx < w and 0 <= ny < h and skel[ny, nx]):
            continue
        if dx != 0 and dy != 0 and (skel[y, nx] or skel[ny, x]):
            continue  # 正交桥已连接，跳过冗余对角
        result.append((nx, ny))
    return result


def _edge_key(a: tuple[int, int], b: tuple[int, int]) -> tuple[tuple[int, int], tuple[int, int]]:
    """无向边规范化：(A,B) 和 (B,A) 映射到同一个 key。"""
    return (a, b) if a <= b else (b, a)


def _choose_next(
    prev: tuple[int, int],
    cur: tuple[int, int],
    candidates: list[tuple[int, int]],
    visited_edges: set,
) -> tuple[int, int] | None:
    """
    在交叉点选择"最直的未访问边"继续走。
    用当前行进方向与候选方向的余弦相似度衡量"直度"，取最大值。
    """
    fresh = [p for p in candidates if _edge_key(cur, p) not in visited_edges and p != prev]
    if not fresh:
        return None
    vx, vy = cur[0] - prev[0], cur[1] - prev[1]
    vlen = math.hypot(vx, vy)
    return max(
        fresh,
        key=lambda p: (
            (vx * (p[0] - cur[0]) + vy * (p[1] - cur[1]))
            / (vlen * math.hypot(p[0] - cur[0], p[1] - cur[1]) or 1.0)
        ),
    )


def trace_8connected(skel: np.ndarray, min_points: int = 8) -> list[list[tuple[int, int]]]:
    """
    把 1px 骨架追踪成有序笔画序列。

    - 起点优先级：度=1 的端点 → 度>2 的交叉点 → 其他
    - 交叉点处沿最直的未访问边继续走（而非每分支断成短笔画）
    - 用无向边集合标记访问（像素可复用，边不可重复走）
    - 死胡同（无 fresh 边）即停，剩余分支由后续起点补上
    - 长度 < min_points 的碎片丢弃

    返回 list[list[(x,y)]]，每条是沿笔画方向的有序像素坐标。
    """
    ys, xs = np.nonzero(skel)
    points = [(int(x), int(y)) for x, y in zip(xs, ys)]
    if not points:
        return []
    degrees = {p: len(_skel_neighbors(skel, p)) for p in points}
    starts = (
        [p for p in points if degrees[p] == 1]
        + [p for p in points if degrees[p] > 2]
        + points
    )
    visited_edges: set = set()
    strokes: list[list[tuple[int, int]]] = []
    for start in starts:
        for nb in _skel_neighbors(skel, start):
            edge = _edge_key(start, nb)
            if edge in visited_edges:
                continue
            path = [start]
            prev, cur = start, nb
            visited_edges.add(edge)
            while True:
                path.append(cur)
                next_pt = _choose_next(prev, cur, _skel_neighbors(skel, cur), visited_edges)
                if next_pt is None:
                    break
                visited_edges.add(_edge_key(cur, next_pt))
                prev, cur = cur, next_pt
            if len(path) >= min_points:
                strokes.append(path)
    return strokes


# ── 骨架笔画后处理（重采样 + 平滑 + 排序）──
def _stroke_cumulative_length(points: list[tuple[float, float]]) -> list[float]:
    """每个点的累计弧长 [0, d01, d012, ...]。"""
    cum = [0.0]
    for a, b in zip(points, points[1:]):
        cum.append(cum[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    return cum


def _resample_stroke_points(
    points: list[tuple[float, float]], spacing: float
) -> list[tuple[float, float]]:
    """沿弧长按 spacing 等距重采样，去像素锯齿。"""
    if len(points) < 2:
        return list(points)
    cum = _stroke_cumulative_length(points)
    total = cum[-1]
    if total < spacing:
        return [points[0], points[-1]]
    n = max(2, int(round(total / spacing)))
    result: list[tuple[float, float]] = []
    for i in range(n + 1):
        target = total * i / n
        # 二分定位
        lo, hi = 0, len(cum) - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if cum[mid] < target:
                lo = mid + 1
            else:
                hi = mid
        if lo == 0:
            result.append(points[0])
            continue
        seg_start = cum[lo - 1]
        seg_len = cum[lo] - seg_start
        t = (target - seg_start) / seg_len if seg_len > 0 else 0.0
        ax, ay = points[lo - 1]
        bx, by = points[lo]
        result.append((ax + (bx - ax) * t, ay + (by - ay) * t))
    return result


def _chaikin_smooth(
    points: list[tuple[float, float]], iterations: int = 1
) -> list[tuple[float, float]]:
    """Chaikin 切角平滑：每段用 0.25/0.75 两点替换，起止点保留。"""
    pts = list(points)
    for _ in range(iterations):
        if len(pts) < 3:
            break
        smoothed = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            smoothed.append((a[0] * 0.75 + b[0] * 0.25, a[1] * 0.75 + b[1] * 0.25))
            smoothed.append((a[0] * 0.25 + b[0] * 0.75, a[1] * 0.25 + b[1] * 0.75))
        smoothed.append(pts[-1])
        pts = smoothed
    return pts


def _order_skeleton_strokes(strokes: list[list[tuple[float, float]]]) -> list[list[tuple[float, float]]]:
    """
    笔画排序：从上到下、从左到右，长笔优先。
    简化版①order_strokes——用包围盒左上角 + 负长度做字典序。
    """
    def sort_key(s):
        if not s:
            return (0, 0, 0, 0)
        xs = [p[0] for p in s]
        ys = [p[1] for p in s]
        length = _stroke_cumulative_length(s)[-1]
        return (min(ys) // 12, min(xs), min(ys), -length)
    return sorted(strokes, key=sort_key)


# ──────────────────────────────────────────────────────────────
# 时长 / 段落切分
# ──────────────────────────────────────────────────────────────
@dataclass
class PhasePlan:
    ink_frames: int
    color_frames: int
    gaze_frames: int
    ratio_label: str


def plan_phases(total_ms: int, cfg: Config) -> PhasePlan:
    """
    把总时长切成 起笔/添彩/凝视 三段。
    凝视段先用基准秒数占位，剩余时长按权重分给起笔与添彩；
    若剩余无法被权重和整除，余数补给凝视段，避免精度丢失。
    """
    weight_sum = cfg.ink_weight + cfg.color_weight
    gaze_ms = int(cfg.gaze_seconds * 1000)
    anim_ms = total_ms - gaze_ms
    remainder = anim_ms % weight_sum
    if remainder:
        anim_ms -= remainder
        gaze_ms += remainder

    ink_frames = round(anim_ms * cfg.ink_weight / weight_sum * cfg.fps / 1000)
    color_frames = round(anim_ms * cfg.color_weight / weight_sum * cfg.fps / 1000)
    gaze_frames = round(gaze_ms * cfg.fps / 1000)
    if ink_frames <= 0 and color_frames <= 0:
        ink_frames = color_frames = 0
    return PhasePlan(ink_frames, color_frames, gaze_frames, f"{cfg.ink_weight}:{cfg.color_weight}")


# ──────────────────────────────────────────────────────────────
# 渲染器主体
# ──────────────────────────────────────────────────────────────
class StreamBoardRenderer:
    """持有单次渲染的全部状态，方法挂在实例上。"""

    def __init__(
        self,
        image_bgr: np.ndarray,
        cfg: Config,
        hand_png: Path | None,
        bare_tip: bool,
    ) -> None:
        self.cfg = cfg
        self.canvas_bgr = _hex_to_bgr(cfg.canvas_hex)

        # 计算输出尺寸：长边限到 cap，并对齐到 grid_edge 的偶数倍（编码要求偶数）
        h0, w0 = image_bgr.shape[:2]
        scale = cfg.cap_long_edge / max(h0, w0)
        w = int(round(w0 * scale))
        h = int(round(h0 * scale))
        align = cfg.grid_edge if cfg.grid_edge % 2 == 0 else cfg.grid_edge * 2
        w = (w // align) * align
        h = (h // align) * align
        self.out_w = max(align, w)
        self.out_h = max(align, h)

        self.color_img = cv2.resize(image_bgr, (self.out_w, self.out_h), interpolation=cv2.INTER_AREA)
        gray = cv2.cvtColor(self.color_img, cv2.COLOR_BGR2GRAY)
        self.thresh_map = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 10
        )
        self.active = _active_mask(self.thresh_map, cfg.grid_edge, cfg.ink_threshold)
        self.grid_blocks = _to_grid_blocks(self.thresh_map, cfg.grid_edge)
        self.ink_pixels = self.thresh_map < cfg.ink_threshold
        self.ink_paint = np.repeat(self.thresh_map[:, :, None], 3, axis=2).astype(np.float32)

        # 把原图背景染成画布底色（仅影响 color_img，不碰 ink_pixels / ink_paint）。
        # 这样上色/凝视阶段的背景与起笔(线稿)阶段一致，避免背景色突兀跳变。
        # 放在 ink_pixels 算完之后，线稿质量完全不受影响。
        if cfg.match_bg:
            self._match_original_background()

        # 格空间聚类（grid 模式的笔迹路径 + contour-wipe 阻力场仍需要）
        self.ink_streams = cluster_ink_streams(self.active)

        # 笔迹路径：按 ink_path_mode 选择 grid（格中心插值）或 skeleton（骨架追踪）
        if cfg.ink_path_mode == "skeleton":
            self.skeleton_strokes = self._build_skeleton_path()
            if self.skeleton_strokes:
                self.stroke_path = [pt for stroke in self.skeleton_strokes for pt in stroke]
            else:
                # 骨架追踪无笔画：真正退回格中心路径，而非留一条空 path
                self.stroke_path = flatten_streams(self.ink_streams)
        else:
            self.skeleton_strokes = []
            self.stroke_path = flatten_streams(self.ink_streams)

        # 画布（用浮点缓存，便于墨刷累加混合）
        self.drawn = np.zeros((self.out_h, self.out_w, 3), dtype=np.float32)
        self.drawn[...] = self.canvas_bgr.astype(np.float32)

        # 笔尖覆盖
        self.tip: TipOverlay | None = None
        if not bare_tip:
            hand_data = _load_hand(hand_png, cfg.target_hand_height) if hand_png else None
            tip_anchor_x = cfg.tip_anchor_x
            tip_anchor_y = cfg.tip_anchor_y
            if hand_data is None:
                hand_data = _procedural_tip(cfg.target_hand_height)
                tip_anchor_x = 0.5
                tip_anchor_y = 0.70
            self.tip = TipOverlay(
                hand_data[0], hand_data[1],
                tip_anchor_x=tip_anchor_x,
                tip_anchor_y=tip_anchor_y,
            )

    # ── 把原图背景染成画布底色（仅影响 color_img，不碰线稿墨迹）──
    def _match_original_background(self) -> None:
        """
        采样原图四角作为背景色基准，把与其差异 < 阈值的像素替换为 canvas_hex。
        使上色/凝视阶段的背景与起笔(线稿)阶段一致，避免背景色突兀跳变。
        彩色内容（与背景差异大）保留原色不受影响。
        """
        img = self.color_img
        h, w = img.shape[:2]
        margin = max(3, min(h, w) // 50)
        samples = [
            img[:margin, :margin], img[:margin, -margin:],
            img[-margin:, :margin], img[-margin:, -margin:],
        ]
        bg_color = np.median(np.concatenate([s.reshape(-1, 3) for s in samples]), axis=0)
        diff = np.abs(img.astype(np.int16) - bg_color.astype(np.int16)).sum(axis=2)
        bg_mask = diff < self.cfg.match_bg_threshold
        img[bg_mask] = self.canvas_bgr

    # ── 笔迹中心点（像素坐标）──
    def _cell_center(self, cell: tuple[int, int]) -> tuple[int, int]:
        r, c = cell
        e = self.cfg.grid_edge
        return (c * e + e // 2, r * e + e // 2)  # (x, y)

    # ── 骨架级笔迹路径（Zhang-Suen 细化 + 8邻接最直边追踪）──
    def _build_skeleton_path(self) -> list[list[tuple[int, int]]]:
        """
        用骨架追踪生成像素级有序笔画序列，替代网格格中心插值。
        笔尖走真实骨架，比网格中心更贴合原图线条；
        交叉点处沿最直边继续走，避免三角碎笔画。
        """
        cfg = self.cfg
        skel = _zhang_suen_skeleton(self.ink_pixels, max_iterations=160)
        raw_strokes = trace_8connected(skel, min_points=cfg.skeleton_min_points)
        if not raw_strokes:
            print("  [warn] 骨架追踪无笔画，回退到格中心路径")
            return []

        spacing = cfg.skeleton_resample_spacing
        processed: list[list[tuple[int, int]]] = []
        for stroke in raw_strokes:
            pts = [(float(x), float(y)) for x, y in stroke]
            pts = _resample_stroke_points(pts, spacing)
            pts = _chaikin_smooth(pts, iterations=1)
            pts = _resample_stroke_points(pts, spacing)
            if len(pts) >= 2 and _stroke_cumulative_length(pts)[-1] > 2.0:
                processed.append([(int(round(x)), int(round(y))) for x, y in pts])

        processed = _order_skeleton_strokes(processed)
        total_pts = sum(len(s) for s in processed)
        print(f"  骨架追踪: {len(processed)} 条笔画, {total_pts} 个采样点")
        return processed

    # ── contour-wipe 阻力场（懒构建，整个上色阶段复用）──
    def _build_resistance_field(self) -> np.ndarray:
        """
        用线稿墨迹构建"阻力场"：轮廓处阻力≈1，向下方逐行按 decay 指数衰减。
        揭示前沿遇高阻力被扣减像素数，从而"先卡在轮廓上、再缓慢越过"。

        阻力场全程静态，与上色进度无关，故只算一次缓存到 self._resistance。
        """
        if getattr(self, "_resistance", None) is not None:
            return self._resistance

        h, w = self.out_h, self.out_w
        cfg = self.cfg

        # 1) 墨线二值图（uint8 0/255）
        ink_u8 = (self.ink_pixels.astype(np.uint8)) * 255

        # 2) 膨胀：圆形结构元让轮廓变粗、形成阻挡带
        spread = int(np.clip(min(w, h) // 64, 3, 17))
        if spread % 2 == 0:  # 结构元半径需为正奇数
            spread = max(3, spread - 1)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (spread, spread))
        dilated = cv2.dilate(ink_u8, kernel, iterations=1)

        # 3) 高斯模糊：把硬边变成渐变带（半径需为正奇数）
        blur_r = max(1, int(round(min(w, h) / 220.0)))
        if blur_r % 2 == 0:
            blur_r += 1
        resistance = cv2.GaussianBlur(dilated, (blur_r, blur_r), 0).astype(np.float32)

        # 4) 归一化到 [0,1]
        peak = float(resistance.max())
        if peak > 1e-6:
            resistance /= peak
        else:
            # 无墨线（全白图）：阻力场恒 0，contour-wipe 退化为平直扫描
            resistance = np.zeros((h, w), dtype=np.float32)

        # 5) 逐行向下因果传播 decay：让每条轮廓向下方投出指数衰减阴影
        decay = cfg.wipe_decay
        for row in range(1, h):
            resistance[row] = np.maximum(resistance[row], resistance[row - 1] * decay)

        self._resistance = resistance
        return resistance

    # ── 在落点铺一“墨点”：线稿阶段铺阈值图，添彩阶段铺原色 ──
    def _reveal_ink_segment(
        self, start: tuple[int, int], end: tuple[int, int]
    ) -> None:
        """Reveal only the original line-art pixels touched by one pen movement."""
        segment = np.zeros((self.out_h, self.out_w), dtype=np.uint8)
        thickness = max(1, self.cfg.ink_reveal_radius * 2 + 1)
        cv2.line(segment, start, end, 255, thickness=thickness, lineType=cv2.LINE_AA)
        revealed = (segment > 0) & self.ink_pixels
        self.drawn[revealed] = self.ink_paint[revealed]

    def _ink_stamp(self, cell: tuple[int, int]) -> None:
        r, c = cell
        e = self.cfg.grid_edge
        block = self.grid_blocks[r, c]
        ink_region = block < self.cfg.ink_threshold
        # 阈值图是单通道，复制到三通道画布
        paint = np.repeat(block[:, :, None], 3, axis=2)
        target = self.drawn[r * e:r * e + e, c * e:c * e + e]
        target[ink_region] = paint[ink_region]

    def _color_stamp(self, px: int, py: int, disk: np.ndarray) -> None:
        radius = self.cfg.brush_radius
        h, w = self.out_h, self.out_w
        y0, y1 = max(0, py - radius), min(h, py + radius + 1)
        x0, x1 = max(0, px - radius), min(w, px + radius + 1)
        if y1 <= y0 or x1 <= x0:
            return
        by0, by1 = y0 - (py - radius), disk.shape[0] - ((py + radius + 1) - y1)
        bx0, bx1 = x0 - (px - radius), disk.shape[1] - ((px + radius + 1) - x1)
        m = disk[by0:by1, bx0:bx1]
        inv = 1.0 - m
        target = self.drawn[y0:y1, x0:x1]
        source = self.color_img[y0:y1, x0:x1].astype(np.float32)
        for ch in range(3):
            target[:, :, ch] = target[:, :, ch] * inv + source[:, :, ch] * m

    # ── 把当前画布快照（含笔尖）写若干帧 ──
    def _snapshot_with_tip(self, px: int, py: int) -> np.ndarray:
        snap = self.drawn.astype(np.uint8)  # astype 已返回新数组，无需再 copy
        if self.tip is not None:
            self.tip.stamp(snap, px, py)
        return snap

    def _build_stroke_samples(
        self, path: list[tuple[int, int]]
    ) -> tuple[list[tuple[int, int]], set[int], list[int]]:
        """
        把笔迹折线插值成连续的笔尖像素坐标序列。
        相邻格中心之间按 sample_step 像素均匀采样，形成连贯的滑动轨迹。

        返回 (samples, pen_lifts, sample_cell_index)：
          samples         —— 笔尖像素坐标列表
          pen_lifts       —— “抬笔”采样点索引集合（非相邻格切换处）
          sample_cell_index —— 每个采样点归属的 cell 在 path 中的索引，
                              用于让“揭墨进度”与“笔尖位置”严格同步。
        """
        samples: list[tuple[int, int]] = []
        pen_lifts: set[int] = set()
        sample_cell_index: list[int] = []
        for idx, cell in enumerate(path):
            cx, cy = self._cell_center(cell)
            if idx == 0:
                samples.append((cx, cy))
                sample_cell_index.append(idx)
                continue
            prev_cell = path[idx - 1]
            prev = self._cell_center(prev_cell)
            cell_distance = math.hypot(cell[0] - prev_cell[0], cell[1] - prev_cell[1])
            if cell_distance > math.sqrt(2):
                pen_lifts.add(len(samples))
                samples.append((cx, cy))
                sample_cell_index.append(idx)
                continue
            steps = max(
                1, int(math.hypot(cx - prev[0], cy - prev[1]) / self.cfg.sample_step)
            )
            for s in range(1, steps + 1):
                samples.append(
                    (int(prev[0] + (cx - prev[0]) * s / steps),
                     int(prev[1] + (cy - prev[1]) * s / steps))
                )
                sample_cell_index.append(idx)
        return samples, pen_lifts, sample_cell_index

    def _frame_progress_indices(self, n_steps: int, target_frames: int) -> list[int]:
        """
        给定 n_steps 个笔尖位置和 target_frames 个目标帧，
        返回每个目标帧应取的笔尖位置索引（均匀映射，覆盖完整轨迹）。
        target_frames <= n_steps 时是下采样，> 时是重复采样。
        target_frames <= 0（如总时长≤凝视段导致本段无帧）时返回空，不产生任何帧。
        """
        if n_steps == 0 or target_frames <= 0:
            return []
        if target_frames == 1:
            return [n_steps - 1]
        return [
            round(f * (n_steps - 1) / (target_frames - 1))
            for f in range(target_frames)
        ]

    def _pause_frame_indices(
        self, target_frames: int, n_cells: int
    ) -> set[int]:
        """
        自适应停顿：按内容密度分档决定停顿比例，再把停顿帧均匀分布在时间轴上。
        返回"需要冻结（重复上一帧进度）"的帧索引集合。

        分档指标用"每格帧数" frames_per_cell = target_frames / n_cells：
        帧比格多得多（值大）说明动画时长相对内容有富余 → 多停顿模拟换笔呼吸；
        帧比格少（值小）说明内容密集、时长紧张 → 不停顿。

        pause_mode 可强制覆盖："off" 关闭、"light"/"heavy" 固定档、"auto" 自动。
        """
        mode = self.cfg.pause_mode
        if mode == "off" or target_frames < 8 or n_cells <= 0:
            return set()

        if mode == "light":
            ratio = self.cfg.pause_ratio_light
        elif mode == "heavy":
            ratio = self.cfg.pause_ratio_heavy
        else:  # auto：按"每格帧数"自动分档
            fpc = target_frames / n_cells
            if fpc >= self.cfg.pause_heavy_fpc:
                ratio = self.cfg.pause_ratio_heavy
            elif fpc >= self.cfg.pause_light_fpc:
                ratio = self.cfg.pause_ratio_light
            else:
                return set()  # 内容密集：快节奏，不停顿

        # 停顿帧数量，至少为 0；夹到 target_frames-2 避免首尾帧停顿
        pause_count = min(
            max(0, int(round(target_frames * ratio))),
            max(0, target_frames - 2),
        )
        if pause_count <= 0:
            return set()

        # 等分插入：把 target_frames 分成 pause_count+1 等份，停顿落在内部分点上
        # 不用首尾(1/(n+1) 的分子从 1 起)，保证开头结尾不打断
        return {
            max(1, min(target_frames - 2,
                       round((idx + 1) * target_frames / (pause_count + 1))))
            for idx in range(pause_count)
        }

    # ── 起笔段：沿 stroke_path 铺线稿，笔尖滑动且与揭墨严格同步 ──
    def lay_down_ink(self, writer: cv2.VideoWriter, target_frames: int) -> None:
        """起笔段入口：按 ink_path_mode 分发到骨架追踪或网格格路径。"""
        if self.cfg.ink_path_mode == "skeleton" and self.skeleton_strokes:
            return self._lay_down_ink_skeleton(writer, target_frames)
        return self._lay_down_ink_grid(writer, target_frames)

    # ── grid 模式：沿网格格中心插值路径揭墨（原逻辑）──
    def _lay_down_ink_grid(self, writer: cv2.VideoWriter, target_frames: int) -> None:
        path = self.stroke_path
        n = len(path)
        if n == 0:
            print("  无墨迹，跳过起笔段")
            for _ in range(target_frames):
                writer.write(self._snapshot_with_tip(self.out_w // 2, self.out_h // 2))
            return

        samples, pen_lifts, sample_cell_index = self._build_stroke_samples(path)
        sample_idx_for_frame = self._frame_progress_indices(len(samples), target_frames)

        # 自适应停顿：按密度分档选出"冻结帧"（笔尖不动、揭墨不推进），
        # 模拟真人书写时的换笔/呼吸节奏。
        pause_frames = self._pause_frame_indices(target_frames, n)
        if pause_frames:
            print(f"  自适应停顿: {len(pause_frames)} 帧冻结 (模式={self.cfg.pause_mode})")

        written = 0
        cells_revealed = 0  # 已整块揭示的格数（增量，严格跟随笔尖进度）
        last_sample_idx: int | None = None
        for fi, si in enumerate(sample_idx_for_frame):
            # 停顿帧：复用上一帧的笔尖位置与进度，不揭墨，只写一帧快照（笔尖冻结）
            if fi in pause_frames and last_sample_idx is not None:
                sx, sy = samples[last_sample_idx]
                writer.write(self._snapshot_with_tip(sx, sy))
                written += 1
                if (fi + 1) % max(1, target_frames // 10) == 0:
                    print(f"  起笔进度: {int((fi + 1) / target_frames * 100)}%")
                continue

            # 笔尖沿线揭示（保留笔迹流动感）
            if last_sample_idx is None:
                self._reveal_ink_segment(samples[si], samples[si])
            else:
                for sample_idx in range(last_sample_idx + 1, si + 1):
                    if sample_idx in pen_lifts:
                        continue
                    self._reveal_ink_segment(
                        samples[sample_idx - 1], samples[sample_idx]
                    )

            # 整块揭示：严格揭到"当前笔尖所在 cell"，保证笔尖与画同步、文字完整。
            # sample_cell_index[si] 是当前帧笔尖归属的格索引，揭到它为止。
            target_cell = sample_cell_index[si]
            while cells_revealed <= target_cell and cells_revealed < n:
                self._ink_stamp(path[cells_revealed])
                cells_revealed += 1

            sx, sy = samples[si]
            writer.write(self._snapshot_with_tip(sx, sy))
            written += 1
            last_sample_idx = si
            if (fi + 1) % max(1, target_frames // 10) == 0:
                print(f"  起笔进度: {int((fi + 1) / target_frames * 100)}%")

        # 收尾兜底：确保所有格墨迹揭示完整，并补齐帧数
        while cells_revealed < n:
            self._ink_stamp(path[cells_revealed])
            cells_revealed += 1
        last = samples[-1]
        while written < target_frames:
            writer.write(self._snapshot_with_tip(*last))
            written += 1
        print(f"  起笔完成: {n} 格, {written} 帧")

    # ── skeleton 模式：沿骨架像素路径揭墨（笔尖走真实骨架）──
    def _lay_down_ink_skeleton(self, writer: cv2.VideoWriter, target_frames: int) -> None:
        """
        骨架模式起笔：笔尖沿骨架像素点滑动，用 _reveal_ink_segment 揭原图墨迹。
        不做整块揭示（_ink_stamp），因为骨架已精确到像素，无需保证格完整。
        跨笔画处标记抬笔（pen_lifts），跳过插值。
        """
        strokes = self.skeleton_strokes
        if not strokes:
            return self._lay_down_ink_grid(writer, target_frames)

        # 把多条笔画展平成连续采样点序列，跨笔画处标记抬笔
        samples: list[tuple[int, int]] = []
        pen_lifts: set[int] = set()
        for si, stroke in enumerate(strokes):
            if si > 0:
                pen_lifts.add(len(samples))  # 笔画间抬笔
            samples.extend(stroke)

        n = len(samples)
        if n == 0:
            print("  无骨架笔画，跳过起笔段")
            for _ in range(target_frames):
                writer.write(self._snapshot_with_tip(self.out_w // 2, self.out_h // 2))
            return

        sample_idx_for_frame = self._frame_progress_indices(n, target_frames)

        # 自适应停顿（用笔画数而非格数做密度判定）
        pause_frames = self._pause_frame_indices(target_frames, len(strokes))
        if pause_frames:
            print(f"  自适应停顿: {len(pause_frames)} 帧冻结 (模式={self.cfg.pause_mode})")

        written = 0
        last_sample_idx: int | None = None
        report_step = max(1, target_frames // 10)
        for fi, si in enumerate(sample_idx_for_frame):
            # 停顿帧：笔尖冻结
            if fi in pause_frames and last_sample_idx is not None:
                sx, sy = samples[last_sample_idx]
                writer.write(self._snapshot_with_tip(sx, sy))
                written += 1
                if (fi + 1) % report_step == 0:
                    print(f"  起笔进度: {int((fi + 1) / target_frames * 100)}%")
                continue

            # 沿骨架揭墨：从上一帧采样点到当前帧采样点，逐段揭示原图墨迹
            if last_sample_idx is None:
                self._reveal_ink_segment(samples[si], samples[si])
            else:
                for idx in range(last_sample_idx + 1, si + 1):
                    if idx in pen_lifts:
                        continue
                    self._reveal_ink_segment(samples[idx - 1], samples[idx])

            sx, sy = samples[si]
            writer.write(self._snapshot_with_tip(sx, sy))
            written += 1
            last_sample_idx = si
            if (fi + 1) % report_step == 0:
                print(f"  起笔进度: {int((fi + 1) / target_frames * 100)}%")

        # 收尾兜底：补齐帧数
        last = samples[-1]
        while written < target_frames:
            writer.write(self._snapshot_with_tip(*last))
            written += 1
        print(f"  起笔完成(骨架): {n} 采样点, {written} 帧")

    # ── 添彩段入口：按 color_fill 分发到对应风格 ──
    def wash_color(self, writer: cv2.VideoWriter, target_frames: int) -> None:
        if self.cfg.color_fill == "contour-wipe":
            return self.wash_color_contour(writer, target_frames)
        return self.wash_color_brush(writer, target_frames)

    # ── brush：沿笔画轨迹，用圆形墨刷铺原色（默认风格）──
    def wash_color_brush(self, writer: cv2.VideoWriter, target_frames: int) -> None:
        path = self.stroke_path
        n = len(path)
        disk = _feathered_disk(self.cfg.brush_radius)
        if n == 0:
            print("  无墨迹，跳过添彩段")
            gaze = self.color_img
            for _ in range(target_frames):
                writer.write(gaze)
            return

        centers = [self._cell_center(cell) for cell in path]
        cell_idx_for_frame = self._frame_progress_indices(n, target_frames)

        written = 0
        last_cell_idx: int | None = None
        for fi, ci in enumerate(cell_idx_for_frame):
            # 按当前帧进度上色：从上一帧的格补刷到当前格，
            # 把下采样可能跳过的中间格一并刷上，保证原色连续。
            if last_cell_idx is None:
                self._color_stamp(*centers[ci], disk)
            else:
                for cell_idx in range(last_cell_idx + 1, ci + 1):
                    self._color_stamp(*centers[cell_idx], disk)

            cx, cy = centers[ci]
            writer.write(self._snapshot_with_tip(cx, cy))
            written += 1
            last_cell_idx = ci
            if (fi + 1) % max(1, target_frames // 10) == 0:
                print(f"  添彩进度: {int((fi + 1) / target_frames * 100)}%")

        # 收尾兜底
        last = centers[-1]
        while written < target_frames:
            writer.write(self._snapshot_with_tip(*last))
            written += 1
        print(f"  添彩完成: {n} 格, {written} 帧")

    # ── contour-wipe：轮廓感知自上而下扫描上色 ──
    def wash_color_contour(self, writer: cv2.VideoWriter, target_frames: int) -> None:
        """
        颜色不沿笔画轨迹刷，而是全局自上而下扫一道揭示前沿。
        前沿遇轮廓先卡住（阻力≈1 扣减 delay_px），再随其下方衰减阴影缓慢越过，
        形成"颜色沿着线蔓延"的观感。笔尖做横向来回扫动，模拟手在涂色。
        """
        cfg = self.cfg
        h, w = self.out_h, self.out_w

        if target_frames <= 0:
            print("  无添彩帧，跳过 contour-wipe 段")
            return

        # 一次性预计算：阻力场、水波边界、扣减像素数、行坐标网格
        resistance = self._build_resistance_field()
        wave = _build_wipe_wave(w)
        delay_px = int(np.clip(h * cfg.wipe_delay_ratio, 12, 52))
        blocks = max(1, cfg.wipe_blocks)
        ys = np.arange(h, dtype=np.float32)[:, None]   # (H,1)，逐帧复用

        # 把 self.drawn 复位为"线稿已绘完"的状态（brush 在 lay_down_ink 后接续，此处同样接续）
        # color_img 是揭示目标
        color_src = self.color_img.astype(np.float32)

        print(f"  contour-wipe: {w}x{h}, delay_px={delay_px}, 趟数={blocks}")

        written = 0
        # 揭示前沿从 -delay_px 扫到 h+delay_px，全程覆盖
        sweep = h + 2 * delay_px
        report_step = max(1, target_frames // 10)

        for fi in range(target_frames):
            # 全局进度（带正弦缓动）：0 → 1
            if target_frames == 1:
                progress = 1.0
            else:
                progress = fi / (target_frames - 1)
            lead = _ease_in_out_sine(progress) * sweep - delay_px

            # 揭示掩码：y <= lead + wave[x] - resistance[y,x]*delay_px
            threshold = lead + wave[None, :] - resistance * delay_px  # (H,W)
            reveal = ys <= threshold                        # (H,W) bool

            # 揭示原色到 drawn 缓存
            self.drawn[reveal] = color_src[reveal]

            # 笔尖横向扫动：blocks 趟来回，奇数趟反向
            lane = (fi / blocks * 2.0) % 1.0               # 单趟归一化进度 0..1
            lane = _ease_in_out_sine(lane)
            forward = (int(fi // blocks) % 2 == 0)         # 偶数趟正向、奇数趟反向
            cursor_x = int(lane * w) if forward else int((1.0 - lane) * w)
            cursor_x = max(0, min(w - 1, cursor_x))

            # 光标 y = 当前列已揭示像素的最底部行
            col_revealed = np.where(reveal[:, cursor_x])[0]
            cursor_y = int(col_revealed[-1]) if col_revealed.size > 0 else 0

            writer.write(self._snapshot_with_tip(cursor_x, cursor_y))
            written += 1
            if (fi + 1) % report_step == 0:
                print(f"  添彩进度(contour-wipe): {int((fi + 1) / target_frames * 100)}%")

        # 收尾兜底：确保整图已揭示（最后一帧进度=1 时 lead≈h+delay_px，理论上全覆盖）
        full_reveal = np.ones((h, w), dtype=bool)
        self.drawn[full_reveal] = color_src[full_reveal]
        last = self._snapshot_with_tip(w // 2, h - 1)
        while written < target_frames:
            writer.write(last)
            written += 1
        print(f"  contour-wipe 完成: {written} 帧")

    def render_to(self, raw_path: Path, total_ms: int) -> Path:
        cfg = self.cfg
        plan = plan_phases(total_ms, cfg)
        ink_cells = len(self.stroke_path)

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(raw_path), fourcc, cfg.fps, (self.out_w, self.out_h))

        print(f"  墨流: {len(self.ink_streams)} 条, 墨迹格: {ink_cells}")
        print(
            f"  时长: {total_ms}ms -> 起笔 {plan.ink_frames}f / "
            f"添彩 {plan.color_frames}f / 凝视 {plan.gaze_frames}f (权重 {plan.ratio_label})"
        )

        started = time.time()
        self.lay_down_ink(writer, plan.ink_frames)
        self.wash_color(writer, plan.color_frames)
        # 凝视：完整原图
        gaze_img = self.color_img
        for _ in range(plan.gaze_frames):
            writer.write(gaze_img)
        writer.release()
        print(f"  渲染耗时: {time.time() - started:.1f}s")
        return raw_path


# ──────────────────────────────────────────────────────────────
# 转码（系统 ffmpeg 优先，PyAV 备选，两者都没有则保留 mp4v）
# ──────────────────────────────────────────────────────────────
def transcode_h264(src: Path, dst: Path) -> Path:
    """
    把 mp4v 原始视频转码为 H.264（yuv420p），提升播放器兼容性。

    优先级：
      1. 系统 ffmpeg 子进程（编码效率最高、体积最小，CRF=20）
      2. PyAV（纯 pip 安装，无需系统 ffmpeg；编码效率稍逊，用 CRF=28 控制体积）
      3. 两者都没有：保留原始 mp4v 编码并告警
    """
    # 路径1：系统 ffmpeg（推荐，体积最优）
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is not None:
        cmd = [
            ffmpeg, "-y", "-loglevel", "error",
            "-i", str(src),
            "-c:v", "libx264",
            "-crf", "20",
            "-pix_fmt", "yuv420p",
            str(dst),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            src.unlink(missing_ok=True)
            print(f"  H.264 转码完成(ffmpeg): {dst}")
            return dst
        print(f"  [warn] ffmpeg 转码失败: {res.stderr.strip()}")

    # 路径2：PyAV（备选，纯 pip 安装）
    try:
        return _transcode_with_pyav(src, dst)
    except ImportError:
        pass
    except Exception as e:
        print(f"  [warn] PyAV 转码失败: {e}")

    # 路径3：都没有，保留 mp4v
    print(f"  [warn] 未找到 ffmpeg 和 PyAV，保留原始 mp4v 编码: {src}")
    print(f"         安装任一即可获得 H.264: pip install av  或  安装系统 ffmpeg")
    return src


def _transcode_with_pyav(src: Path, dst: Path) -> Path:
    """
    用 PyAV 在 Python 内做 H.264 转码。PyAV 未装时抛 ImportError。
    PyAV 自带的 libx264 编码效率低于系统 ffmpeg（同 CRF 下体积大数倍），
    故用 CRF=28 平衡体积与画质。
    """
    import av
    input_container = av.open(str(src), mode="r")
    in_stream = input_container.streams.video[0]
    width = in_stream.codec_context.width
    height = in_stream.codec_context.height
    fps = in_stream.average_rate

    output_container = av.open(str(dst), mode="w")
    out_stream = output_container.add_stream("h264", rate=fps)
    out_stream.width = width
    out_stream.height = height
    out_stream.pix_fmt = "yuv420p"
    out_stream.options = {"crf": "28", "preset": "medium"}

    for frame in input_container.decode(video=0):
        packet = out_stream.encode(frame)
        if packet:
            output_container.mux(packet)
    # flush
    packet = out_stream.encode(None)
    if packet:
        output_container.mux(packet)

    output_container.close()
    input_container.close()
    src.unlink(missing_ok=True)
    print(f"  H.264 转码完成(PyAV): {dst}")
    return dst


# ──────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────
def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="把一张图片渲染成流式笔迹白板动画视频"
    )
    p.add_argument("image", help="输入图片路径 (PNG/JPG/JPEG/BMP/TIFF)")
    p.add_argument("--out-dir", default="./out", help="输出目录 (默认: ./out)")
    p.add_argument("--total-ms", type=int, default=10000, help="视频总时长，单位毫秒 (默认: 10000)")
    p.add_argument("--bare-tip", action="store_true", help="不叠加笔尖/手部覆盖")
    p.add_argument(
        "--pen-image", default=str(DEFAULT_HAND_PNG),
        help="自定义笔尖/手部素材路径 (默认: skill 内置 drawing-hand.png)",
    )
    p.add_argument("--fps", type=int, default=None, help="覆盖默认帧率")
    p.add_argument("--grid-edge", type=int, default=None, help="覆盖默认网格边长")
    p.add_argument("--brush-radius", type=int, default=None, help="覆盖默认墨刷半径")
    p.add_argument(
        "--color-fill", default="contour-wipe", choices=["brush", "contour-wipe"],
        help="添彩阶段上色风格: contour-wipe 轮廓感知自上而下扫描 (默认); brush 沿笔画轨迹刷",
    )
    p.add_argument(
        "--wipe-decay", type=float, default=None,
        help="contour-wipe: 阻力场逐行向下衰减系数 (默认 0.86，越小越快越过轮廓)",
    )
    p.add_argument(
        "--wipe-delay-ratio", type=float, default=None,
        help="contour-wipe: 轮廓处前沿扣减比例×h (默认 0.04，越大轮廓处停留越久)",
    )
    p.add_argument(
        "--wipe-blocks", type=int, default=None,
        help="contour-wipe: 笔尖横向来回扫动趟数 (默认 18)",
    )
    p.add_argument(
        "--pause", default="heavy", choices=["auto", "off", "light", "heavy"],
        help="起笔段停顿节奏: heavy 明显(默认); auto 按密度自动分档; off 关闭; light 少量",
    )
    p.add_argument(
        "--ink-path", default="grid", choices=["grid", "skeleton"],
        help="起笔段笔迹路径: grid 网格格中心插值(默认); skeleton 骨架级像素追踪(更精准贴合线条)",
    )
    return p.parse_args(argv)


def _build_cfg(args: argparse.Namespace) -> Config:
    kw: dict = {}
    if args.fps is not None:
        kw["fps"] = args.fps
    if args.grid_edge is not None:
        kw["grid_edge"] = args.grid_edge
    if args.brush_radius is not None:
        kw["brush_radius"] = args.brush_radius
    if args.color_fill is not None:
        kw["color_fill"] = args.color_fill
    if args.wipe_decay is not None:
        kw["wipe_decay"] = args.wipe_decay
    if args.wipe_delay_ratio is not None:
        kw["wipe_delay_ratio"] = args.wipe_delay_ratio
    if args.wipe_blocks is not None:
        kw["wipe_blocks"] = args.wipe_blocks
    if args.pause is not None:
        kw["pause_mode"] = args.pause
    if args.ink_path is not None:
        kw["ink_path_mode"] = args.ink_path
    return Config(**kw)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    cfg = _build_cfg(args)

    print("=" * 56)
    print("流式笔迹动画渲染器")
    print("=" * 56)

    image_bgr = _imread_any(args.image)
    if image_bgr is None:
        print(f"[err] 无法读取图片: {args.image}")
        return 1

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_path = out_dir / f"stream_{ts}.mp4"
    h264_path = out_dir / f"stream_{ts}_h264.mp4"

    pen_png = Path(args.pen_image) if args.pen_image else None
    renderer = StreamBoardRenderer(image_bgr, cfg, pen_png, args.bare_tip)
    print(f"  输入: {args.image}")
    print(f"  输出尺寸: {renderer.out_w}x{renderer.out_h}, 帧率: {cfg.fps}")

    renderer.render_to(raw_path, args.total_ms)
    final = transcode_h264(raw_path, h264_path)

    size_mb = final.stat().st_size / (1024 * 1024)
    print(f"\n最终视频: {final}")
    print(f"  文件大小: {size_mb:.2f} MB")
    print("=" * 56)
    print("完成")
    # 末行输出最终路径，便于上层捕获
    print(f"OUTPUT={final}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
