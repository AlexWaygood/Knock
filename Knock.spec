# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['Knock.py'],
             pathex=['C:\\Users\\Alex\\Desktop\\Code dump\\Knock model\\Final version'],
             binaries=[],
             datas=[('CardImages', 'CardImages')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='Knock',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          version='C:\\Users\\Alex\\Desktop\\Code dump\\Knock model\\Final version - Local copy\\Knock_version_info.rc',
          icon='C:\\Users\\Alex\\Desktop\\Code dump\\Knock model\\Final version - Local copy\\CardImages\PyinstallerIcon.ico',
          runtime_tmpdir=None,
          console=True )
