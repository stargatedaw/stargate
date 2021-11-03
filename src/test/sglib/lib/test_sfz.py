from sglib.lib import sfz

import glob
import os

def test_parse():
    path = os.path.join(
        os.path.dirname(__file__),
        'sfz',
        '*',
    )

    for path in glob.glob(path):
        # should not raise an exception
        f = sfz.sfz_file(path)
        #assert f.samples, path

