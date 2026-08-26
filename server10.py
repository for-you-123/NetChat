import socket
import threading
HOST="127.0.0.1"
PORT=5000
users={}
def broadcast(message,sender):
    for username,conn in list(users.items()):
        if conn != sender:
            try:
                conn.send(
                    message.encode("utf-8")
                )
            except:
                pass
def handle_client(conn,addr):
    username=""
    try:
        name_data=conn.recv(1024)
        username=name_data.decode(
            "utf-8"
        )
        users[username]=conn
        print(
            username,
            "上线"
        )
        broadcast(
            username+"加入聊天室",
            conn
        )
        while True:
            data=conn.recv(1024)
            if not data:
                break
            message=data.decode(
                "utf-8"
            )
            if message=="quit":
                break
            msg=f"{username}:{message}"
            broadcast(
                msg,
                conn
            )
    finally:
        if username in users:
            del users[username]
        conn.close()
        broadcast(
            username+"退出聊天室",
            conn
        )