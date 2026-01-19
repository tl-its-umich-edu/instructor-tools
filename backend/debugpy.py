import debugpy
import logging
from backend import settings


def check_and_enable_debugpy():
    debugpy_address = '0.0.0.0'

    if settings.DEBUGPY_ENABLE:
        logging.debug('DEBUGPY: Enabled Listening on ({0}:{1})'.format(debugpy_address, settings.DEBUGPY_PORT))
        debugpy.listen((debugpy_address, settings.DEBUGPY_PORT))