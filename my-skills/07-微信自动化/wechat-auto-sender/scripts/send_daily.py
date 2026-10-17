# -*- coding: utf-8 -*-
"""
微信每日定时发送「早安/晚安」图片 —— 自动发送程序

原理：用 Windows 界面自动化模拟人工操作已登录的微信客户端窗口
      （不注入、不破解协议、不读内存），因此运行期间微信窗口会被临时前置。

用法：
  python send_daily.py                      # 正常发送（定时任务调用）
  python send_daily.py --dry-run            # 演练：只粘贴不点发送
  python send_daily.py --test               # 试发到「文件传输助手」
  python send_daily.py --date 9-18          # 指定日期
  python send_daily.py --force              # 忽略「当天已发过」限制
  python send_daily.py --calibrate "对象备注名"   # 校准：打开聊天并保存标题参考图
"""
from __future__ import annotations

import argparse
import ctypes
import datetime as dt
import io
import json
import os
import sys
import time
import traceback
from ctypes import wintypes

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
user32.SetProcessDPIAware()

# 明确函数签名，避免 64 位句柄被截断成 32 位
user32.FindWindowW.restype = wintypes.HWND
user32.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
user32.GetForegroundWindow.restype = wintypes.HWND
user32.OpenInputDesktop.restype = wintypes.HANDLE
user32.OpenInputDesktop.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
user32.CloseDesktop.argtypes = [wintypes.HANDLE]
user32.CloseDesktop.restype = wintypes.BOOL

WECHAT_WINDOW_CLASS = "Qt51514QWindowIcon"
# 微信自己弹出的窗口标题：识别主窗口时排除，出现时用 WM_CLOSE 关掉
WECHAT_POPUP_TITLES = ("搜索聊天记录",)

def _resolve_base():
    """确定「数据目录」（config.json / refs / logs 所在处），兼容两种部署方式：

      A) 平铺：send_daily.py 与 config.json 同目录        -> 用脚本所在目录
      B) 分层：脚本在 scripts/ 下、配置在技能根目录        -> 用上一级目录

    这样无论怎么摆，都能找到同一份 config.json。
    """
    here = os.path.dirname(os.path.abspath(__file__))
    if os.path.exists(os.path.join(here, "config.json")):
        return here
    parent = os.path.dirname(here)
    if parent and os.path.exists(os.path.join(parent, "config.json")):
        return parent
    return here


BASE = _resolve_base()
LOG_DIR = os.path.join(BASE, "logs")
SHOT_DIR = os.path.join(LOG_DIR, "shots")
REF_DIR = os.path.join(BASE, "refs")
STATE_FILE = os.path.join(LOG_DIR, "state.json")


# ────────────────────────────── 日志 ──────────────────────────────
class Log:
    def __init__(self, tag=""):
        os.makedirs(LOG_DIR, exist_ok=True)
        os.makedirs(SHOT_DIR, exist_ok=True)
        stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.path = os.path.join(LOG_DIR, f"run_{stamp}{tag}.log")
        self.fh = open(self.path, "w", encoding="utf-8")

    def __call__(self, msg=""):
        line = f"[{dt.datetime.now().strftime('%H:%M:%S')}] {msg}"
        try:
            print(line)
        except Exception:
            pass          # 无控制台时打印可能失败，不影响写日志
        try:
            self.fh.write(line + "\n")
            self.fh.flush()
        except Exception:
            pass

    def close(self):
        try:
            self.fh.close()
        except Exception:
            pass


# ────────────────────────── Windows 基础操作 ──────────────────────────
# 全局目标进程：鼠标/键盘操作前必须确认前台窗口属于微信进程，
# 否则立即中止 —— 绝不让模拟点击落到你正在用的其它程序上。
# （判断进程而不是窗口，是为了兼容微信自己的弹窗，如"搜索聊天记录"）
_TARGET_HWND = None
_TARGET_PID = None


def set_target(hwnd):
    global _TARGET_HWND, _TARGET_PID
    _TARGET_HWND = hwnd
    pid = wintypes.DWORD(0)
    user32.GetWindowThreadProcessId(wintypes.HWND(hwnd), ctypes.byref(pid))
    _TARGET_PID = pid.value


def _win_desc(h):
    try:
        cls = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(ctypes.c_void_p(h), cls, 256)
        t = ctypes.create_unicode_buffer(512)
        user32.GetWindowTextW(ctypes.c_void_p(h), t, 512)
        return f"{cls.value}/{t.value!r}"
    except Exception:
        return "?"


