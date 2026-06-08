"""
Build ComfyUI Cleaner release package.

Run:
  python -m pip install -r requirements-dev.txt
  python build.py
"""
import os
import shutil
import subprocess
import sys
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")
ASSETS = os.path.join(ROOT, "assets")
BUILD = os.path.join(ROOT, "build")
DIST = os.path.join(ROOT, "dist")
PAYLOAD = os.path.join(BUILD, "payload")

CLEANER_NAME = "ComfyUI一键清理"
SETUP_NAME = "ComfyUI清理工具_Setup"
ICON = os.path.join(ASSETS, "comfyui-cleaner.ico")


def run(cmd):
    print(" ".join(cmd))
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def clean():
    for path in [BUILD, DIST]:
        if os.path.exists(path):
            shutil.rmtree(path)
    os.makedirs(BUILD, exist_ok=True)
    os.makedirs(DIST, exist_ok=True)


def build_cleaner():
    run([
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--windowed",
        f"--icon={ICON}",
        f"--name={CLEANER_NAME}",
        f"--distpath={PAYLOAD}",
        f"--workpath={os.path.join(BUILD, 'cleaner')}",
        f"--specpath={BUILD}",
        f"--add-data={ICON};.",
        "--clean",
        os.path.join(SRC, "comfyui_cleaner.pyw"),
    ])


def build_uninstaller():
    run([
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--windowed",
        f"--icon={ICON}",
        "--name=uninstall",
        f"--distpath={PAYLOAD}",
        f"--workpath={os.path.join(BUILD, 'uninstall')}",
        f"--specpath={BUILD}",
        "--clean",
        os.path.join(SRC, "uninstaller.pyw"),
    ])


def build_setup():
    cleaner_exe = os.path.join(PAYLOAD, f"{CLEANER_NAME}.exe")
    uninstall_exe = os.path.join(PAYLOAD, "uninstall.exe")
    for required in [cleaner_exe, uninstall_exe, ICON]:
        if not os.path.exists(required):
            raise FileNotFoundError(required)

    run([
        sys.executable,
        "-m",
        "PyInstaller",
        "--onedir",
        "--windowed",
        f"--icon={ICON}",
        f"--name={SETUP_NAME}",
        f"--distpath={DIST}",
        f"--workpath={os.path.join(BUILD, 'setup')}",
        f"--specpath={BUILD}",
        f"--add-data={cleaner_exe};.",
        f"--add-data={uninstall_exe};.",
        f"--add-data={ICON};.",
        "--clean",
        os.path.join(SRC, "setup_installer.pyw"),
    ])


def create_zip():
    folder = os.path.join(DIST, SETUP_NAME)
    zip_path = os.path.join(DIST, f"{SETUP_NAME}.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for root, _, files in os.walk(folder):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                archive.write(file_path, os.path.relpath(file_path, DIST))
    print(f"Created: {zip_path}")


def main():
    clean()
    build_cleaner()
    build_uninstaller()
    build_setup()
    create_zip()
    print("Build complete.")


if __name__ == "__main__":
    main()
