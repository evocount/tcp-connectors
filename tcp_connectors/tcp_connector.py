import asyncio
import logging
import uuid
from abc import abstractmethod
from asyncio import Queue

from .exceptions import ConnectionFailed, DestinationNotAvailable

from .base import BaseConnector

logger = logging.getLogger(__name__)


class TCPConnector(BaseConnector):
    """TCPConnector manages a TCP-style connection. It
    defines methods to connect to a TCP server and listen
    to the data. It also has methods to get connection details,
    and stores the received data in an asyncio.Queue
    """
    connection_type = "TCP"

    def __init__(self, *_, **kwargs):
        self.RECEIVED_DATA_QUEUE = Queue(maxsize=500)
        self.host = kwargs.get("host", "")
        self.port = kwargs.get("port", "")
        self.is_connected = False
        self.connection_id = uuid.uuid4().hex[:8]
        self.sockname = "-"
        self.reader = None
        self.writer = None
        self.reconnect_delay = kwargs.get("reconnect_delay", 1.5)

    @abstractmethod
    async def run_proto(self):
        """run_proto should perform any actions required
        by the TCP server to setup send/receive data, including
        authentication.
        """

    @abstractmethod
    async def read_msg(self):
        """read_msg should read the message according to the
        server protocol and return bytes of data.
        """

    @abstractmethod
    async def send_msg(self, data):
        """send_msg should take the data and send it to the
        TCP server, following the correct protocol.

        Arguments:
            data {bytes} -- bytes of data that needs to sent.
        """

    def get_connection_details(self):
        """get_connection_details return a dict containing all
        relevant details associated with the current connection.

        Returns:
            dict -- dict containing connection info.
        """
        return dict(
            connection_type=self.connection_type,
            connection_id=self.connection_id,
            sockname=self.sockname,
            is_connected=self.is_connected,
            host=self.host,
            port=self.port
        )

    async def start(self):
        """start creates a connection to the TCP server,
        and return reader and writer asyncio streams to interact
        with the server.

        Returns:
            tuple -- ([asyncio.StreamReader|None],[asyncio.StreamWriter|None])
        """
        try:
            self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
            self.sockname = self.writer.transport.get_extra_info("sockname")
            await self.run_proto()
            self.is_connected = True
            return self.reader, self.writer
        except ConnectionError as e:
            raise DestinationNotAvailable(
                f'Connection Failed: Error connecting to'
                f' {self.host}:{self.port} - {e}'
            ) from None
        except Exception as e:
            raise ConnectionFailed(e)

    async def listen(self):
        """listen just listens to the server and echoes the
        data it receives.
        """
        while True:
            data = await self.read_msg()
            if not data:
                logger.info('Connection ended.')
                break
            logger.info(f'Received by {self.connection_id}: {data}')

    async def receive_data(self):
        """receive_data persistently tries to receive data from server,
        if the server disconnects, it attempts to reconnect every few seconds
        until a connection is established or the loop is interrupted.
        """
        try:
            await self.handle_received_data()
        except asyncio.CancelledError:
            logger.error(f'Remote connection cancelled.')
        except asyncio.streams.IncompleteReadError:
            self.is_connected = False
            while not self.is_connected:
                await asyncio.sleep(self.reconnect_delay)
                logger.info("Atttempting to reconnect")
                await self.start()
            await self.receive_data()
        finally:
            logger.info(f'Remote closed')
            await self.RECEIVED_DATA_QUEUE.put(None)
            self.RECEIVED_DATA_QUEUE = Queue(maxsize=500)

    async def handle_received_data(self):
        """handle_received_data reads the data and stores it in
        received_data_queue. This queue is exposed for consumption
        by other objects/pipelines.
        """
        while True:
            data = await self.read_msg()
            if not data:
                logger.info('Connection ended.')
                break
            logger.debug("Enqueuing data in RECEIVED_DATA_QUEUE")
            await self.RECEIVED_DATA_QUEUE.put(data)

    def stop(self):
        """close performs connection teardown"""
        self.is_connected = False
        self.RECEIVED_DATA_QUEUE = None
        logger.info('Server closed.')
