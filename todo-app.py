#!/usr/bin/env python3
"""
置顶待办 — Windows 桌面始终置顶的轻量级待办清单
Python + tkinter 实现，零外部依赖
"""

import os
import tkinter as tk
from tkinter import font

from todo_app_store import TodoStore

# ── 配置 ──────────────────────────────────────────────────────
APP_NAME = "置顶待办"
DATA_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), ".todo-top-app")
DATA_FILE = os.path.join(DATA_DIR, "todos.json")
WINDOW_W = 320
WINDOW_H = 480

# ── 颜色主题 (暗色) ───────────────────────────────────────────
COLORS = {
    "bg": "#1e1e2e",
    "surface": "#2a2a3e",
    "surface_hover": "#353550",
    "text": "#e0e0f0",
    "text_dim": "#8888a0",
    "accent": "#7c5cfc",
    "accent_light": "#9b7fff",
    "done": "#4ade80",
    "delete": "#f87171",
    "border": "#3a3a50",
    "input_bg": "#2a2a3e",
}


# ── 主应用 ────────────────────────────────────────────────────
class TodoApp:
    MIN_H = 200

    def __init__(self):
        self.store = TodoStore(DATA_FILE)

        # ── 窗口 ──
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.geometry(f"{WINDOW_W}x{WINDOW_H}")
        self.root.minsize(280, self.MIN_H)

        # 置顶
        self.root.attributes("-topmost", True)

        # 无边框 + 可拖动
        self.root.overrideredirect(True)

        # 窗口居中
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - WINDOW_W) // 2
        y = (sh - WINDOW_H) // 2
        self.root.geometry(f"+{x}+{y}")

        # ── 样式 ──
        self.root.configure(bg=COLORS["bg"])
        self.root.option_add("*Font", "{Segoe UI} 10")
        self.root.option_add("*Background", COLORS["bg"])
        self.root.option_add("*Foreground", COLORS["text"])

        # ── 拖拽状态 ──
        self._drag_data = {"x": 0, "y": 0, "dragging": False}

        # ── 字体 ──
        self.F9 = tk.font.Font(family="Segoe UI", size=9)
        self.F11 = tk.font.Font(family="Segoe UI", size=11)
        self.F12 = tk.font.Font(family="Segoe UI", size=12)
        self.F13 = tk.font.Font(family="Segoe UI", size=13)
        self.F9B = tk.font.Font(family="Segoe UI", size=9, weight="bold")
        self.F10B = tk.font.Font(family="Segoe UI", size=10, weight="bold")
        self.F12B = tk.font.Font(family="Segoe UI", size=12, weight="bold")
        self.F16B = tk.font.Font(family="Segoe UI", size=16, weight="bold")

        # ── 构建 UI ──
        self._build_ui()
        self._bind_events()
        self._refresh()

        # ── 窗口创建后应用原生样式 ──
        self.root.update_idletasks()
        self._tray_nid = None
        self._old_wndproc = None
        self._wndproc_cb = None
        self._apply_win32_styles()

    # ── UI 构建 ──────────────────────────────────────────────
    def _build_ui(self):
        # 标题栏
        self._build_titlebar()

        # 容器 (列表)
        self._build_list()

        # 底部操作栏
        self._build_bottom_bar()

        # 输入区域
        self._build_input_area()

    def _build_titlebar(self):
        frame = tk.Frame(self.root, bg=COLORS["surface"], height=36)
        frame.pack(fill="x", padx=0, pady=0)
        frame.pack_propagate(False)

        # 拖拽事件
        frame.bind("<Button-1>", self._start_drag)
        frame.bind("<B1-Motion>", self._do_drag)

        # 图标 + 标题 (左)
        left = tk.Frame(frame, bg=COLORS["surface"])
        left.pack(side="left", padx=(10, 0))

        lbl_icon = tk.Label(left, text="☑", font=self.F12B,
                            fg=COLORS["accent_light"], bg=COLORS["surface"])
        lbl_icon.pack(side="left")
        lbl_icon.bind("<Button-1>", self._start_drag)
        lbl_icon.bind("<B1-Motion>", self._do_drag)

        lbl_title = tk.Label(left, text=APP_NAME, font=self.F10B,
                             fg=COLORS["text"], bg=COLORS["surface"])
        lbl_title.pack(side="left", padx=(6, 0))
        lbl_title.bind("<Button-1>", self._start_drag)
        lbl_title.bind("<B1-Motion>", self._do_drag)

        # 计数徽标
        self.lbl_count = tk.Label(left, text="0", font=self.F9B,
                                  fg="#ffffff", bg=COLORS["accent"],
                                  padx=5, pady=0, width=2)
        self.lbl_count.pack(side="left", padx=(8, 0))
        self.lbl_count.bind("<Button-1>", self._start_drag)
        self.lbl_count.bind("<B1-Motion>", self._do_drag)

        # 窗口按钮 (右)
        right = tk.Frame(frame, bg=COLORS["surface"])
        right.pack(side="right", padx=(0, 6))

        btn_min = tk.Label(right, text="─", font=self.F12,
                           fg=COLORS["text_dim"], bg=COLORS["surface"],
                           cursor="hand2", padx=8)
        btn_min.pack(side="right")
        btn_min.bind("<Button-1>", lambda e: self._minimize())
        btn_min.bind("<Enter>", lambda e: btn_min.configure(bg=COLORS["surface_hover"], fg=COLORS["text"]))
        btn_min.bind("<Leave>", lambda e: btn_min.configure(bg=COLORS["surface"], fg=COLORS["text_dim"]))

        btn_close = tk.Label(right, text="✕", font=self.F11,
                             fg=COLORS["text_dim"], bg=COLORS["surface"],
                             cursor="hand2", padx=8)
        btn_close.pack(side="right")
        btn_close.bind("<Button-1>", lambda e: self._quit())
        btn_close.bind("<Enter>", lambda e: btn_close.configure(bg=COLORS["delete"], fg="#ffffff"))
        btn_close.bind("<Leave>", lambda e: btn_close.configure(bg=COLORS["surface"], fg=COLORS["text_dim"]))

    def _build_list(self):
        # 外框
        outer = tk.Frame(self.root, bg=COLORS["bg"])
        outer.pack(fill="both", expand=True, padx=0, pady=0)

        # Canvas + Scrollbar 实现滚动
        self.canvas = tk.Canvas(outer, bg=COLORS["bg"], highlightthickness=0)
        scrollbar = tk.Scrollbar(outer, orient="vertical", command=self.canvas.yview,
                                 bg=COLORS["bg"])
        self.scroll_frame = tk.Frame(self.canvas, bg=COLORS["bg"])

        self.scroll_frame.bind("<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw",
                                  width=self.canvas.winfo_reqwidth())
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 鼠标滚轮支持
        self.canvas.bind("<Enter>", lambda e: self._bind_mousewheel())
        self.canvas.bind("<Leave>", lambda e: self._unbind_mousewheel())

        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(
            self.canvas.find_all()[0] if self.canvas.find_all() else "",
            width=e.width))

    def _bind_mousewheel(self):
        if os.name == "nt":
            self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        else:
            self.canvas.bind_all("<Button-4>", self._on_mousewheel)
            self.canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _unbind_mousewheel(self):
        if os.name == "nt":
            self.canvas.unbind_all("<MouseWheel>")
        else:
            self.canvas.unbind_all("<Button-4>")
            self.canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event):
        if os.name == "nt":
            self.canvas.yview_scroll(-1 * (event.delta // 120), "units")
        else:
            if event.num == 4:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self.canvas.yview_scroll(1, "units")

    def _build_bottom_bar(self):
        frame = tk.Frame(self.root, bg=COLORS["bg"], height=28)
        frame.pack(fill="x", padx=10, pady=(0, 0))
        frame.pack_propagate(False)

        # 清除已完成
        self.btn_clear = tk.Label(frame, text="清除已完成",
                                  font=self.F9,
                                  fg=COLORS["text_dim"], bg=COLORS["bg"],
                                  cursor="hand2")
        self.btn_clear.pack(side="left")
        self.btn_clear.bind("<Button-1>", lambda e: self._clear_done())
        self.btn_clear.bind("<Enter>", lambda e: self.btn_clear.configure(fg=COLORS["delete"]))
        self.btn_clear.bind("<Leave>", lambda e: self.btn_clear.configure(fg=COLORS["text_dim"]))

        # 已完成计数
        self.lbl_done = tk.Label(frame, text="已完成 0",
                                 font=self.F9,
                                 fg=COLORS["text_dim"], bg=COLORS["bg"])
        self.lbl_done.pack(side="right")

    def _build_input_area(self):
        frame = tk.Frame(self.root, bg=COLORS["bg"])
        frame.pack(fill="x", padx=10, pady=(6, 10))

        entry_font = font.Font(family="Segoe UI", size=10)

        self.entry = tk.Entry(frame, font=entry_font,
                              fg=COLORS["text"], bg=COLORS["input_bg"],
                              insertbackground=COLORS["text"],
                              relief="flat", bd=8,
                              highlightthickness=1,
                              highlightbackground=COLORS["border"],
                              highlightcolor=COLORS["accent"])
        self.entry.pack(side="left", fill="x", expand=True, ipady=4)
        self.entry.insert(0, "")
        self.entry.bind("<Return>", self._add_todo)

        # 占位符
        self._placeholder = "输入新待办，回车添加..."
        self.entry.insert(0, self._placeholder)
        self.entry.configure(fg=COLORS["text_dim"])
        self.entry.bind("<FocusIn>", self._on_entry_focus)
        self.entry.bind("<FocusOut>", self._on_entry_blur)

        btn_add = tk.Label(frame, text="＋", font=self.F16B,
                           fg="#ffffff", bg=COLORS["accent"],
                           cursor="hand2", padx=10, pady=2)
        btn_add.pack(side="right", padx=(6, 0))
        btn_add.bind("<Button-1>", self._add_todo)
        btn_add.bind("<Enter>", lambda e: btn_add.configure(bg=COLORS["accent_light"]))
        btn_add.bind("<Leave>", lambda e: btn_add.configure(bg=COLORS["accent"]))

    # ── 输入框占位符 ─────────────────────────────────────────
    def _on_entry_focus(self, event=None):
        if self.entry.get() == self._placeholder:
            self.entry.delete(0, "end")
            self.entry.configure(fg=COLORS["text"])

    def _on_entry_blur(self, event=None):
        if not self.entry.get().strip():
            self.entry.delete(0, "end")
            self.entry.insert(0, self._placeholder)
            self.entry.configure(fg=COLORS["text_dim"])

    # ── 事件绑定 ─────────────────────────────────────────────
    def _bind_events(self):
        # 全局快捷键
        self.root.bind("<Escape>", lambda e: self._quit())
        self.root.bind("<Control-w>", lambda e: self._quit())

    # ── 窗口操作 ─────────────────────────────────────────────
    def _start_drag(self, event):
        self._drag_data["x"] = event.x_root
        self._drag_data["y"] = event.y_root

    def _do_drag(self, event):
        dx = event.x_root - self._drag_data["x"]
        dy = event.y_root - self._drag_data["y"]
        x = self.root.winfo_x() + dx
        y = self.root.winfo_y() + dy
        self.root.geometry(f"+{int(x)}+{int(y)}")
        self._drag_data["x"] = event.x_root
        self._drag_data["y"] = event.y_root

    # ── Win32 原生样式 ──────────────────────────────────────
    def _apply_win32_styles(self):
        try:
            from ctypes import windll, c_int, byref
            hwnd = windll.user32.GetParent(self.root.winfo_id())
            if not hwnd:
                return

            # 窗口圆角 (Windows 11)
            try:
                DWMWA_WINDOW_CORNER_PREFERENCE = 33
                DWM_WINDOW_CORNER_ROUND = 2
                windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, DWMWA_WINDOW_CORNER_PREFERENCE,
                    byref(c_int(DWM_WINDOW_CORNER_ROUND)), 4
                )
            except Exception:
                pass

            # 隐藏 Alt+Tab
            try:
                GWL_EXSTYLE = -20
                WS_EX_TOOLWINDOW = 0x00000080
                style = windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_TOOLWINDOW)
            except Exception:
                pass

            # 系统托盘 + 全局快捷键
            try:
                self._setup_tray_and_hotkey(hwnd)
            except Exception:
                pass
        except Exception:
            pass

    # ── 系统托盘 + 全局快捷键 (Win32) ──────────────────────
    def _setup_tray_and_hotkey(self, hwnd):
        from ctypes import wintypes, WINFUNCTYPE, c_int64, c_uint, c_uint64

        hwnd = windll.user32.GetParent(self.root.winfo_id())

        # ── NOTIFYICONDATA ──
        class NOTIFYICONDATAW(ctypes.Structure):
            _pack_ = 4
            _fields_ = [
                ("cbSize", wintypes.DWORD),
                ("hWnd", wintypes.HWND),
                ("uID", wintypes.UINT),
                ("uFlags", wintypes.UINT),
                ("uCallbackMessage", wintypes.UINT),
                ("hIcon", wintypes.HICON),
                ("szTip", wintypes.WCHAR * 128),
                ("dwState", wintypes.DWORD),
                ("dwStateMask", wintypes.DWORD),
                ("szInfo", wintypes.WCHAR * 256),
                ("uVersion", wintypes.UINT),
                ("szInfoTitle", wintypes.WCHAR * 64),
                ("dwInfoFlags", wintypes.DWORD),
                ("guidItem", ctypes.c_byte * 16),
                ("hBalloonIcon", wintypes.HICON),
            ]

        NIF_MESSAGE = 1
        NIF_ICON = 2
        NIF_TIP = 4
        WM_APP_TRAY = 0x8000 + 100
        nid = NOTIFYICONDATAW()
        nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        nid.hWnd = hwnd
        nid.uID = 1
        nid.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP
        nid.uCallbackMessage = WM_APP_TRAY
        nid.hIcon = windll.user32.LoadIconW(0, 32512)  # IDI_APPLICATION
        nid.szTip = "置顶待办\x00"
        windll.shell32.Shell_NotifyIconW(0, ctypes.byref(nid))  # NIM_ADD
        self._tray_nid = nid

        # ── 全局快捷键 Ctrl+Shift+T ──
        MOD_CONTROL = 0x0002
        MOD_SHIFT = 0x0004
        MOD_NOREPEAT = 0x4000
        VK_T = 0x54
        windll.user32.RegisterHotKey(hwnd, 1, MOD_CONTROL | MOD_SHIFT | MOD_NOREPEAT, VK_T)

        # ── 窗口子类化 ──
        GWL_WNDPROC = -4
        WNDPROC = WINFUNCTYPE(c_int64, c_int64, c_uint, c_uint64, c_int64)

        def wndproc(h, msg, wp, lp):
            if msg == WM_APP_TRAY:
                lo = lp & 0xFFFF
                if lo == 0x202:  # WM_LBUTTONUP
                    self._toggle_visibility()
                elif lo == 0x205:  # WM_RBUTTONUP
                    self._toggle_visibility()
                return 0
            if msg == 0x0312:  # WM_HOTKEY
                self._toggle_visibility()
                return 0
            if msg == 0x0002:  # WM_DESTROY
                try:
                    windll.shell32.Shell_NotifyIconW(2, ctypes.byref(nid))  # NIM_DELETE
                except Exception:
                    pass
            return windll.user32.CallWindowProcW(self._old_wndproc, h, msg, wp, lp)

        self._wndproc_cb = WNDPROC(wndproc)
        self._old_wndproc = windll.user32.SetWindowLongPtrW(hwnd, GWL_WNDPROC, self._wndproc_cb)

    def _toggle_visibility(self):
        if self.root.state() == "withdrawn" or not self.root.winfo_viewable():
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
        else:
            self.root.withdraw()

    def _minimize(self):
        self.root.withdraw()

    def _quit(self):
        self.store._save()
        if self._tray_nid is not None:
            try:
                windll.shell32.Shell_NotifyIconW(2, ctypes.byref(self._tray_nid))  # NIM_DELETE
            except Exception:
                pass
        self.root.destroy()

    # ── 业务逻辑 ─────────────────────────────────────────────
    def _add_todo(self, event=None):
        text = self.entry.get().strip()
        if not text or text == self._placeholder:
            return

        self.store.add(text)
        self.entry.delete(0, "end")
        self._refresh()
        # 滚动到底部
        self.root.after(50, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        self.canvas.yview_moveto(1.0)

    def _toggle_todo(self, todo_id):
        self.store.toggle(todo_id)
        self._refresh()

    def _delete_todo(self, todo_id):
        self.store.delete(todo_id)
        self._refresh()

    def _clear_done(self):
        self.store.clear_done()
        self._refresh()

    # ── 渲染 ─────────────────────────────────────────────────
    def _refresh(self):
        # 清除现有项
        for w in self.scroll_frame.winfo_children():
            w.destroy()

        pending = self.store.get_pending()
        done = self.store.get_done()

        # 更新计数
        self.lbl_count.configure(text=str(len(pending)))
        self.lbl_done.configure(text=f"已完成 {len(done)}")
        self.btn_clear.configure(fg=COLORS["text_dim"] if done else COLORS["bg"],
                                 cursor="hand2" if done else "arrow")

        # 空状态
        if not pending and not done:
            lbl = tk.Label(self.scroll_frame,
                           text="☑ 没有待办事项\n\n输入内容开始添加",
                           font=self.F11,
                           fg=COLORS["text_dim"], bg=COLORS["bg"],
                           justify="center")
            lbl.pack(expand=True, fill="both", pady=60)
            return

        # 待办项
        all_items = pending + done
        for todo in all_items:
            self._render_todo_item(todo)

    def _render_todo_item(self, todo):
        is_done = todo["done"]
        item_id = todo["id"]

        frame = tk.Frame(self.scroll_frame, bg=COLORS["bg"], cursor="hand2")
        frame.pack(fill="x", padx=6, pady=1)

        # 悬停效果
        frame.bind("<Enter>", lambda e, f=frame, i=item_id:
            f.configure(bg=COLORS["surface"]) if not self._is_dragging(f) else None)
        frame.bind("<Leave>", lambda e, f=frame:
            f.configure(bg=COLORS["bg"]))

        # 行内布局
        inner = tk.Frame(frame, bg=frame["bg"])
        inner.pack(fill="x", padx=6, pady=5)

        # Checkbox (替代)
        cb_frame = tk.Frame(inner, bg=inner["bg"], width=20, height=20)
        cb_frame.pack(side="left")
        cb_frame.pack_propagate(False)

        cb_bg = COLORS["done"] if is_done else COLORS["border"]
        cb_text = "✓" if is_done else ""

        lbl_cb = tk.Label(cb_frame, text=cb_text,
                          font=self.F10B,
                          fg=COLORS["bg"] if is_done else COLORS["bg"],
                          bg=cb_bg,
                          relief="flat", bd=0,
                          cursor="hand2")
        lbl_cb.pack(fill="both", expand=True)
        lbl_cb.bind("<Button-1>", lambda e, i=item_id: self._toggle_todo(i))

        # 文本
        text_color = COLORS["text_dim"] if is_done else COLORS["text"]
        text_font = font.Font(family="Segoe UI", size=10,
                              overstrike=is_done)

        lbl_text = tk.Label(inner, text=todo["text"],
                            font=text_font,
                            fg=text_color, bg=inner["bg"],
                            anchor="w", wraplength=220,
                            justify="left")
        lbl_text.pack(side="left", fill="x", expand=True, padx=(8, 4))
        lbl_text.bind("<Button-1>", lambda e, i=item_id: self._toggle_todo(i))

        # 删除按钮
        btn_del = tk.Label(inner, text="×",
                           font=self.F13,
                           fg=COLORS["bg"], bg=inner["bg"],
                           cursor="hand2", padx=4)
        btn_del.pack(side="right")
        btn_del.bind("<Button-1>", lambda e, i=item_id: self._delete_todo(i))

        # 悬停显示删除按钮
        def show_del(e, lbl=btn_del):
            lbl.configure(fg=COLORS["delete"])
        def hide_del(e, lbl=btn_del):
            lbl.configure(fg=frame["bg"])
            # Check if we should show based on parent bg
            if frame["bg"] != COLORS["bg"]:
                lbl.configure(fg=COLORS["text_dim"])
        btn_del.bind("<Enter>", show_del)
        btn_del.bind("<Leave>", hide_del)

        # 行悬停时显示删除
        orig = frame["bg"]
        frame._last_bg = COLORS["bg"]
        frame.bind("<Enter>", lambda e, f=frame, d=btn_del:
            self._on_item_hover(f, d, True, item_id))
        frame.bind("<Leave>", lambda e, f=frame, d=btn_del:
            self._on_item_hover(f, d, False, item_id))

    def _on_item_hover(self, frame, del_btn, enter, item_id):
        if enter:
            frame.configure(bg=COLORS["surface"])
            del_btn.configure(fg=COLORS["text_dim"])
        else:
            frame.configure(bg=COLORS["bg"])
            del_btn.configure(fg=COLORS["bg"])

    def _is_dragging(self, frame):
        return False

    # ── 启动 ─────────────────────────────────────────────────
    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = TodoApp()
    app.run()
