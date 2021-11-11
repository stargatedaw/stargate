from sglib.constants import MAJOR_VERSION
import os
import sys


# Running from the source repo
if os.path.join("src", "sglib") in os.path.abspath(__file__):
    IS_LOCAL_DEVEL = True
    INSTALL_PREFIX = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            *([".."] * 3)
        )
    )
    BIN_DIR = os.path.join(INSTALL_PREFIX, 'scripts')
    COMMIT_PATH = os.path.join(INSTALL_PREFIX, "COMMIT")
    ENGINE_DIR = os.path.join(INSTALL_PREFIX, 'engine')
    FONTS_DIR = os.path.join(INSTALL_PREFIX, 'files', 'fonts')
    META_DOT_JSON_PATH = os.path.join(INSTALL_PREFIX, "meta.json")
    PLUGIN_ASSETS_DIR = os.path.join(INSTALL_PREFIX, 'files', 'plugin_assets')
    PRESETS_DIR = os.path.join(INSTALL_PREFIX, 'files', 'presets')
    SHARE_DIR = os.path.join(INSTALL_PREFIX, 'files', 'share')
    THEMES_DIR = os.path.join(INSTALL_PREFIX, 'files', 'themes')
# Running installed as a pyinstaller exe
else:
    IS_LOCAL_DEVEL = False
    INSTALL_PREFIX = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            *(['..'] * 3),
        ),
    )

    BIN_DIR = os.path.join(INSTALL_PREFIX, 'scripts')
    COMMIT_PATH = os.path.join(INSTALL_PREFIX, "COMMIT")
    ENGINE_DIR = os.path.join(INSTALL_PREFIX, 'engine')
    FONTS_DIR = os.path.join(INSTALL_PREFIX, 'files', 'fonts')
    META_DOT_JSON_PATH = os.path.join(INSTALL_PREFIX, "meta.json")
    PLUGIN_ASSETS_DIR = os.path.join(INSTALL_PREFIX, 'files', 'plugin_assets')
    PRESETS_DIR = os.path.join(INSTALL_PREFIX, 'files', 'presets')
    SHARE_DIR = os.path.join(INSTALL_PREFIX, 'files', 'share')
    THEMES_DIR = os.path.join(INSTALL_PREFIX, 'files', 'themes')

