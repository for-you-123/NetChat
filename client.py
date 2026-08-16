import socket
client = socket.socket(
    socket.AF_INET,
    socket.SOCK_STREAM
)
HOST = "127.0.0.1"
PORT = 8888
client.connect((HOST, PORT))
print("已经连接到服务器")
message = "Hello"
client.send(
    message.encode("utf-8")
)
print("消息已发送：", message)
client.close()