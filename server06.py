import socket
HOST = "127.0.0.1"
PORT = 5000
server_socket = socket.socket(
    socket.AF_INET,
    socket.SOCK_STREAM
)
server_socket.bind((HOST, PORT))
server_socket.listen()
print(f"服务器启动：{HOST}:{PORT}")
print("等待客户端连接...")
conn = None
try:
    conn, addr = server_socket.accept()
    print("客户端已连接：", addr)
    while True:
        data = conn.recv(1024)
        if not data:
            print("客户端已断开连接")
            break
        message = data.decode("utf-8")
        print("客户端：", message)
        if message == "quit":
            print("客户端请求退出")
            break
        reply = input("服务器：")
        conn.send(reply.encode("utf-8"))
        if reply == "quit":
            print("服务器结束聊天")
            break
except ConnectionResetError:
    print("客户端异常断开连接")
except Exception as e:
    print("发生异常：", e)
finally:
    if conn:
        conn.close()
    server_socket.close()
    print("服务器已关闭")