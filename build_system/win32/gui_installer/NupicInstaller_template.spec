a = Analysis([
  # HOMEPATH is defined by pyinstaller
  os.path.join(HOMEPATH, r'support\_mountzlib.py'),
  os.path.join(HOMEPATH, r'support\useUnicode.py'),

  #os.path.join(r'${SourceDir}', 'test.pyw'),

  # These files are unchanged so they are collected from the original source dir
  os.path.join(r'${SourceDir}', 'NupicInstaller.pyw'),
  #os.path.join(r'${SourceDir}', 'firewall.py'),
  os.path.join(r'${SourceDir}', 'installer.py'),

  # config.py is in the work dir because it is generated from a template
  os.path.join(r'${WorkDir}', 'config.py')
  ],
  [$AdditionalSitePackages])

pyz = PYZ(a.pure)

exe = EXE( pyz,
      a.scripts,
      a.binaries,
      [(r'${NupicArchiveName}', r'${NupicArchivePath}', 'BINARY'),
      #('python-${FullPythonVersion}.msi', os.path.join(r'${ExternalDir}', 'python-${FullPythonVersion}.msi'), 'BINARY'),
      #('wxPython${WxVersion}-win32-unicode-${FullWxVersion}-py${PythonIntVersion}.exe', os.path.join(r'${ExternalDir}', 'wxPython${WxVersion}-win32-unicode-${FullWxVersion}-py${PythonIntVersion}.exe'), 'BINARY'),
      ('nupic.png', os.path.join(r'${SourceDir}', 'nupic.png'), 'BINARY'),
      ('setup.ico', os.path.join(r'${SourceDir}', 'setup.ico'), 'BINARY'),
      ('numenta.png', os.path.join(r'${SourceDir}', 'numenta.png'), 'BINARY'),
      ('numenta_logo.png', os.path.join(r'${SourceDir}', 'numenta_logo.png'), 'BINARY'),
      #('license_validator.py', os.path.join(r'${SourceDir}', 'license_validator.py'), 'BINARY'),
      ],

      name='${InstallerName}',
      icon=os.path.join(r'${SourceDir}', 'setup.ico'),
      debug=False,
      strip=False,
      upx=False,
      console=False)
