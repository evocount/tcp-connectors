import asyncio
import logging
from asyncio import Queue

import aiohttp
from aiohttp import web

from .exceptions import DestinationNotAvailable

from .base import BaseConnector

logger = logging.getLogger(__name__)


class ServerConnector(BaseConnector):
    """ServerConnector creates a aiohttp based
    Web Server. This connector should be the parent class
    for all push-based connectors.
    """

    connection_type = "SERVER"

    def __init__(self, host="localhost", port=8777):
        self.RECEIVED_DATA_QUEUE = Queue(maxsize=500)
        self.host = host
        self.port = port
        self.app = web.Application()
        self.runner = None
        self.site = None

    async def start(self):
        """start runs the server and starts listening
        to requests.

        Raises:
            DestinationNotAvailable: Raised if the selected port:host
            combo is unavailable
        """
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.host, self.port)
        try:
            await self.site.start()
        except OSError as e:
            raise DestinationNotAvailable(
                f'Connection Failed: Error connecting to'
                f' {self.host}:{self.port} - {e}'
            ) from None

    async def echo(self, _):
        """echo sends a generic response on request. This is to
        demonstrate how to create a request handler.

        Arguments:
            request {HTTPRequest} -- aio request

        Returns:
            HTTPResponse -- http Response for the request
        """
        return web.Response(text=f'Hello from {self.host}:{self.port}\n'
                            f'{self.get_connection_details()}')

    def get_connection_details(self):
        """return the connection details as a dict

        Returns:
            dict -- connection details dictionary
        """
        return dict(connection_type=self.connection_type,
                    host=self.host, port=self.port)

    async def handle_received_data(self, data):
        """handle_received_data stores the data into the
        received_data_queue. This queue is exposed for consumption
        by other objects/pipelines.
        """
        if not data:
            return
        logger.debug("Enqueuing data in RECEIVED_DATA_QUEUE")
        await self.RECEIVED_DATA_QUEUE.put(data)

    async def stop(self):
        """stops the server and runs the cleanup
        """
        self.RECEIVED_DATA_QUEUE = Queue(maxsize=500)
        await self.runner.cleanup()
