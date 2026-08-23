import socket
import threading
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
            conn.send(reply.encode("utf-8"))
    except ConnectionResetError:
        print(f"客户端 {addr} 异常断开")
    except Exception as e:
        print(f"处理客户端 {addr} 时发生异常：{e}")
    finally:
        conn.close()
        print(f"客户端 {addr} 的连接已关闭")
while True:
    conn, addr = server_socket.accept()
    print(f"新的客户端连接：{addr}")
    client_thread = threading.Thread(
        target=handle_client,
        args=(conn, addr)
    )
    client_thread.start()