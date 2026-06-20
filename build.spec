# PyInstaller spec — сборка Fleet Manager в один exe.
# Сборка:  python -m PyInstaller build.spec --noconfirm
# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('ui/logo.png', 'ui'), ('ui/snake.gif', 'ui')],
    hiddenimports=['PySide6.QtWidgets', 'PySide6.QtGui', 'PySide6.QtCore'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Лишние модули Qt не нужны автономному калькулятору — уменьшаем размер.
    excludes=[
        'matplotlib', 'tkinter', 'numpy', 'scipy', 'networkx',
        'PySide6.QtQml', 'PySide6.QtQuick', 'PySide6.Qt3DCore',
        'PySide6.QtWebEngineCore', 'PySide6.QtNetwork', 'PySide6.QtMultimedia',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Fleet Manager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # GUI без консоли
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
