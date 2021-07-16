from sglib.ipc.abstract import AbstractIPCTransport
from sglib.lib.enginelib import engine_lib_configure
#import stargateengine

class EngineLibIPCTransport(AbstractIPCTransport):
    def send(
        self,
        path,
        key,
        value,
    ):
        #stargateengine.configure(
        engine_lib_configure(
            path,
            key,
            value,
        )

