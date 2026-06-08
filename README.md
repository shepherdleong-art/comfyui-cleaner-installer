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

`dist/` 里的内容是分发产物，适合放到 GitHub Release，不建议直接提交进普通 Git 仓库。

## GitHub 建议

普通仓库只提交源码和图标：

- `src/`
- `assets/`
- `build.py`
- `README.md`
- `.gitignore`
- `.gitattributes`

不要提交：

- `build/`
- `dist/`
- `*.exe`
- `*.zip`

## 安全说明

当前构建出的 exe 默认没有数字签名。Windows Defender、浏览器或 SmartScreen 可能提示风险，这是未签名自制工具常见现象。

如果要公开分发，建议：

- 在 GitHub Release 附上 SHA256；
- 说明它是未签名工具；
- 条件允许时购买代码签名证书。
