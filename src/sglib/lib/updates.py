import json
import re
from typing import Optional
from urllib.request import urlopen

from sglib.log import LOG
from .util import META_DOT_JSON


def check_for_updates(
    url='https://api.github.com/repos/stargatedaw/stargate/releases/latest',
) -> Optional[str]:
    """ Check for newer versions of Stargate DAW than what is running

        @return: The update name if newer is available, else None
    """
    with urlopen(url) as response:
        j = json.loads(response.read())
    latest_version = j['tag_name']
    match = re.match('release-(.*)', latest_version)
    version = match.group(1)
    installed = META_DOT_JSON['version']['minor']
    if version.split('.') >  installed.split('.'):
        LOG.info(f'{version} > {installed}, requesting update')
        return j['name']
    LOG.info(f'{version} <= {installed}, not requesting update')
    return None