def _ensure_main_foreground():
    """确认前台确实是「微信主窗口」，否则先把主窗口重新提上来；再不行就报错中止。

    - 前台是别的程序           -> 立即中止（绝不让模拟点击外溢到你的其它应用）
    - 前台是微信的小窗口       -> 放行（输入法状态条、小弹窗，不影响对主窗口的操作）
    - 前台是微信的另一个大窗口 -> 这正是 10-6 凌晨失灵的形态：窗口看着正常，
                                  但点击全打在错的窗口上，搜索框永远吃不到字。
                                  这里先把主窗口重新置前，仍不行就中止，绝不盲点。
    """
    if _TARGET_PID is None or not _TARGET_HWND:
        return
    for _ in range(3):
        fg = user32.GetForegroundWindow()
        if fg == _TARGET_HWND:
            return
        if not fg:
            raise RuntimeError("当前没有前台窗口，立即停止操作")
        pid = wintypes.DWORD(0)
        user32.GetWindowThreadProcessId(wintypes.HWND(fg), ctypes.byref(pid))
        if pid.value != _TARGET_PID:
            raise RuntimeError(
                f"前台已被其它程序抢走（{_win_desc(fg)}），立即停止操作，避免误点")
        r = wintypes.RECT()
        user32.GetWindowRect(wintypes.HWND(fg), ctypes.byref(r))
        w, ht = r.right - r.left, r.bottom - r.top
        if w < 500 or ht < 400:
            return                                  # 微信自己的小窗口，放行
        # 微信的另一个大窗口挡在前面，把主窗口重新提上来再判一次
        user32.BringWindowToTop(wintypes.HWND(_TARGET_HWND))
        user32.SetForegroundWindow(wintypes.HWND(_TARGET_HWND))
        time.sleep(0.5)
    raise RuntimeError(
        f"__WECHAT_OTHER_WINDOW__ 前台被微信的另一个大窗口占着"
        f"（{_win_desc(user32.GetForegroundWindow())}），已中止避免点错")


VK = {
    "ctrl": 0x11, "alt": 0x12, "shift": 0x10, "win": 0x5B,
    "enter": 0x0D, "esc": 0x1B, "tab": 0x09, "space": 0x20,
    "backspace": 0x08, "delete": 0x2E,
    "f": 0x46, "v": 0x56, "c": 0x43, "a": 0x41, "w": 0x57,
    "up": 0x26, "down": 0x28, "left": 0x25, "right": 0x27,
}
for _i in range(10):
    VK[str(_i)] = 0x30 + _i
for _c in "abcdefghijklmnopqrstuvwxyz":
    VK[_c] = ord(_c.upper())


def scan_wechat_windows():
    """扫描微信所有顶层 Qt 窗口，返回 [(面积, hwnd, 标题, 是否可见, 宽, 高), ...]。"""
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    out = []

    def cb(h, _):
        try:
            cls = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(ctypes.c_void_p(h), cls, 256)
            if cls.value != WECHAT_WINDOW_CLASS:
                return True
            t = ctypes.create_unicode_buffer(512)
            user32.GetWindowTextW(ctypes.c_void_p(h), t, 512)
            r = wintypes.RECT()
            user32.GetWindowRect(ctypes.c_void_p(h), ctypes.byref(r))
            w, ht = r.right - r.left, r.bottom - r.top
            vis = bool(user32.IsWindowVisible(ctypes.c_void_p(h)))
            out.append((w * ht, h, t.value, vis, w, ht))
        except Exception:
            pass
        return True

    user32.EnumWindows(WNDENUMPROC(cb), 0)
    return out


def find_hwnd():
    """定位微信主窗口。

    微信 4.x 的标题会随当前聊天变化（例如显示为「<当前打开的聊天名>」），不能按标题找。
    这里在微信特有的窗口类里挑「面积足够大」的那个（弹窗面积小，自动排除）；
    **不要求窗口可见** —— 因为主窗口常被隐藏到托盘，需要把它找出来再唤醒。
    """
    wins = [w for w in scan_wechat_windows()
            if w[4] >= 500 and w[5] >= 400 and w[2] not in WECHAT_POPUP_TITLES]
    if not wins:
        return 0
    visible = [w for w in wins if w[3]]
    pool = visible if visible else wins      # 有可见的优先用可见的
    pool.sort(key=lambda x: x[0], reverse=True)
    return pool[0][1]


def wechat_is_running():
    """微信进程是否在运行（哪怕只挂着一个登录窗口也算）。"""
    return len(scan_wechat_windows()) > 0


