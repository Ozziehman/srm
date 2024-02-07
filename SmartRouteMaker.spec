# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['wsgi.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('srm/__init__.py', 'srm'),
        ('srm/Core/Routes.py', 'srm/Core'),
        ('srm/Core/SmartRouteMaker/Analyzer.py', 'srm/Core/SmartRouteMaker'),
        ('srm/Core/SmartRouteMaker/Graph.py', 'srm/Core/SmartRouteMaker'),
        ('srm/Core/SmartRouteMaker/Planner.py', 'srm/Core/SmartRouteMaker'),
        ('srm/Core/SmartRouteMaker/Visualizer.py', 'srm/Core/SmartRouteMaker'),
        ('srm/Core/SmartRouteMaker/__init__.py', 'srm/Core/SmartRouteMaker'),
        ('srm/Core/SmartRouteMaker/config/VisualisationSettings.json', 'srm/Core/SmartRouteMaker/config'),
        ('srm/Core/SmartRouteMaker/Facades/SmartRouteMakerFacade.py', 'srm/Core/SmartRouteMaker/Facades'),
        ('srm/Core/Static/css/leaflet.css', 'srm/Core/Static/css'),
        ('srm/Core/Static/css/srm.css', 'srm/Core/Static/css'),
        ('srm/Core/Static/ico/srm-favicon.ico', 'srm/Core/Static/ico'),
        ('srm/Core/Static/Image/best_path_points.png', 'srm/Core/Static/Image'),
        ('srm/Core/Static/Image/elevation.png', 'srm/Core/Static/Image'),
        ('srm/Core/Static/Image/leaf_points.png', 'srm/Core/Static/Image'),
        ('srm/Core/Static/Image/surface_percentage.png', 'srm/Core/Static/Image'),
        ('srm/Core/Static/js/map_contextmenu.js', 'srm/Core/Static/js'),
        ('srm/Core/Static/js/srm_interactive_map.js', 'srm/Core/Static/js'),
        ('srm/Core/Static/js/lib/leaflet.js', 'srm/Core/Static/js/lib'),
        ('srm/Core/Templates/home.html', 'srm/Core/Templates'),
        ('srm/Core/Templates/result.html', 'srm/Core/Templates'),
        ('srm/Core/Templates/Includes/branding.html', 'srm/Core/Templates/Includes'),
        ('srm/Core/Templates/Includes/topbar.html', 'srm/Core/Templates/Includes'),
        ('srm/Core/Templates/Layouts/base.html', 'srm/Core/Templates/Layouts'),
        ('srm/Site/Routes.py', 'srm/Site'),
    ],
    hiddenimports=[],
    hookspath=['hooks'],
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
    a.zipfiles,
    a.datas,
    name='SmartRouteMaker',
    debug=False,
    strip=False,
    upx=True,
    console=True,
    icon='srm\Core\Static\ico\srm.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='SmartRouteMaker'
)