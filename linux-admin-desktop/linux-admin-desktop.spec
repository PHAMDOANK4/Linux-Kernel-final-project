# -*- mode: python ; coding: utf-8 -*-
import os
import sys

block_cipher = None

# Determine project root (parent of the spec file location)
project_root = os.path.abspath(os.path.join(os.getcwd()))
scripts_src = os.path.join(project_root, "scripts")

a = Analysis(
    ["main.py"],
    pathex=[project_root],
    binaries=[],
    datas=[(scripts_src, "scripts")],
    hiddenimports=[
        "app.database", "app.auth", "app.executor",
        "app.parsers", "app.logging", "app.rbac",
        "ui.login_window", "ui.main_window",
        "ui.file_manager_widget", "ui.task_scheduler_widget",
        "ui.system_time_widget", "ui.package_manager_widget",
        "ui.logs_viewer_widget",
        "sqlalchemy", "werkzeug", "pytz",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="linux-admin-desktop",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
