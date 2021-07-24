from sgui.sgqt import QtCore, Signal, Slot
from sglib.ipc.abstract import AbstractIPCTransport
from sglib.log import LOG
from sgui import shared
import socket
import socketserver
import time

__all__ = [
    'SocketIPCServer',
    'SocketIPCTransport',
]

SOCKET_IPC_SERVER = None

class SocketIPCServerSignal(QtCore.QObject):
    handled = Signal(str)

    def handle(self, data):
        self.handled.emit(data)

class UDPHandler(socketserver.DatagramRequestHandler):
    def handle(self):
        data = self.rfile.read().strip()
        data = data.decode('utf-8')
        SOCKET_IPC_SERVER.signal.handle(data)
        # Send a message from a client
        self.wfile.write(
			"Message processed".encode(),
		)

class SocketIPCServerThread(QtCore.QThread):
    def run(self):
        SOCKET_IPC_SERVER._thread()

class SocketIPCServer:
    def __init__(
        self,
        daw_callback,
        we_callback,
        host='127.0.0.1',
        port=30321,
        server=None,
        signal=None,
    ):
        self.daw_callback = daw_callback
        self.we_callback = we_callback
        self.host = host
        self.port = port
        self.server = server
        self.signal = signal
        global SOCKET_IPC_SERVER
        SOCKET_IPC_SERVER = self

    def _thread(self):
        with socketserver.UDPServer(
            (self.host, self.port),
            UDPHandler
        ) as self.server:
            self.server.serve_forever()

    def start(self):
        self.signal = SocketIPCServerSignal()
        self.signal.handled.connect(self._handle)
        self.thread = SocketIPCServerThread()
        self.thread.start()

    def _handle(self, data: str):
        path, value = data.split("\n", 1)
        if path == "stargate/daw":
            self.daw_callback(value)
        elif path == "stargate/wave_edit":
            self.we_callback(value)
        else:
            LOG.error(f"Received unknown path from engine: {path}")

    def free(self):
        self.server.shutdown()

class SocketIPCTransport(AbstractIPCTransport):
    def __init__(
        self,
        host='127.0.0.1',
        port=19271,
    ):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.connect((self.host, self.port))

    def send(
        self,
        path,
        key,
        value,
    ):
        message = "\n".join([path, key, value])
        assert len(message) < 24576, (len(message), message)
        message = message.encode('ascii')
        for wait in (0.1, 0.3, 0.6):
            try:
                self.socket.sendall(message)
                LOG.info(f"Sent message: {message}")
                return
            except Exception as ex:
                LOG.warning(f"Error: {ex}, waiting {wait}s to retry")
                time.sleep(wait)
        LOG.error(f"Failed to send {message}")

