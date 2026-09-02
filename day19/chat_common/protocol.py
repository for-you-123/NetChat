import json
from chat_common.config import SOCKET_RECV_SIZE
def encode_message(data):
    text = json.dumps(
        data,
        ensure_ascii=False
    )
    return (
        text + "\n"
    ).encode("utf-8")
def send_json(sock, data):
    packet = encode_message(data)
    sock.sendall(packet)
def receive_json(sock, buffer):
    while b"\n" not in buffer:
        chunk = sock.recv(
            SOCKET_RECV_SIZE
        )
        if not chunk:
            return None, buffer
        buffer += chunk
    line, buffer = buffer.split(
        b"\n",
        1
    )
    if not line:
        return {}, buffer
    text = line.decode(
        "utf-8"
    )
    message = json.loads(
        text
    )
    return message, buffer