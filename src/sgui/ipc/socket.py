from sgui.sgqt import QtCore, Signal
from sglib.ipc.abstract import AbstractIPCTransport
from sglib import constants
from sglib.lib import engine
from sglib.log import LOG
from sgui import shared
import select
import socket
import socketserver
import time

__all__ = [
    'SocketIPCServer',
    'SocketIPCTransport',
]

SOCKET_IPC_SERVER = None
IPC_ENGINE_SERVER_PORT = 31999
IPC_UI_SERVER_PORT = 31909
SOCKET_ERROR_SHOWN = False

class SocketIPCServerSignal(QtCore.QObject):
    handled = Signal(str)

    def handle(self, data):
        self.handled.emit(data)

class UDPHandler(socketserver.DatagramRequestHandler):
    def handle(self):
        data = self.rfile.read().strip()
        self.wfile.write(
			"Message received".encode(),
		)
        data = data.decode('utf-8')
        SOCKET_IPC_SERVER.signal.handle(data)

class SocketIPCServerThread(QtCore.QThread):
    def run(self):
        SOCKET_IPC_SERVER._thread()

class SocketIPCServer:
    def __init__(
        self,
        daw_callback,
        we_callback,
        host='127.0.0.1',
        port=IPC_UI_SERVER_PORT,
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
            self.server.max_packet_size = 63000
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
        port=IPC_ENGINE_SERVER_PORT,
    ):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.connect((self.host, self.port))
        self.socket.setblocking(0)

    def send(
        self,
        path,
        key,
        value,
    ):
        message = "\n".join([path, key, value])
        assert len(message) < 60000, (len(message), message)
        message = message.encode('ascii')
        for wait in (0.1, 0.3, 0.6):
            try:
                self.socket.sendall(message)
                ready = select.select(
                    [self.socket],
                    [],
                    [],
                    0.2,
                )
                if ready[0]:
                    self.socket.recv(4096)
                else:
                    LOG.warning("Did not receive a reply from the engine")
                return
            except Exception as ex:
                LOG.warning(f"Error: {ex}, waiting {wait}s to retry")
                time.sleep(wait)
        global SOCKET_ERROR_SHOWN
        if (
            not SOCKET_ERROR_SHOWN
            and
            engine.ENGINE_SUBPROCESS
            and
            engine.ENGINE_SUBPROCESS.returncode is None
        ):
            msg = _(
                "Unable to communicate with the engine over UDP sockets.  "
                "Please ensure that UDP sockets on localhost are enabled "
                "in your firewall for the entire application, or for "
                "the following UDP ports:\n"
                f"{IPC_UI_SERVER_PORT}\n{IPC_ENGINE_SERVER_PORT}"
            )
            LOG.error(msg)
            SOCKET_ERROR_SHOWN = True
            QMessageBox.warning(
                shared.MAIN_WINDOW,
                _("Error"),
                msg,
            )
        LOG.error(f"Failed to send {message[:100]}")

