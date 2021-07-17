import argparse
import socket
import time


def ipc_send(
    path,
    key,
    value,
    ip='127.0.0.1',
    port=9999,
    buffer_size=8192,
):
    message = "\n".join([path, key, value])
    assert len(message) < 8192, (len(message), message)
    message = message.encode('ascii')
    for wait in (0.1, 0.3, 0.6):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ip, port))
            s.sendall(message)
            s.close()
            return
        except ConnectionRefusedError:
            print("Connection refused: ")
            time.sleep(wait)
    print(f"Failed to send {message}")

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'path',
    )
    parser.add_argument(
        'key',
    )
    parser.add_argument(
        'value',
    )
    return parser.parse_args()

if __name__ == '__main__':
    import time
    args = parse_args()
    while True:
        print("Sending...")
        ipc_send(**args.__dict__)
        time.sleep(1)

