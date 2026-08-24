import socket
import threading
HOST = "127.0.0.1"
PORT = 5000
clients = []
server_socket = socket.socket(
    socket.AF_INET,
    socket.SOCK_STREAM
)
server_socket.bind((HOST, PORT))
server_socket.listen()
print(f"服务器启动：{HOST}:{PORT}")
def handle_client(conn, addr):
    print(f"开始处理客户端：{addr}")
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                print(f"客户端 {addr} 已断开")
                break
            message = data.decode("utf-8")
            print(f"{addr}：{message}")
            if message == "quit":
                print(f"客户端 {addr} 请求退出")
                break
            reply = f"服务器收到：{message}"
            conn.send(
                reply.encode("utf-8")
            )
    except ConnectionResetError:
        print(f"客户端 {addr} 异常断开")
    except Exception as e:
        print(f"客户端 {addr} 出现异常：{e}")
    finally:
        if conn in clients:
            clients.remove(conn)
        conn.close()
        print(f"客户端 {addr} 已移除")
        print(f"当前连接数：{len(clients)}")
while True:
    conn, addr = server_socket.accept()
    clients.append(conn)
    print(f"新客户端连接：{addr}")
    print(f"当前连接数：{len(clients)}")
    client_thread = threading.Thread(
        target=handle_client,
        args=(conn, addr)
    )
    client_thread.start()