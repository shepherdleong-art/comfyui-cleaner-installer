# ComfyUI 一键清理安装器

这是一个 Windows 小工具项目，用来打包和安装 `ComfyUI 一键清理`。

清理器的用途是结束 ComfyUI 相关残留进程，帮助释放 GPU 显存和后台进程占用。安装器会把清理器放进用户选择的 ComfyUI 目录中，并创建桌面快捷方式。

> 非官方工具。使用前请确认你理解它会结束 ComfyUI / Python / uv / 终端相关残留进程。

## 项目结构

```text
assets/
  comfyui-cleaner.ico
src/
  comfyui_cleaner.pyw
  setup_installer.pyw
  uninstaller.pyw
build.py
requirements-dev.txt
```

## 安装器行为

安装时：

- 用户选择 ComfyUI 目录；
- 创建专属目录 `ComfyUI-Cleaner/`；
- 复制清理器、卸载器和图标；
- 创建桌面快捷方式；
- 在当前用户注册卸载入口。

卸载时：

- 删除桌面快捷方式；
- 删除 ComfyUI 目录中的快捷方式；
- 删除 `ComfyUI-Cleaner/` 专属目录；
- 删除当前用户卸载注册表项。

为了避免误删用户自己的文件，卸载器只会删除目录名严格等于 `ComfyUI-Cleaner` 的安装目录。

## 构建

需要 Windows、Python 3 和 PyInstaller：

```powershell
python -m pip install -r requirements-dev.txt
python build.py
```

构建结果：

```text
dist/ComfyUI清理工具_Setup/
dist/ComfyUI清理工具_Setup.zip
```
## 致谢

本项目由 shepherdleong-art 制作。

开发与整理过程中使用了：

- OpenAI Codex
- Claude Code
