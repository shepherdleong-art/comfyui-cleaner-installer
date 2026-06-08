"""
ComfyUI Cleaner setup wizard.

Installs the cleaner into a dedicated subdirectory inside the selected
ComfyUI folder, then registers a per-user uninstall entry.
"""
import ctypes
import os
import shutil
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

APP_NAME = "ComfyUI 一键清理"
APP_ID = "PUIKIN.ComfyUI.Cleaner"
PUBLISHER = "PUIKIN"
REG_KEY = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\ComfyUI_Cleaner"

INSTALL_SUBDIR = "ComfyUI-Cleaner"
CLEANER_EXE = "ComfyUI一键清理.exe"
UNINSTALL_EXE = "uninstall.exe"
ICON_FILE = "comfyui-cleaner.ico"
LNK_NAME = "ComfyUI 一键清理.lnk"

BG = "#0f0e17"
CARD = "#1a1930"
ACCENT = "#7c3aed"
CYAN = "#60a5fa"
GREEN = "#34d399"
YELLOW = "#fbbf24"
WHITE = "#e2e8f0"
MUTED = "#94a3b8"
DIM = "#334155"

DESKTOP = os.path.join(os.environ.get("USERPROFILE", os.path.expanduser("~")), "Desktop")


def payload_dir():
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(sys.argv[0])))
    return os.path.dirname(os.path.abspath(__file__))


def quote(path):
    return f'"{path}"'


def write_uninstall_entry(install_dir):
    """Register in the current user's Apps & features list."""
    import winreg

    cleaner_path = os.path.join(install_dir, CLEANER_EXE)
    uninstall_path = os.path.join(install_dir, UNINSTALL_EXE)
    icon_path = os.path.join(install_dir, ICON_FILE)

    estimated_kb = 0
    for root, _, files in os.walk(install_dir):
        for file_name in files:
            try:
                estimated_kb += os.path.getsize(os.path.join(root, file_name)) // 1024
            except OSError:
                pass

    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, REG_KEY, 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, APP_NAME)
        winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, "1.0.0")
        winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, PUBLISHER)
        winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, install_dir)
        winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, quote(uninstall_path))
        winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, icon_path if os.path.exists(icon_path) else cleaner_path)
        winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "EstimatedSize", 0, winreg.REG_DWORD, max(estimated_kb, 1))


def create_shortcut(location, target, working_dir, icon_path):
    from win32com.client import Dispatch

    os.makedirs(location, exist_ok=True)
    shortcut_path = os.path.join(location, LNK_NAME)
    if os.path.exists(shortcut_path):
        os.remove(shortcut_path)

    shell = Dispatch("WScript.Shell")
    shortcut = shell.CreateShortcut(shortcut_path)
    shortcut.TargetPath = target
    shortcut.WorkingDirectory = working_dir
    shortcut.Description = f"{APP_NAME} - 释放 ComfyUI / GPU 残留进程"
    shortcut.WindowStyle = 1
    shortcut.IconLocation = icon_path if os.path.exists(icon_path) else target
    shortcut.Save()


