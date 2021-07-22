import os

INSTALL_PREFIX = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        *(['..'] * 3),
    ),
)
SHARE_DIR = os.path.join(INSTALL_PREFIX, 'files', 'share')
PRESETS_DIR = os.path.join(INSTALL_PREFIX, 'files', 'presets')
THEMES_DIR = os.path.join(INSTALL_PREFIX, 'files', 'themes')
META_DOT_JSON_PATH = os.path.join(INSTALL_PREFIX, "meta.json")
BIN_DIR = os.path.join(INSTALL_PREFIX, 'scripts')
ENGINE_DIR = os.path.join(INSTALL_PREFIX, 'engine')

