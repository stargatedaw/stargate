# -*- coding: utf-8 -*-
"""
This file is part of the Stargate project, Copyright Stargate Team

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

"""


from sglib.lib.util import SHARE_DIR
from sglib.log import LOG
import gettext
import locale
import os

try:
    LOCALE, TEXT_ENCODING = locale.getdefaultlocale()
    LOG.info("locale: {}".format(LOCALE))
    LOG.info("encoding: {}".format(TEXT_ENCODING))
    LANGUAGE = gettext.translation(
        "stargate",
        os.path.join(SHARE_DIR, "locale"),
        [LOCALE],
    )
    LOG.info("LANGUAGE.info: {}".format(LANGUAGE.info()))
    LANGUAGE.install()
    LOG.info("Installed language for {}".format(LOCALE))
    if not "_" in globals():
        LOG.info(
            "'_' not defined by Python gettext module, setting to "
            "LANGUAGE.gettext",
        )
        _ = LANGUAGE.gettext
except Exception as ex:
    LOG.warning(
        f"Could not set locale '{ex}', falling back to English"
    )

if not "_" in globals():
    LOG.info(
        "'_' not defined by Python gettext module, setting to lambda x: x",
    )
    _ = lambda x: x