class SetupWizard:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} - 安装向导")
        self.root.geometry("500x560")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)

        try:
            self.root.iconbitmap(os.path.join(payload_dir(), ICON_FILE))
        except Exception:
            pass
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
        except Exception:
            pass

        self.selected_path = None
        self.install_step = -1
        self.install_errors = []
        self.step_labels = []

        self.canvas = tk.Canvas(self.root, bg=BG, highlightthickness=0, width=500, height=560)
        self.canvas.pack(fill="both", expand=True)
        self.draw_bg()
        self.show_step1()

    def draw_bg(self):
        for y in range(560):
            t = y / 560
            r = int(15 + t * 7)
            g = int(14 + t * 7)
            b = int(23 + t * 14)
            self.canvas.create_line(0, y, 500, y, fill=f"#{r:02x}{g:02x}{b:02x}", width=1)

    def clear_content(self):
        self.canvas.delete("content")
        for child in self.root.winfo_children():
            if child is not self.canvas:
                child.destroy()

    def header(self, title, subtitle):
        self.canvas.create_text(250, 36, text="🧹", font=("Microsoft YaHei UI", 34), fill=WHITE, tags="content")
        self.canvas.create_text(250, 75, text=title, font=("Microsoft YaHei UI", 17, "bold"), fill=WHITE, tags="content")
        if subtitle:
            self.canvas.create_text(250, 100, text=subtitle, font=("Microsoft YaHei UI", 9), fill=MUTED, tags="content")

    def bottom_button(self, text, command, y=490, bg=ACCENT):
        btn = tk.Button(
            self.root,
            text=text,
            font=("Microsoft YaHei UI", 12, "bold"),
            bg=bg,
            fg=WHITE,
            relief="flat",
            activebackground="#6d28d9",
            activeforeground=WHITE,
            cursor="hand2",
            borderwidth=0,
            padx=38,
            pady=10,
            command=command,
        )
        btn.place(x=250, y=y, anchor="center")
        return btn

    def show_step1(self):
        self.clear_content()
        self.header("选择 ComfyUI 目录", "请选择包含 ComfyUI.exe 的文件夹")

        card = tk.Frame(self.root, bg=CARD)
        card.place(x=40, y=125, width=420, height=250)

        tk.Label(card, text="安装器只会创建专属子目录", font=("Microsoft YaHei UI", 13, "bold"), fg=WHITE, bg=CARD).place(x=0, y=28, width=420)
        tk.Label(
            card,
            text="将创建 ComfyUI-Cleaner 文件夹，不会改动 ComfyUI 本体文件。\n卸载时也只删除这个专属文件夹。",
            font=("Microsoft YaHei UI", 10),
            fg=MUTED,
            bg=CARD,
            justify="center",
        ).place(x=0, y=68, width=420)

        tk.Label(card, text="ComfyUI 目录", font=("Microsoft YaHei UI", 10, "bold"), fg=CYAN, bg=CARD, anchor="w").place(x=22, y=130)

        entry_frame = tk.Frame(card, bg=CARD)
        entry_frame.place(x=22, y=158, width=376, height=38)

        self.path_entry = tk.Entry(entry_frame, font=("Microsoft YaHei UI", 10), bg=BG, fg=WHITE, insertbackground=WHITE, relief="flat")
        self.path_entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(8, 6))

        tk.Button(
            entry_frame,
            text="浏览...",
            font=("Microsoft YaHei UI", 9),
            bg=DIM,
            fg=WHITE,
            relief="flat",
            activebackground=ACCENT,
            activeforeground=WHITE,
            cursor="hand2",
            borderwidth=0,
            padx=14,
            pady=7,
            command=self.browse_path,
        ).pack(side="right")

        self.bottom_button("下一步", self.show_step2)

    def show_step2(self):
        path = self.path_entry.get().strip()
        if not path:
            messagebox.showwarning("提示", "请先选择 ComfyUI 安装目录。")
            return
        if not os.path.isdir(path):
            messagebox.showwarning("提示", f"目录不存在：\n{path}")
            return

        self.selected_path = os.path.abspath(path)
        if not os.path.exists(os.path.join(self.selected_path, "ComfyUI.exe")):
            if not messagebox.askyesno("确认目录", "这个目录里没有找到 ComfyUI.exe。\n仍然继续安装吗？"):
                return

        install_dir = os.path.join(self.selected_path, INSTALL_SUBDIR)
        self.clear_content()
        self.header("确认安装", "请确认安装位置和快捷方式")

        card = tk.Frame(self.root, bg=CARD)
        card.place(x=40, y=125, width=420, height=230)

        rows = [
            ("安装位置", install_dir),
            ("桌面图标", os.path.join(DESKTOP, LNK_NAME)),
            ("目录图标", os.path.join(self.selected_path, LNK_NAME)),
            ("卸载入口", "Windows 设置 > 应用 > 已安装的应用"),
        ]
        for index, (label, value) in enumerate(rows):
            y = 22 + index * 50
            tk.Label(card, text=label, font=("Microsoft YaHei UI", 10, "bold"), fg=CYAN, bg=CARD).place(x=18, y=y)
            tk.Label(card, text=value, font=("Microsoft YaHei UI", 9), fg=MUTED, bg=CARD, wraplength=370, justify="left", anchor="w").place(x=18, y=y + 22)

        self.bottom_button("开始安装", self.start_install)
        back = tk.Label(self.root, text="返回上一步", font=("Microsoft YaHei UI", 9), fg=MUTED, bg=BG, cursor="hand2")
        back.place(x=42, y=506)
        back.bind("<Button-1>", lambda _event: self.show_step1())

    def show_step3(self):
        self.clear_content()
        self.header("正在安装...", "")

        card = tk.Frame(self.root, bg=CARD)
        card.place(x=40, y=125, width=420, height=265)

        steps = [
            "创建专属安装目录",
            "复制清理工具",
            "复制卸载程序",
            "复制图标",
            "创建快捷方式",
            "注册卸载入口",
        ]
        self.step_labels = []
        for i, text in enumerate(steps):
            y = 22 + i * 38
            icon = tk.Label(card, text="●", font=("Microsoft YaHei UI", 10), fg=DIM, bg=CARD)
            icon.place(x=18, y=y)
            label = tk.Label(card, text=text, font=("Microsoft YaHei UI", 10), fg=MUTED, bg=CARD, anchor="w")
            label.place(x=45, y=y)
            self.step_labels.append((icon, label))

        self.canvas.create_rectangle(70, 425, 430, 436, fill=DIM, outline="", tags="content")
        self.progress_bar = self.canvas.create_rectangle(70, 425, 70, 436, fill=ACCENT, outline="", tags="content")

        threading.Thread(target=self.do_install, daemon=True).start()
        self.poll_install()

    def do_install(self):
        payload = payload_dir()
        install_dir = os.path.join(self.selected_path, INSTALL_SUBDIR)
        cleaner_path = os.path.join(install_dir, CLEANER_EXE)
        uninstall_path = os.path.join(install_dir, UNINSTALL_EXE)
        icon_path = os.path.join(install_dir, ICON_FILE)

        actions = [
            lambda: os.makedirs(install_dir, exist_ok=True),
            lambda: shutil.copy2(os.path.join(payload, CLEANER_EXE), cleaner_path),
            lambda: shutil.copy2(os.path.join(payload, UNINSTALL_EXE), uninstall_path),
            lambda: shutil.copy2(os.path.join(payload, ICON_FILE), icon_path),
            lambda: (
                create_shortcut(DESKTOP, cleaner_path, install_dir, icon_path),
                create_shortcut(self.selected_path, cleaner_path, install_dir, icon_path),
            ),
            lambda: write_uninstall_entry(install_dir),
        ]

        self.install_errors = []
        for index, action in enumerate(actions):
            self.install_step = index
            try:
                action()
            except Exception as exc:
                self.install_errors.append(str(exc))
        self.install_step = len(actions)

    def poll_install(self):
        step = self.install_step
        total = len(self.step_labels)

        for index, (icon, label) in enumerate(self.step_labels):
            if index < step:
                icon.config(text="✓", fg=GREEN)
                label.config(fg=WHITE)
            elif index == step:
                icon.config(text="●", fg=CYAN)
                label.config(fg=CYAN)
            else:
                icon.config(text="●", fg=DIM)
                label.config(fg=MUTED)

        if step >= 0:
            width = int(360 * min(step, total) / total)
            self.canvas.coords(self.progress_bar, 70, 425, 70 + width, 436)

        if step < total:
            self.root.after(150, self.poll_install)
            return

        self.canvas.itemconfig(self.progress_bar, fill=GREEN)
        self.canvas.coords(self.progress_bar, 70, 425, 430, 436)

        if self.install_errors:
            text = "安装完成，但有部分步骤失败。\n" + "\n".join(self.install_errors[:2])
            color = YELLOW
        else:
            text = "安装完成！"
            color = GREEN

        tk.Label(self.root, text=text, font=("Microsoft YaHei UI", 13, "bold"), fg=color, bg=BG, wraplength=420, justify="center").place(x=250, y=462, anchor="center")
        self.bottom_button("完成", self.root.destroy, y=515)

    def browse_path(self):
        path = filedialog.askdirectory(title="选择 ComfyUI 安装目录")
        if path:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, path)

    def start_install(self):
        self.show_step3()


def main():
    root = tk.Tk()
    SetupWizard(root)
    root.mainloop()


if __name__ == "__main__":
    main()
