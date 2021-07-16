from sglib.ipc.abstract import AbstractIPCTransport
from sglib.log import LOG

class NullIPCTransport(AbstractIPCTransport):
    def send(
        self,
        path,
        key,
        value,
    ):
        LOG.info(
            "Engine not running.  Would have sent RPC call: "
            f'path: "{path}", key: "{key}", value: "{value}"'
        )