def login_window_present():
    """是否存在微信登录/扫码窗口（尺寸较小的 "微信" 窗口）。"""
    for _area, _h, title, vis, w, ht in scan_wechat_windows():
        if vis and (w < 500 or ht < 400) and title.strip() in ("微信", "WeChat"):
            return True
    return False


def get_rect(hwnd):
    r = wintypes.RECT()
    user32.GetWindowRect(wintypes.HWND(hwnd), ctypes.byref(r))
    return r.left, r.top, r.right, r.bottom


def activate(hwnd, retries=8, log=None):
    """可靠地把微信窗口切到前台并取得焦点。
    窗口被隐藏到托盘（不可见）时，先把它显示出来；最小化时还原。"""
    for _ in range(retries):
        if not user32.IsWindowVisible(wintypes.HWND(hwnd)):
            user32.ShowWindow(wintypes.HWND(hwnd), 5)      # SW_SHOW：把托盘里的窗口显示出来
            time.sleep(0.7)
        if user32.IsIconic(wintypes.HWND(hwnd)):
            user32.ShowWindow(wintypes.HWND(hwnd), 9)      # SW_RESTORE：把最小化还原
            time.sleep(0.4)
        if user32.GetForegroundWindow() == hwnd:
            return True
        fg = user32.GetForegroundWindow()
        fg_thread = user32.GetWindowThreadProcessId(wintypes.HWND(fg), None)
        tgt_thread = user32.GetWindowThreadProcessId(wintypes.HWND(hwnd), None)
        cur = kernel32.GetCurrentThreadId()
        attached = []
        for t in (fg_thread, tgt_thread, cur):
            if t and user32.AttachThreadInput(wintypes.DWORD(t), wintypes.DWORD(cur), True):
                attached.append(t)
        try:
            user32.BringWindowToTop(wintypes.HWND(hwnd))
            user32.SetForegroundWindow(wintypes.HWND(hwnd))
            user32.SetActiveWindow(wintypes.HWND(hwnd))
        finally:
            for t in attached:
                user32.AttachThreadInput(wintypes.DWORD(t), wintypes.DWORD(cur), False)
        time.sleep(0.4)
        if user32.GetForegroundWindow() == hwnd:
            return True
    # 不用模拟 ALT 键那类旁门左道解锁前台：宁可失败让上层安全中止，
    # 也不要往你正在使用的其它程序里丢按键。
    return user32.GetForegroundWindow() == hwnd


def move_window(hwnd, x, y, w, h):
    SWP_NOZORDER, SWP_SHOWWINDOW = 0x0004, 0x0040
    user32.SetWindowPos(wintypes.HWND(hwnd), 0, int(x), int(y), int(w), int(h),
                        SWP_NOZORDER | SWP_SHOWWINDOW)
    time.sleep(0.5)


def grab(hwnd):
    """截取微信窗口。截图前临时置顶，避免被其它窗口挡住截到别的东西。"""
    from PIL import ImageGrab
    HWND_TOPMOST, HWND_NOTOPMOST = -1, -2
    SWP_NOMOVE, SWP_NOSIZE, SWP_SHOWWINDOW = 0x0002, 0x0001, 0x0040
    flags = SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW
    user32.SetWindowPos(wintypes.HWND(hwnd), HWND_TOPMOST, 0, 0, 0, 0, flags)
    time.sleep(0.4)
    try:
        l, t, r, b = get_rect(hwnd)
        img = ImageGrab.grab(bbox=(l, t, r, b), all_screens=True)
    finally:
        user32.SetWindowPos(wintypes.HWND(hwnd), HWND_NOTOPMOST, 0, 0, 0, 0, flags)
    return img


def session_locked():
    """判断当前 Windows 会话是否已锁屏（锁屏时桌面不可交互，必须放弃）。"""
    DESKTOP_SWITCHDESKTOP = 0x0100
    h = user32.OpenInputDesktop(0, False, DESKTOP_SWITCHDESKTOP)
    if h:
        user32.CloseDesktop(h)
        return False
    return True


def require_foreground(hwnd, log, tries=6):
    """必须让微信处于前台，否则后面的点击/按键会落到别的程序上，宁可中止。"""
    for _ in range(tries):
        if activate(hwnd, log=log) and user32.GetForegroundWindow() == hwnd:
            return True
        time.sleep(0.6)
    return user32.GetForegroundWindow() == hwnd


