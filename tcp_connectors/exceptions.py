"""
Copyright (C) EvoCount GmbH - All Rights Reserved

Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential.
"""

import logging

logger = logging.getLogger(__name__)


class BaseConnectorException(Exception):
    """all exceptions of Connector should inherit from BaseException"""


class ConnectionFailed(BaseConnectorException):
    """thrown when a persistent connection fails because of
    an unknown reason"""


class DestinationNotAvailable(BaseConnectorException):
    """thrown when a persistent connection attempt fails
    due to destination not being available"""
