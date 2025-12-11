import json
import socket

def send_message(sock: socket.socket, obj: dict):
    data = json.dumps(obj).encode("utf-8")
    size = len(data).to_bytes(4, "big")
    sock.sendall(size + data)


def recv_message(sock: socket.socket):
    size_bytes = sock.recv(4)
    if not size_bytes:
        return None

    size = int.from_bytes(size_bytes, "big")
    data = sock.recv(size)
    return json.loads(data.decode("utf-8"))