from sglib import constants
from sglib.log import LOG

class AbstractIPCTransport:
    """ Abstract class for sending data to and from the engine.
    """
    def send(
        self,
        path: str,
        key: str,
        value: str,
    ):
        """ Send RPC commands to the engine
            Note that these parameters are defined by the engine code,
            see the engine source code for valid values.

            @path:  The path that will route the engine to the correct host
            @key:   The name of the RPC function
            @value: The value passed to the function
        """
        raise NotImplementedError

class AbstractIPC:
    """ Abstract class containing the minimum contract
        to run SG Plugins for host communication to the
        Stargate engine
    """
    def __init__(
        self,
        transport: AbstractIPCTransport,
        a_with_audio: bool=False,
        a_configure_path: str="/stargate/daw",
    ):
        self.transport = transport
        self.configure_path = a_configure_path
        self.with_audio = a_with_audio
        self.m_suppressHostUpdate = not a_with_audio

    def send_configure(self, key, value):
        if not constants.IPC_ENABLED and key != "exit":
            LOG.info(
                "IPC_ENABLED == False, "
                "Would've sent configure message: "
                f'key: "{key}" value: "{value}"'
            )
            return
        self.transport.send(
            self.configure_path,
            key,
            value,
        )
