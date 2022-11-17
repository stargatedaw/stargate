import os
import shutil

DESKTOP_FILE = """\
[Desktop Entry]
Type=Application
Name=StargateDAW
Comment=Digital Audio Workstation
Exec={EXEC}
Icon={ICON}
"""

def appimage_start_menu_path():
    desktop_dir = os.path.join(
        os.path.expanduser('~'),
        '.local',
        'share',
        'applications',
    )
    desktop_path = os.path.join(desktop_dir, 'stargate.desktop')
    return desktop_dir, desktop_path

def appimage_start_menu_install():
    appimage = os.environ['APPIMAGE']
    appdir = os.environ['APPDIR']
    parent = os.path.dirname(appimage)
    icon = os.path.join(
        appdir,
        'opt',
        'python3.10',
        'share',
        'pixmaps',
        'stargate.png',
    )
    icon_copy = os.path.join(parent, 'stargate.png')
    shutil.copy(icon, icon_copy)
    desktop_dir, desktop_path = appimage_start_menu_path()
    os.makedirs(desktop_dir, exist_ok=True)
    desktop_file = DESKTOP_FILE.format(EXEC=appimage, ICON=icon_copy)
    with open(desktop_path, 'w') as f:
        f.write(desktop_file)

__all__ = [
    'appimage_start_menu_install',
    'appimage_start_menu_path',
]

