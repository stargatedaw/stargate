from sglib.ipc.abstract import AbstractIPCTransport
import liblo

class SocketIPCTransport(AbstractIPCTransport):
    def __init__(
        self,
        address: liblo.Address,
    ):
        self.address = address

    @staticmethod
    def new(
        port:int,
    ):
        return SocketIPCTransport(
            liblo.Address(port),
        )

    def send(
        self,
        path,
        key,
        value,
    ):
        liblo.send(
            self.address,
            path,
            key,
            value,
        )