def close_wechat_popups(log=None):
    """用 WM_CLOSE 关掉微信自己的弹窗（不依赖焦点，最稳，也不会影响别的程序）。"""
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    closed = []

    def cb(h, _):
        try:
            cls = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(ctypes.c_void_p(h), cls, 256)
            if cls.value != WECHAT_WINDOW_CLASS:
                return True
            if not user32.IsWindowVisible(ctypes.c_void_p(h)):
                return True
            t = ctypes.create_unicode_buffer(512)
            user32.GetWindowTextW(ctypes.c_void_p(h), t, 512)
            if t.value in WECHAT_POPUP_TITLES:
                user32.PostMessageW(ctypes.c_void_p(h), 0x0010, 0, 0)   # WM_CLOSE
                closed.append(t.value)
        except Exception:
            pass
        return True

    user32.EnumWindows(WNDENUMPROC(cb), 0)
    if closed:
        if log:
            log(f"  已关闭微信弹窗：{closed}")
        time.sleep(1.0)
    return closed


def dismiss_popups(hwnd, log):
    """关掉微信弹窗并回到微信主窗口。"""
    close_wechat_popups(log)
    return require_foreground(hwnd, log)


def click(hwnd, x, y):
    _ensure_main_foreground()
    l, t, _, _ = get_rect(hwnd)
    user32.SetCursorPos(l + int(x), t + int(y))
    time.sleep(0.15)
    _ensure_main_foreground()
    user32.mouse_event(0x0002, 0, 0, 0, 0)
    time.sleep(0.07)
    user32.mouse_event(0x0004, 0, 0, 0, 0)
    time.sleep(0.3)


def key(combo):
    _ensure_main_foreground()
    parts = [p.strip().lower() for p in combo.replace("+", " ").split()]
    mods, main = [], None
    for p in parts:
        if p in ("ctrl", "alt", "shift", "win"):
            mods.append(VK[p])
        else:
            main = VK.get(p)
    if main is None:
        raise ValueError(f"未知按键: {combo}")
    for m in mods:
        user32.keybd_event(m, 0, 0, 0)
    time.sleep(0.06)
    user32.keybd_event(main, 0, 0, 0)
    time.sleep(0.06)
    user32.keybd_event(main, 0, 2, 0)
    for m in reversed(mods):
        user32.keybd_event(m, 0, 2, 0)
    time.sleep(0.25)


def set_clip_text(text):
    import win32clipboard
    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_UNICODETEXT, text)
    finally:
        win32clipboard.CloseClipboard()
    time.sleep(0.25)


def set_clip_image(path):
    """把图片以 CF_DIB 形式放进剪贴板 —— 粘贴到微信即为图片消息。"""
    import win32clipboard
    from PIL import Image
    img = Image.open(path).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, "BMP")
    dib = buf.getvalue()[14:]  # 去掉 BMP 文件头，保留 DIB
    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, dib)
    finally:
        win32clipboard.CloseClipboard()
    time.sleep(0.3)


# ────────────────────────────── 配置 ──────────────────────────────
def load_config():
    with open(os.path.join(BASE, "config.json"), encoding="utf-8") as f:
        return json.load(f)


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"sent": {}}


def save_state(st):
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=2)


# ─────────────────────────── 业务步骤 ───────────────────────────
def ensure_wechat(cfg, log):
    """确保微信主窗口可用。主窗口被隐藏到托盘时会直接唤醒，不再重复启动新实例。"""
    hwnd = find_hwnd()
    if hwnd:
        vis = bool(user32.IsWindowVisible(wintypes.HWND(hwnd)))
        log(f"微信主窗口已找到 hwnd={hwnd}（可见={vis}，不可见会自动唤醒）")
        return hwnd

    exe = cfg.get("微信程序")
    if not exe or not os.path.exists(exe):
        raise RuntimeError(f"微信程序不存在: {exe}")

    wait_s = int(cfg.get("启动等待秒数", 180))
    if wechat_is_running():
        # 已在运行却没有主窗口，多半是停在登录/扫码界面。
        # 千万不要再启动一个新实例，否则会留下重复进程（9-25 那次就是这么来的）。
        log(f"微信在运行但没有主窗口（可能停在登录界面），等待最多 {wait_s} 秒")
    else:
        log(f"微信未运行，正在启动 {exe}")
        os.startfile(exe)

    t0 = time.time()
    while time.time() - t0 < wait_s:
        time.sleep(2)
        hwnd = find_hwnd()
        if hwnd:
            time.sleep(2)
            log(f"微信主窗口已就绪 hwnd={hwnd}（等待了 {int(time.time() - t0)} 秒）")
            return hwnd

    if login_window_present():
        raise RuntimeError(f"微信停留在登录界面，需要人工用手机扫码登录（已等待 {wait_s} 秒）")
    raise RuntimeError(f"等待 {wait_s} 秒仍未出现微信主窗口，本次放弃")


