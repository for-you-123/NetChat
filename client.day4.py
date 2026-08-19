import socket
HOST = "127.0.0.1"
PORT = 5000
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print("正在连接服务器...")
client_socket.connect((HOST, PORT))
print("连接服务器成功")
client_socket.sendall(b"Hello")
print("已发送：Hello")
client_socket.close()
print("客户端已关闭")