import sys
from PyQt5.QtWidgets import QApplication, QDialog
from PyQt5.QtNetwork import QHostAddress, QTcpServer

class IPCServer(QDialog):
    def __init__(self):
        super().__init__()
        self.tcpServer = None

    def sessionOpened(self):
        self.tcpServer = QTcpServer(self)
        PORT = 9999
        address = QHostAddress('127.0.0.1')
        if not self.tcpServer.listen(address, PORT):
            QMessageBox.error(
                self,
                "Error",
                f"Unable to listen on port {PORT}",
            )
            self.close()
            exit(1)
        self.tcpServer.newConnection.connect(self._communicate)

    def _communicate(self):
        clientConnection = self.tcpServer.nextPendingConnection()
        clientConnection.waitForReadyRead()
        instr = clientConnection.readAll()
        data = str(instr, encoding='ascii')
        print(data.split('\x00', 1)[0])
        clientConnection.disconnected.connect(clientConnection.deleteLater)
        clientConnection.disconnectFromHost()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    server = IPCServer()
    server.sessionOpened()
    sys.exit(server.exec())
