import socket
import threading
import json
from database import (
    init_database,
    save_message,
    load_messages
)
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
        except Exception as e:
            print(
                f"向 {username} 发送失败：",
                e
            )

def broadcast_user_list():
    data = {
        "type": "user_list",
        "users": list(users.keys())
    }
    for username, conn in list(
        users.items()
    ):
        try:
            send_json(
                conn,
                data
            )
        except Exception as e:
            print(
                f"向 {username} 发送用户列表失败：",
                e
            )

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
        if username in users:
            send_json(
                conn,
                {
                    "type": "error",
                    "content": "昵称已经被使用"
                }
            )
            return
        users[username] = conn
        print(
            f"{username} 已上线：{addr}"
        )
        broadcast(
            {
                "type": "system",
                "content": f"{username} 加入聊天室"
            },
            sender=conn
        )
        broadcast_user_list()
        while True:
            raw = conn.recv(1024)
            if not raw:
                print(
                    f"{username} 已断开"
                )
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
                    send_json(
                        conn,
                        {
                            "type": "error",
                            "content": "消息不能为空"
                        }
                    )
                    continue
                save_message(
                    username=username,
                    content=content,
                    message_type="message",
                    target=None
                )
                broadcast(
                    {
                        "type": "message",
                        "username": username,
                        "content": content
                    },
                    sender=conn
                )
                print(
                    f"[群聊] {username}: {content}"
                )
            elif msg_type == "private":
                target = (
                    message
                    .get("target", "")
                    .strip()
                )
                content = (
                    message
                    .get("content", "")
                    .strip()
                )
                if not target:
                    send_json(
                        conn,
                        {
                            "type": "error",
                            "content": "缺少私聊目标"
                        }
                    )
                    continue
                if not content:
                    send_json(
                        conn,
                        {
                            "type": "error",
                            "content": "私聊消息不能为空"
                        }
                    )
                    continue
                if target == username:
                    send_json(
                        conn,
                        {
                            "type": "error",
                            "content": "不能私聊自己"
                        }
                    )
                    continue
                target_conn = users.get(
                    target
                )
                if target_conn is None:
                    send_json(
                        conn,
                        {
                            "type": "error",
                            "content": f"{target} 当前不在线"
                        }
                    )
                    continue
                save_message(
                    username=username,
                    content=content,
                    message_type="private",
                    target=target
                )
                private_message = {
                    "type": "private",
                    "from": username,
                    "to": target,
                    "content": content
                }
                send_json(
                    target_conn,
                    private_message
                )
                send_json(
                    conn,
                    private_message
                )
                print(
                    f"[私聊] {username} -> {target}: {content}"
                )
            elif msg_type == "quit":
                print(
                    f"{username} 请求退出"
                )
                break
            else:
                send_json(
                    conn,
                    {
                        "type": "error",
                        "content": f"未知消息类型：{msg_type}"
                    }
                )
    except json.JSONDecodeError:
        print(
            f"{username or addr} 发送了非法 JSON"
        )
        try:
            send_json(
                conn,
                {
                    "type": "error",
                    "content": "JSON 格式错误"
                }
            )
        except:
            pass
    except ConnectionResetError:
        print(
            f"{username or addr} 异常断开连接"
        )
    except Exception as e:
        print(
            f"处理客户端 {username or addr} 时发生异常：",
            e
        )
    finally:
        if (
            username
            and username in users
            and users[username] == conn
        ):
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
        print(
            f"客户端连接结束：{addr}"
        )

def print_history():
    rows = load_messages()
    print()
    print("=" * 60)
    print("历史聊天记录")
    print("=" * 60)
    if not rows:
        print("暂无历史记录")
    else:
        for row in rows:
            (
                message_id,
                username,
                content,
                message_type,
                target,
                created_at
            ) = row
            if message_type == "message":
                print(
                    f"[{created_at}] "
                    f"[群聊] "
                    f"{username}: {content}"
                )
            elif message_type == "private":
                print(
                    f"[{created_at}] "
                    f"[私聊] "
                    f"{username} -> {target}: "
                    f"{content}"
                )
    print("=" * 60)
    print()

def main():
    init_database()
    print_history()
    server_socket = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )
    server_socket.bind(
        (HOST, PORT)
    )
    server_socket.listen()
    print(
        f"服务器启动成功：{HOST}:{PORT}"
    )
    print(
        "正在等待客户端连接..."
    )
    try:
        while True:
            conn, addr = (
                server_socket.accept()
            )
            print(
                f"新的客户端连接：{addr}"
            )
            thread = threading.Thread(
                target=handle_client,
                args=(conn, addr),
                daemon=True
            )
            thread.start()
    except KeyboardInterrupt:
        print()
        print("服务器正在关闭...")
    finally:
        server_socket.close()
        print("服务器已关闭")

if __name__ == "__main__":
    main()
