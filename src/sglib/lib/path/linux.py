from sglib.constants import MAJOR_VERSION
import os


# Running from the source repo
if os.path.join("src", "sglib") in os.path.abspath(__file__):
    INSTALL_PREFIX = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            *([".."] * 3)
        )
    )
    FONTS_DIR = os.path.join(INSTALL_PREFIX, 'files', 'fonts')
    SHARE_DIR = os.path.join(INSTALL_PREFIX, 'files', 'share')
    PRESETS_DIR = os.path.join(INSTALL_PREFIX, 'files', 'presets')
    PLUGIN_ASSETS_DIR = os.path.join(INSTALL_PREFIX, 'files', 'plugin_assets')
    THEMES_DIR = os.path.join(INSTALL_PREFIX, 'files', 'themes')
    META_DOT_JSON_PATH = os.path.join(INSTALL_PREFIX, "meta.json")
    BIN_DIR = os.path.join(INSTALL_PREFIX, 'scripts')
# Running installed
else:
    INSTALL_PREFIX = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            *(['..'] * 6),
        )
    )
    _STARGATE_DIR = os.path.join(INSTALL_PREFIX, 'lib', MAJOR_VERSION)
    FONTS_DIR = os.path.join(_STARGATE_DIR, 'fonts')
    SHARE_DIR = os.path.join(INSTALL_PREFIX, 'share')
    PRESETS_DIR = os.path.join(_STARGATE_DIR, 'presets')
    THEMES_DIR = os.path.join(_STARGATE_DIR, 'themes')
    PLUGIN_ASSETS_DIR = os.path.join(_STARGATE_DIR, 'plugin_assets')
    META_DOT_JSON_PATH = os.path.join(_STARGATE_DIR, "meta.json")
    BIN_DIR = os.path.join(INSTALL_PREFIX, 'bin')