def search_text_present(img, cfg):
    """判断搜索框里是否真的输进去了文字（占位提示是浅灰色，真文字是深色）。"""
    try:
        x1, y1, x2, y2 = cfg["界面坐标"]["搜索框裁剪区"]
        crop = img.crop((x1, y1, x2, y2)).convert("L")
        darkest = crop.getextrema()[0]
        return darkest < 120
    except Exception:
        return True


def save_debug_shots(hwnd, tag, log=None):
    """出问题时保留现场：主窗口截图 + 全屏截图 + 前后台窗口信息。
    10-6 那次失败因为没有截图，事后无法判断当时屏幕上是什么，这个函数就是补这个洞。"""
    try:
        from PIL import ImageGrab
        stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        win_p = os.path.join(SHOT_DIR, f"{stamp}_{tag}_窗口.png")
        full_p = os.path.join(SHOT_DIR, f"{stamp}_{tag}_全屏.png")
        txt_p = os.path.join(SHOT_DIR, f"{stamp}_{tag}_现场.txt")
        grab(hwnd).save(win_p)
        ImageGrab.grab(all_screens=True).save(full_p)
        fg = user32.GetForegroundWindow()
        lines = [
            f"时间      : {dt.datetime.now():%Y-%m-%d %H:%M:%S}",
            f"故障       : {tag}",
            f"前台窗口   : {fg}  {_win_desc(fg)}",
            f"主窗口     : {_TARGET_HWND}  {_win_desc(_TARGET_HWND) if _TARGET_HWND else ''}",
            "微信的所有窗口：",
        ]
        for _a, h, t, v, w, ht in scan_wechat_windows():
            lines.append(f"  hwnd={h:<10} {w}x{ht:<5} 可见={int(v)} 标题={t!r}")
        with open(txt_p, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        if log:
            log(f"  已留下失败现场：{os.path.basename(win_p)} / {os.path.basename(full_p)} / {os.path.basename(txt_p)}")
    except Exception as e:
        if log:
            log(f"  (保存失败现场时出错: {e})")


def open_chat(hwnd, target, cfg, log, method="click", row=None):
    """搜索并打开指定联系人的聊天窗口，返回整窗截图。

    method="click" 直接点搜索结果里该联系人的那一行（row 为行号 y）
    method="key"   下方向键选中第一条结果后回车
    """
    ui = cfg["界面坐标"]
    if not dismiss_popups(hwnd, log):
        log("  !! 微信窗口无法切到前台（可能你正在用电脑），本次放弃该目标")
        save_debug_shots(hwnd, "无法前置窗口", log)
        return None

    sx, sy = ui["搜索框"]
    # 预热点击：窗口刚被前置时，最初几次点击可能被系统吞掉
    click(hwnd, 650, 520)
    time.sleep(0.4)

    got = False
    for attempt in range(1, 5):
        click(hwnd, sx, sy)
        time.sleep(0.4)
        click(hwnd, sx, sy)
        time.sleep(0.6)
        key("ctrl+a")          # 清空搜索框里可能残留的旧关键词
        key("delete")
        time.sleep(0.3)
        set_clip_text(target)
        key("ctrl+v")
        time.sleep(1.2)
        img = grab(hwnd)
        if search_text_present(img, cfg):
            got = True
            log(f"  搜索词已输入（第 {attempt} 次尝试）")
            break
        log(f"  第 {attempt} 次尝试：搜索框没吃进文字，重试")
    if not got:
        log("  !! 搜索框始终无法输入，放弃该目标")
        save_debug_shots(hwnd, "搜索框无输入", log)
        return None

    time.sleep(max(0.0, cfg.get("搜索等待毫秒", 2200) / 1000.0 - 1.2))
    if method == "key":
        key("down")
        time.sleep(0.4)
        key("enter")
    else:
        rx, ry = ui["搜索结果第一条"]
        if row:
            ry = row
        click(hwnd, rx, ry)
    time.sleep(2.0)
    return grab(hwnd)


def crop_title(img, cfg):
    x1, y1, x2, y2 = cfg["界面坐标"]["标题裁剪区"]
    return img.crop((x1, y1, x2, y2))


def title_similarity(a, b):
    """返回 0~1 的相似度（1 表示完全一致）。"""
    from PIL import ImageChops, ImageStat
    if a.size != b.size:
        b = b.resize(a.size)
    diff = ImageChops.difference(a.convert("L"), b.convert("L"))
    mean = ImageStat.Stat(diff).mean[0]
    return max(0.0, 1.0 - mean / 40.0)


def verify_title(img, target, cfg, log):
    """把当前聊天标题与参考图比对，防止发错人。"""
    if not cfg.get("验证标题", True):
        log("已按配置跳过标题校验")
        return True
    ref_rel = target.get("标题参考图")
    if not ref_rel:
        log("!! 该对象未配置标题参考图，为安全起见判定为校验失败")
        return False
    ref_path = ref_rel if os.path.isabs(ref_rel) else os.path.join(BASE, ref_rel)
    if not os.path.exists(ref_path):
        log(f"!! 标题参考图不存在: {ref_path}（先运行 --calibrate 生成）")
        return False
    from PIL import Image
    cur = crop_title(img, cfg)
    ref = Image.open(ref_path)
    sim = title_similarity(cur, ref)
    thr = cfg.get("标题相似度阈值", 0.8)
    log(f"标题校验相似度 = {sim:.3f}（阈值 {thr}）")
    return sim >= thr


def verify_input_empty(img, cfg, log):
    """发送前确认聊天输入框里没有残留草稿，否则会把旧内容一起发出去。"""
    box = cfg["界面坐标"].get("输入框裁剪区")
    ref_rel = cfg.get("输入框空参考图")
    if not box or not ref_rel:
        return True
    ref_path = ref_rel if os.path.isabs(ref_rel) else os.path.join(BASE, ref_rel)
    if not os.path.exists(ref_path):
        log(f"  (提示) 输入框空参考图不存在，跳过输入框校验：{ref_path}")
        return True
    from PIL import Image
    cur = img.crop(tuple(box))
    ref = Image.open(ref_path)
    sim = title_similarity(cur, ref)
    thr = cfg.get("输入框相似度阈值", 0.8)
    log(f"  输入框空闲校验 = {sim:.3f}（阈值 {thr}）")
    return sim >= thr


def send_image(hwnd, path, cfg, log, dry_run=False):
    ui = cfg["界面坐标"]
    if not require_foreground(hwnd, log):
        raise RuntimeError("发送前无法把微信窗口切到前台")
    ix, iy = ui["聊天输入框"]
    click(hwnd, ix, iy)
    time.sleep(0.5)
    # 关键闸门：输入框必须先是空的，否则停止发送（演练模式也会走这道校验）
    if not verify_input_empty(grab(hwnd), cfg, log):
        raise RuntimeError("输入框里检测到残留内容，为避免误发已中止（请手动清空微信输入框后重试）")
    if dry_run:
        log(f"  演练模式：未发送（应发送文件 {os.path.basename(path)}）")
        return False
    # 再尽力清一次（正常状态下是无害的空操作）
    key("ctrl+a")
    key("delete")
    time.sleep(0.3)
    set_clip_image(path)
    key("ctrl+v")
    time.sleep(cfg.get("发送间隔毫秒", 1800) / 1000.0)
    if not require_foreground(hwnd, log):
        raise RuntimeError("按发送键前窗口失去前台")
    key("enter")
    time.sleep(cfg.get("发送间隔毫秒", 1800) / 1000.0)
    log(f"  已发送 -> {os.path.basename(path)}")
    return True


def resolve_images(cfg, date_str, log):
    """返回 [(类别, 完整路径 或 None)]"""
    folder = cfg["图片文件夹"]
    m, d = date_str.split("-")[0], date_str.split("-")[1]
    out = []
    for kind in cfg["发送类别"]:
        name = cfg["文件名格式"].format(m=m, d=d, kind=kind)
        p = os.path.join(folder, name)
        out.append((kind, p if os.path.exists(p) else None))
    return out


def latest_available(cfg, kind):
    folder = cfg["图片文件夹"]
    suffix = kind + ".jpg"
    cands = []
    for n in os.listdir(folder):
        if n.endswith(suffix):
            try:
                mm, dd = n[: -len(suffix)].split("-")
                cands.append((int(mm), int(dd), os.path.join(folder, n)))
            except Exception:
                continue
    if not cands:
        return None
    cands.sort(key=lambda x: (x[0], x[1]))
    return cands[-1][2]


# ───────────────────────────── 主流程 ─────────────────────────────
def run(args):
    tag = ""
    if args.test:
        tag = "_TEST"
    elif args.dry_run:
        tag = "_DRYRUN"
    log = Log(tag)
    cfg = load_config()

    try:
        today = dt.date.today()
        if args.date:
            date_str = args.date
        elif cfg.get("日期口径") == "yesterday":
            y = today - dt.timedelta(days=1)
            date_str = f"{y.month}-{y.day}"
        else:
            date_str = f"{today.month}-{today.day}"

        log(f"==== 微信图片自动发送 ====")
        log(f"日期口径={cfg.get('日期口径')} -> 目标日期 {date_str}")

        if session_locked():
            log("!! 当前 Windows 会话处于锁屏状态，界面无法操作，本次放弃（请保持不锁屏）")
            log("==== 结束（未发送）====")
            return 3

        images = resolve_images(cfg, date_str, log)
        for kind, p in images:
            log(f"  图片 {kind}: {p if p else '【缺失】'}")

        missing = [k for k, p in images if not p]
        if missing:
            if cfg.get("缺图处理") == "latest":
                fixed = []
                for kind, p in images:
                    if p:
                        fixed.append((kind, p))
                    else:
                        lp = latest_available(cfg, kind)
                        log(f"  {kind} 缺失，改用最新一张: {lp}")
                        fixed.append((kind, lp))
                images = fixed
            else:
                log(f"缺失 {missing}，按配置「skip」跳过，本次不发送")
                log("==== 结束（未发送）====")
                return 0

        targets = cfg.get("测试对象", []) if args.test else cfg["发送对象"]
        if args.test and not targets:
            log("!! 未配置「测试对象」，无法试发")
            return 2

        hwnd = ensure_wechat(cfg, log)
        set_target(hwnd)          # 开启「非微信前台就立即中止」的硬防护
        orig = get_rect(hwnd)
        log(f"记录微信窗口原位置 {orig}")
        win = cfg["窗口位置"]
        move_window(hwnd, win["x"], win["y"], win["w"], win["h"])
        time.sleep(0.8)

        state = load_state()
        day_key = date_str
        failed = False
        try:
            for t in targets:
                name = t.get("备注名") or t.get("搜索关键词")
                log(f"--- 目标：{name} ---")

                sent_flag = state["sent"].get(day_key, {}).get(name, [])
                todo = [k for k, p in images if k not in sent_flag]
                if not todo and cfg.get("同一目标同一天只发一次", True) and not args.force:
                    log(f"  当天已发送过 {sent_flag}，跳过")
                    continue

                try:
                    # 微信搜索下拉框的行位置会变，所以逐行尝试，直到标题比对通过；
                    # 每行都不过就再试一次「下方向键+回车」。全程只认标题，不认坐标。
                    rows = list(cfg.get("默认候选行Y") or [131, 165, 199, 233, 267, 301, 335, 369, 403])
                    plan = []
                    if t.get("结果行Y"):
                        plan.append(("click", t["结果行Y"]))
                    plan += [("click", r) for r in rows if r != t.get("结果行Y")]
                    plan.append(("key", None))

                    ok_open = False
                    img, shot = None, None
                    for attempt, (method, row) in enumerate(plan, start=1):
                        try:
                            img = open_chat(hwnd, t["搜索关键词"], cfg, log, method=method, row=row)
                        except RuntimeError as e:
                            msg = str(e)
                            if ("__WECHAT_POPUP__" in msg or "__WECHAT_OTHER_WINDOW__" in msg
                                    or "抢走" in msg or "没有前台窗口" in msg):
                                log(f"  第 {attempt} 次尝试被打断（{msg}），恢复后继续")
                                dismiss_popups(hwnd, log)
                                continue
                            raise
                        if img is None:
                            log(f"  第 {attempt} 次尝试（{method}@{row}）没打开，继续")
                            continue
                        shot = os.path.join(
                            SHOT_DIR, f"{dt.datetime.now():%Y%m%d_%H%M%S}_{name}_try{attempt}.png"
                        )
                        img.save(shot)
                        # 无论正式还是测试，一律校验标题，绝不凭运气发送
                        if verify_title(img, t, cfg, log):
                            ok_open = True
                            log(f"  已打开「{name}」（第 {attempt} 次尝试 {method}@{row}）")
                            break
                        log(f"  第 {attempt} 次尝试（{method}@{row}）标题不符，换下一行")
                    if not ok_open:
                        failed = True
                        log(f"  !! 共 {len(plan)} 次尝试都未能打开「{name}」，已中止，绝不乱发。最近截图：{shot}")
                        save_debug_shots(hwnd, f"打开失败_{name}", log)
                        continue

                    ok_kinds = []
                    for kind, p in images:
                        if kind in sent_flag:
                            log(f"  {kind} 当天已发过，跳过")
                            continue
                        if send_image(hwnd, p, cfg, log, dry_run=args.dry_run) or args.dry_run:
                            ok_kinds.append(kind)

                    if not args.dry_run:
                        lst = state["sent"].setdefault(day_key, {}).setdefault(name, [])
                        for k in ok_kinds:
                            if k not in lst:      # 去重，避免 --force 重跑后记录重复
                                lst.append(k)
                        save_state(state)

                    tail = grab(hwnd)
                    tail.save(os.path.join(SHOT_DIR, f"{dt.datetime.now():%Y%m%d_%H%M%S}_{name}_after.png"))
                except Exception as e:
                    failed = True
                    log(f"  !! 处理 {name} 时出错：{e}")
                    log(traceback.format_exc())
                    save_debug_shots(hwnd, f"异常_{name}", log)
        finally:
            if cfg.get("运行后恢复窗口", True):
                move_window(hwnd, orig[0], orig[1], orig[2] - orig[0], orig[3] - orig[1])
                log(f"微信窗口已恢复原位 {orig}")

        log("==== 结束 ====")
        return 1 if failed else 0

    except Exception as e:
        log(f"!! 运行失败：{e}")
        log(traceback.format_exc())
        return 2
    finally:
        log.close()


def calibrate(args):
    """打开指定联系人，保存标题参考图，供人工确认。"""
    log = Log("_CALIB")
    cfg = load_config()
    try:
        hwnd = ensure_wechat(cfg, log)
        set_target(hwnd)
        orig = get_rect(hwnd)
        win = cfg["窗口位置"]
        move_window(hwnd, win["x"], win["y"], win["w"], win["h"])
        time.sleep(0.8)

        target = None
        for t in list(cfg["发送对象"]) + list(cfg.get("测试对象", [])):
            if args.calibrate in (t.get("备注名"), t.get("搜索关键词")):
                target = t
                break
        if target is None:
            raise RuntimeError(f"config.json 的对象列表里找不到 {args.calibrate}")

        img = open_chat(hwnd, target["搜索关键词"], cfg, log,
                        method=args.calib_method, row=target.get("结果行Y"))
        if img is None:
            raise RuntimeError("搜索框始终无法输入，校准失败")
        os.makedirs(REF_DIR, exist_ok=True)
        full = os.path.join(REF_DIR, f"calib_{target['备注名']}.png")
        img.save(full)
        ref_rel = target.get("标题参考图") or f"refs/{target['备注名']}_title.png"
        ref_path = ref_rel if os.path.isabs(ref_rel) else os.path.join(BASE, ref_rel)
        os.makedirs(os.path.dirname(ref_path), exist_ok=True)
        crop_title(img, cfg).save(ref_path)
        log(f"已打开「{target['备注名']}」的聊天")
        log(f"整窗截图: {full}")
        log(f"标题参考图: {ref_path}")
        log("请人工确认标题与聊天内容是否为正确的对象。")
        move_window(hwnd, orig[0], orig[1], orig[2] - orig[0], orig[3] - orig[1])
        return 0
    except Exception as e:
        log(f"!! 校准失败：{e}")
        log(traceback.format_exc())
        return 2
    finally:
        log.close()


def main():
    # 定时任务运行时常无控制台，先把输出编码固定住，避免中文/特殊字符导致打印报错
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    ap = argparse.ArgumentParser(description="微信每日定时发送早安/晚安图片")
    ap.add_argument("--date", help="指定日期，格式 M-D，例如 9-18")
    ap.add_argument("--test", action="store_true", help="试发到「文件传输助手」")
    ap.add_argument("--dry-run", action="store_true", help="演练：完整走流程但不发送（不会在输入框留下痕迹）")
    ap.add_argument("--force", action="store_true", help="忽略当天已发送记录")
    ap.add_argument("--calibrate", metavar="对象", help="校准标题参考图")
    ap.add_argument("--calib-method", default="click", choices=["click", "key"],
                    help="校准时的打开方式")
    args = ap.parse_args()

    if args.calibrate:
        sys.exit(calibrate(args))
    sys.exit(run(args))


if __name__ == "__main__":
    main()
