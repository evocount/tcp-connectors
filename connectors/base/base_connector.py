"""
Copyright (C) EvoCount GmbH - All Rights Reserved

Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential.
"""

import asyncio
from abc import ABC, abstractclassmethod, abstractmethod


class BaseConnector(ABC):
    """BaseConnector is an abstract class that defines
    a structure for all connections to external sources.
    """

    @abstractmethod
    def start(self):
        """start will be used to initiate the connection.
        If it is a persistent connection, this would connect
        with the target, if it is a server, it would run the
        server, if it is a client, it will establish the
        connection with the server.
        """

    @abstractmethod
    def stop(self):
        """close will be used to teardown the connection and
        clear local datastores associated with the connection.
        """

    @abstractmethod
    def get_connection_details(self):
        """get_connection_details should return a dictionary
        will all relevant connection details"""
