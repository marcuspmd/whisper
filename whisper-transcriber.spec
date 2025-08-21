# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

block_cipher = None

# Data files to include
datas = [
    ('src/ui/static', 'ui/static'),
    ('src/ui/templates', 'ui/templates'),
    ('requirements.txt', '.'),
    ('README.md', '.'),
    ('LICENSE', '.'),
]

# Hidden imports
hiddenimports = [
    'src',
    'src.app',
    'src.audio',
    'src.audio.capture',
    'src.audio.device_manager',
    'src.config',
    'src.config.settings',
    'src.transcription',
    'src.transcription.whisper_engine',
    'src.translation',
    'src.translation.engines',
    'src.ui',
    'src.ui.desktop',
    'src.ui.web',
    'src.ui.simple',
    'src.utils',
    'src.utils.logger',
    'faster_whisper',
    'transformers',
    'torch',
    'torchaudio',
    'sounddevice',
    'numpy',
    'flask',
    'waitress',
    'googletrans',
    'webrtcvad',
    'soundfile',
    'tkinter',
    'tkinter.ttk',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'threading',
    'multiprocessing',
    'queue',
    'collections',
    'datetime',
    'logging',
    'yaml',
    'dataclasses',
    'typing',
    'pathlib',
    'tempfile',
    'signal',
    'time',
    'json',
    'sys',
    'os',
]

# Binaries to exclude (let system handle these)
excludes = [
    'matplotlib',
    'PIL',
    'cv2',
    'pandas',
    'scipy',
    'sklearn',
    'jupyter',
    'notebook',
    'ipython',
    'pytest',
    'sphinx',
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Console executable
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='whisper-transcriber',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# GUI executable (for desktop mode)
exe_gui = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='whisper-transcriber-gui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if os.path.exists('assets/icon.ico') else None,
)

# Collect everything
coll = COLLECT(
    exe,
    exe_gui,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='whisper-transcriber',
)

# macOS App bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='Whisper Transcriber.app',
        icon='assets/icon.icns' if os.path.exists('assets/icon.icns') else None,
        bundle_identifier='com.marcuspereira.whisper-transcriber',
        version='1.0.0',
        info_plist={
            'NSPrincipalClass': 'NSApplication',
            'NSAppleScriptEnabled': False,
            'CFBundleDocumentTypes': [
                {
                    'CFBundleTypeName': 'Audio Files',
                    'CFBundleTypeRole': 'Viewer',
                    'LSItemContentTypes': ['public.audio'],
                }
            ],
            'NSMicrophoneUsageDescription': 'This app needs microphone access for audio transcription.',
            'LSMinimumSystemVersion': '10.14.0',
        },
    )
