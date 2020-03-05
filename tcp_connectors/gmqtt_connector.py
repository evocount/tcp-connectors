import asyncio
import logging
import uuid
import ssl

from gmqtt import Client as MQTTClient

from .exceptions import ConnectionFailed, DestinationNotAvailable

from .base import BaseConnector

logger = logging.getLogger(__name__)


class GMQTTConnector(BaseConnector):
    """GMQTTConnector uses gmqtt library for connectors
    running over MQTT.
    """

    def __init__(self, host, port, subscribe_topic, publish_topic, **kwargs):
        self.host = host
        self.port = port

        # topics
        self.subscribe_topic = subscribe_topic
        self.publish_topic = publish_topic

        # connection
        self.connection_id = uuid.uuid4().hex[:8]
        self.is_connected = False
        self.client = MQTTClient(self.connection_id)

        # callbacks
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.client.on_subscribe = self.on_subscribe
        self.STOP = asyncio.Event()

        # options
        self.ack_topic = kwargs.get('ack_topic')
        self.enable_ssl = kwargs.get('enable_ssl', False)
        self.enable_auth = kwargs.get('enable_auth', False)
        self.username = kwargs.get('username')
        self.password = kwargs.get('password')
        self.client_cert = kwargs.get('client_cert')
        self.client_key = kwargs.get('client_key')
        self.qos = kwargs.get('qos', 2)

    def get_connection_details(self):
        """get_connection_details returns the details
        about the current MQTT connection.
        """
        return dict(
            connection_id=self.connection_id,
            host=self.host,
            port=self.port,
            is_connected=self.is_connected,
            subscribe_topic=self.subscribe_topic,
            publish_topic=self.publish_topic
        )

    def on_connect(self, *args):
        """on_connect is a callback that gets exectued after the
        connection is made.

        Arguments:
            client {MQTTClient} -- gmqtt.MQTTClient
            flags {int} -- connection flags
            rc {int} -- connection result code
            properties {dict} -- config of the current connection
        """
        logger.info("Connected with result code %s", str(args[2]))
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        # client.subscribe("$SYS/#", qos=0)
        if isinstance(self.subscribe_topic, str):
            self.client.subscribe(self.subscribe_topic, qos=self.qos)
        elif isinstance(self.subscribe_topic, list):
            for topic in self.subscribe_topic:
                self.client.subscribe(topic, qos=self.qos)
        else:
            logger.warning('subscribe_topic is either None or an unknown data type.'
                           ' Currently subscribed to 0 topics.')

    async def on_message(self, *args):
        """on_message callback gets executed when the connection receives
        a message.

        Arguments:
            client {MQTTClient} -- gmqtt.MQTTClient
            topic {string} -- topic from which message was received
            payload {bytes} -- actual message bytes received
            qos {string} -- message QOS level (0,1,2)
            properties {dict} -- message properties
        """
        logger.info("%s %s", args[1], str(args[2]))
        return 0

    @staticmethod
    def on_disconnect(*args):
        """on_disconnect is a callback that gets executed
         after a disconnection occurs"""
        logger.info('Disconnected')

    @staticmethod
    def on_subscribe(*args):
        """on_subscribe is a callback that gets executed
        after a subscription is succesful"""
        logger.info('Subscribed')

    def ask_exit(self):
        """sets the STOP variable so that a signal gets sent
        to disconnect the client
        """
        self.STOP.set()

    async def start(self):
        """starts initiates the connnection with the broker

        Raises:
            DestinationNotAvailable: If broker is not available
            ConnectionFailed: If connection failed due to any other reason
        """
        try:
            conn_kwargs = dict(host=self.host, port=self.port)
            if self.enable_auth:
                self.client.set_auth_credentials(self.username, self.password)
            if self.enable_ssl:
                assert self.client_cert and self.client_key, \
                    "Cannot enable ssl without specifying client_cert and client_key"
                ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
                ssl_context.load_cert_chain(self.client_cert,
                                            keyfile=self.client_key)
                conn_kwargs.update(dict(ssl=ssl_context))

            await self.client.connect(**conn_kwargs)
            self.is_connected = True
        except ConnectionRefusedError as e:
            # raising from None suppresses the exception chain
            raise DestinationNotAvailable(
                f'Connection Failed: Error connecting to'
                f' {self.host}:{self.port} - {e}'
            ) from None
        except Exception as e:
            raise ConnectionFailed(e)

    async def publish(self, *args, **kwargs):
        """publishes the message to the topic using client.publish"""
        self.client.publish(*args, **kwargs)

    async def stop(self):
        """force stop the connection with the MQTT broker."""
        await self.client.disconnect()
        self.is_connected = False
