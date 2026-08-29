import socket
import threading
import json
HOST = "127.0.0.1"
PORT = 5000
users = {}
def send_json(conn, data):
    text = json.dumps(
        data,
        ensure_ascii=False
    )
    conn.send(
        text.encode("utf-8")
    )
def broadcast(data, sender=None):
    for username, conn in list(
        users.items()
    ):
        if conn == sender:
            continue
        try:
            send_json(
                conn,
                data
            )
        except:
            pass
def broadcast_user_list():
    data = {
        "type": "user_list",
        "users": list(users.keys())
    }
    for conn in list(
        users.values()
    ):
        try:
            send_json(
                conn,
                data
            )
        except:
            pass
def handle_client(conn, addr):
    username = ""
    try:
        raw = conn.recv(1024)
        if not raw:
            return
        login_message = json.loads(
            raw.decode("utf-8")
        )
        if login_message.get("type") != "login":
            send_json(
                conn,
                {
                    "type": "error",
                    "content": "第一条消息必须是 login"
                }
            )
            return
        username = (
            login_message
            .get("username", "")
            .strip()
        )
        if not username:
            send_json(
                conn,
                {
                    "type": "error",
                    "content": "昵称不能为空"
                }
            )
            return
        users[username] = conn
        broadcast(
            {
                "type": "system",
                "content": f"{username} 加入聊天室"
            },
            conn
        )
        broadcast_user_list()
        while True:
            raw = conn.recv(1024)
            if not raw:
                break
            message = json.loads(
                raw.decode("utf-8")
            )
            msg_type = message.get(
                "type"
            )
            if msg_type == "message":
                content = (
                    message
                    .get("content", "")
                    .strip()
                )
                if not content:
                    continue
                broadcast(
                    {
                        "type": "message",
                        "username": username,
                        "content": content
                    },
                    conn
                )
            elif msg_type == "quit":
                break
            else:
                send_json(
                    conn,
                    {
                        "type": "error",
                        "content": "未知消息类型"
                    }
                )
    except ConnectionResetError:
        pass
    except json.JSONDecodeError:
        try:
            send_json(
                conn,
                {
                    "type": "error",
                    "content": "JSON格式错误"
                }
            )
        except:
            pass
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
            broadcast(
                {
                    "type": "system",
                    "content": f"{username} 退出聊天室"
                }
            )
            broadcast_user_list()