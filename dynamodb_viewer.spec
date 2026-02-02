# PyInstaller spec - DynamoDB Viewer para Linux
# Uso: pyinstaller dynamodb_viewer.spec

block_cipher = None

# Incluir pacote src e pasta img (logo para ícone da aplicação)
datas = [('src', 'src'), ('img', 'img')]

hiddenimports = [
    'boto3', 'botocore', 'botocore.exceptions', 'tkinter',
    'ijson', 'tqdm', 'decimal',
    # Pillow/Tkinter integration for ImageTk
    'PIL', 'PIL.Image', 'PIL.ImageTk', 'PIL._tkinter_finder',
    'src', 'src.config', 'src.ui', 'src.ui.windows', 'src.ui.components',
    'src.ui.components.environment_selector', 'src.ui.components.connection_dialog',
    'src.ui.components.import_dialog', 'src.services', 'src.services.dynamodb_service',
    'src.services.batch_importer', 'src.models', 'src.models.filter_row',
    'src.utils', 'src.utils.encoders', 'src.utils.resource_paths',
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
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='dynamodb-viewer',
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
