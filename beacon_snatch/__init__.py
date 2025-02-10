
import logging

from . import helpers
from .series import BeaconSeries
from .content import BeaconContent
from .collection import BeaconCollection
from .stream import BeaconStreamInfo
from .authentication import BeaconAuthentication


__all__ = ["BeaconSeries", 
           "BeaconContent", 
           "BeaconCollection", 
           "BeaconStreamInfo", 
           "BeaconAuthentication"] 

logging.addLevelName(helpers.LOG_VERBOSE, helpers.LOG_VERBOSE_NAME)
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
