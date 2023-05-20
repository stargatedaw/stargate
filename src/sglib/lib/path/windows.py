import os

def _is_self_contained():
    dirname = os.path.dirname(
        os.path.abspath(__file__),
    )
    scripts = os.path.join(
        dirname,
        '..',
        '..',
        '..',
        'scripts',
    )
    return os.path.isdir(scripts)

IS_LOCAL_DEVEL = _is_self_contained()

INSTALL_PREFIX = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        *(['..'] * 3),
    ),
).replace('\\', '/')

FONTS_DIR = '/'.join((INSTALL_PREFIX, 'files', 'fonts'))
SHARE_DIR = '/'.join((INSTALL_PREFIX, 'files', 'share'))
PRESETS_DIR = '/'.join((INSTALL_PREFIX, 'files', 'presets'))
PLUGIN_ASSETS_DIR = '/'.join((INSTALL_PREFIX, 'files', 'plugin_assets'))
THEMES_DIR = '/'.join((INSTALL_PREFIX, 'files', 'themes'))
COMMIT_PATH = '/'.join((INSTALL_PREFIX, "COMMIT"))
META_DOT_JSON_PATH = '/'.join((INSTALL_PREFIX, "meta.json"))
BIN_DIR = '/'.join((INSTALL_PREFIX, 'scripts'))
ENGINE_DIR = '/'.join((INSTALL_PREFIX, 'engine'))

