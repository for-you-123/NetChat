import socket
import threading
HOST = "127.0.0.1"
PORT = 5000
users = {}
server_socket = socket.socket(
    socket.AF_INET,
    socket.SOCK_STREAM
)
server_socket.bind(
    (HOST, PORT)
)
server_socket.listen()
print(
    f"服务器启动：{HOST}:{PORT}"
)
def broadcast(message, sender=None):
    for username, conn in list(users.items()):
        if conn == sender:
            continue
        try:
            conn.send(
                message.encode("utf-8")
            )
        except:
            pass
def broadcast_user_list():
    usernames = list(
        users.keys()
    )
    message = (
        "USER_LIST|"
        + ",".join(usernames)
    )
    for conn in list(
        users.values()
    ):
        try:
            conn.send(
                message.encode("utf-8")
            )
        except:
            pass
def handle_client(conn, addr):
    username = ""
    try:
        name_data = conn.recv(1024)
        if not name_data:
            return
        username = name_data.decode(
            "utf-8"
        )
        users[username] = conn
        print(
            f"{username} 上线"
        )
        broadcast(
            f"{username} 加入聊天室",
            conn
        )
        broadcast_user_list()
        while True:
            data = conn.recv(1024)
            if not data:
                break
            message = data.decode(
                "utf-8"
            )
            if message == "quit":
                break
            broadcast(
                f"{username}:{message}",
                conn
            )
    except ConnectionResetError:
        print(
            f"{username} 异常断开"
        )
    except Exception as e:
        print(
            "客户端异常：",
            e
        )
    finally:
        if username in users:
            del users[username]
        try:
            conn.close()
        except:
            pass
        if username:
            print(
                f"{username} 下线"
            )
            broadcast(
                f"{username} 退出聊天室"
            )
            broadcast_user_list()
while True:
    conn, addr = (
        server_socket.accept()
    )
    thread = threading.Thread(
        target=handle_client,
        args=(conn, addr),
        daemon=True
    )
    thread.start()