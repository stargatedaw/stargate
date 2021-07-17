import sys
from PyQt5.QtCore import QByteArray
from PyQt5.QtWidgets import QApplication, QDialog
from PyQt5.QtNetwork import (
    QHostAddress,
    QNetworkDatagram,
    QUdpSocket,
)

class IPCServer(QDialog):
    def __init__(self):
        super().__init__()
        self.udp_server = None

    def sessionOpened(self):
        PORT = 9999
        self.udp_server = QUdpSocket(self)
        self.udp_server.bind(QHostAddress.LocalHost, PORT)
        self.udp_server.readyRead.connect(self._communicate)

    def _communicate(self):
        while self.udp_server.hasPendingDatagrams():
            dgram = self.udp_server.receiveDatagram()
            data = dgram.data()
            data = str(data, encoding='ascii')
            print(data.split('\x00', 1)[0])
            self.udp_server.writeDatagram(
                QNetworkDatagram(
                    QByteArray(b"Processed request"),
                ),
            )

if __name__ == '__main__':
    app = QApplication(sys.argv)
    server = IPCServer()
    server.sessionOpened()
    sys.exit(server.exec())
