"""
ComfyUI Cleaner uninstaller.

Removes only files created inside the dedicated ComfyUI-Cleaner directory,
plus shortcuts and the per-user uninstall registry entry.
"""
import ctypes
import os
import shutil
import sys
import tkinter as tk
from tkinter import messagebox

APP_NAME = "ComfyUI 一键清理"
INSTALL_SUBDIR = "ComfyUI-Cleaner"
LNK_NAME = "ComfyUI 一键清理.lnk"
REG_KEY = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\ComfyUI_Cleaner"

INSTALL_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
COMFYUI_DIR = os.path.dirname(INSTALL_DIR)
DESKTOP = os.path.join(os.environ.get("USERPROFILE", os.path.expanduser("~")), "Desktop")


def remove_uninstall_entry():
    try:
        import winreg

        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, REG_KEY)
    except OSError:
        pass


def is_managed_install_dir(path):
    return os.path.basename(os.path.normpath(path)) == INSTALL_SUBDIR


def uninstall():
    errors = []

    for shortcut_dir in [DESKTOP, COMFYUI_DIR]:
        shortcut = os.path.join(shortcut_dir, LNK_NAME)
        if os.path.exists(shortcut):
            try:
                os.remove(shortcut)
            except OSError as exc:
                errors.append(f"删除快捷方式失败：{shortcut}\n{exc}")

    remove_uninstall_entry()

    if is_managed_install_dir(INSTALL_DIR) and os.path.isdir(INSTALL_DIR):
        try:
            shutil.rmtree(INSTALL_DIR)
        except OSError as exc:
            errors.append(f"删除安装目录失败：{INSTALL_DIR}\n{exc}")
    else:
        errors.append(f"安全检查未通过，未删除目录：{INSTALL_DIR}")

    return errors


def main():
    root = tk.Tk()
    root.title(f"{APP_NAME} - 卸载")
    root.geometry("430x260")
    root.resizable(False, False)
    root.configure(bg="#0f0e17")

    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("PUIKIN.ComfyUI.Cleaner.Uninstaller")
    except Exception:
        pass

    frame = tk.Frame(root, bg="#0f0e17")
    frame.pack(expand=True, fill="both", padx=30, pady=24)

    tk.Label(frame, text="卸载 ComfyUI 一键清理", font=("Microsoft YaHei UI", 15, "bold"), fg="#e2e8f0", bg="#0f0e17").pack(pady=(8, 8))
    tk.Label(frame, text=f"安装目录：{INSTALL_DIR}", font=("Microsoft YaHei UI", 9), fg="#94a3b8", bg="#0f0e17", wraplength=360).pack(pady=(0, 16))

    status = tk.Label(frame, text="", font=("Microsoft YaHei UI", 10), fg="#34d399", bg="#0f0e17", wraplength=360, justify="center")
    status.pack(pady=(0, 12))

    def on_uninstall():
        if not messagebox.askyesno("确认卸载", "确定卸载 ComfyUI 一键清理吗？"):
            return
        errors = uninstall()
        if errors:
            status.config(text="部分内容需要手动删除：\n" + "\n".join(errors[:2]), fg="#fbbf24")
        else:
            status.config(text="卸载完成。", fg="#34d399")
        btn.config(text="关闭", command=root.destroy)

    btn = tk.Button(
        frame,
        text="确认卸载",
        font=("Microsoft YaHei UI", 11, "bold"),
        bg="#7c3aed",
        fg="white",
        activebackground="#6d28d9",
        activeforeground="white",
        relief="flat",
        padx=30,
        pady=8,
        cursor="hand2",
        borderwidth=0,
        command=on_uninstall,
    )
    btn.pack()

    root.mainloop()


if __name__ == "__main__":
    main()
