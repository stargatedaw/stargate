from sglib.log import LOG, setup_logging


def test_setup_logging():
    setup_logging()
    LOG.info('test_setup_logging')

