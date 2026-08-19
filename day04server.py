import socket
HOST = "127.0.0.1"
PORT = 5000
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen()
print(f"服务器已启动：{HOST}:{PORT}")
print("正在等待客户端连接...")
conn, addr = server_socket.accept()
print("客户端已连接：", addr)
data = conn.recv(1024)
print("收到的数据：", data)
print("收到的消息：", data.decode("utf-8"))
conn.close()
server_socket.close()
print("服务器已关闭")