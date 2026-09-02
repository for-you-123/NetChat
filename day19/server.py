import json
import socket
import sqlite3
import threading

from chat_common.config import (
    HOST,
    PORT,
    MAX_MESSAGE_LENGTH
)

from chat_common.protocol import (
    send_json,
    receive_json
)

from server_modules.database import (
    init_database,
    save_message,
    load_messages
)

from server_modules.client_manager import (
    ClientManager
)


# ==========================================
# 在线用户管理器
# ==========================================

client_manager = ClientManager()


# ==========================================
# Socket 发送锁
# ==========================================

send_lock = threading.Lock()


def safe_send(conn, data):
    """
    Server 统一发送入口。

    多个客户端线程可能同时发送数据，
    所以这里使用 Lock 保护发送操作。
    """

    with send_lock:

        send_json(
            conn,
            data
        )


def send_error(
    conn,
    code,
    content
):
    """
    统一发送错误消息。
    """

    try:

        safe_send(
            conn,
            {
                "type": "error",
                "code": code,
                "content": content
            }
        )

    except OSError:

        pass


# ==========================================
# 广播
# ==========================================

def broadcast(
    data,
    sender=None
):
    """
    广播消息给所有在线客户端。

    sender:
        如果传入发送者 Socket，
        则跳过该 Socket。
    """

    connections = (
        client_manager
        .get_connections()
    )


    for username, conn in connections:

        if conn == sender:

            continue


        try:

            safe_send(
                conn,
                data
            )

        except OSError:

            print(
                f"[WARN] "
                f"发送给 {username} 失败"
            )


# ==========================================
# 在线用户列表
# ==========================================

def broadcast_user_list():
    """
    把当前在线用户列表
    广播给全部客户端。
    """

    usernames = (
        client_manager
        .get_usernames()
    )


    broadcast(
        {
            "type": "user_list",
            "users": usernames
        }
    )


# ==========================================
# 消息内容校验
# ==========================================

def validate_content(content):
    """
    验证聊天内容。

    返回：

        True, content

    或：

        False, error_message
    """

    if not isinstance(
        content,
        str
    ):

        return (
            False,
            "消息内容必须是字符串"
        )


    content = content.strip()


    if not content:

        return (
            False,
            "消息不能为空"
        )


    if (
        len(content)
        > MAX_MESSAGE_LENGTH
    ):

        return (
            False,
            f"消息不能超过 "
            f"{MAX_MESSAGE_LENGTH} 个字符"
        )


    return (
        True,
        content
    )


# ==========================================
# 群聊处理
# ==========================================

def handle_public_message(
    username,
    conn,
    message
):
    """
    处理普通群聊消息。
    """

    success, result = (
        validate_content(
            message.get(
                "content"
            )
        )
    )


    if not success:

        send_error(
            conn,
            "INVALID_MESSAGE",
            result
        )

        return


    content = result


    # ======================================
    # 先写数据库
    # ======================================

    try:

        created_at = save_message(
            username=username,
            content=content,
            message_type="message",
            target=None
        )

    except sqlite3.Error as e:

        print(
            "[ERROR] "
            "数据库保存失败：",
            e
        )


        send_error(
            conn,
            "DATABASE_ERROR",
            "消息保存失败，请稍后重试"
        )

        return


    # ======================================
    # 发给其他用户
    # ======================================

    broadcast(
        {
            "type": "message",
            "username": username,
            "content": content,
            "time": created_at
        },
        sender=conn
    )


    # ======================================
    # 回执给发送者
    # ======================================

    try:

        safe_send(
            conn,
            {
                "type": "message_sent",
                "content": content,
                "time": created_at
            }
        )

    except OSError:

        return


    print(
        f"[群聊] "
        f"{username}: "
        f"{content}"
    )


# ==========================================
# 私聊处理
# ==========================================

def handle_private_message(
    username,
    conn,
    message
):
    """
    处理 private 消息。
    """

    target = message.get(
        "target",
        ""
    )


    if not isinstance(
        target,
        str
    ):

        send_error(
            conn,
            "INVALID_TARGET",
            "私聊目标格式错误"
        )

        return


    target = target.strip()


    if not target:

        send_error(
            conn,
            "EMPTY_TARGET",
            "请选择私聊用户"
        )

        return


    if target == username:

        send_error(
            conn,
            "SELF_PRIVATE_MESSAGE",
            "不能私聊自己"
        )

        return


    # ======================================
    # 验证消息正文
    # ======================================

    success, result = (
        validate_content(
            message.get(
                "content"
            )
        )
    )


    if not success:

        send_error(
            conn,
            "INVALID_MESSAGE",
            result
        )

        return


    content = result


    # ======================================
    # 根据 username 找目标 Socket
    # ======================================

    target_conn = (
        client_manager
        .get_user(target)
    )


    if target_conn is None:

        send_error(
            conn,
            "USER_OFFLINE",
            f"{target} 当前不在线"
        )

        return


    # ======================================
    # 保存私聊记录
    # ======================================

    try:

        created_at = save_message(
            username=username,
            content=content,
            message_type="private",
            target=target
        )

    except sqlite3.Error as e:

        print(
            "[ERROR] "
            "私聊保存失败：",
            e
        )


        send_error(
            conn,
            "DATABASE_ERROR",
            "私聊消息保存失败"
        )

        return


    private_message = {
        "type": "private",
        "from": username,
        "to": target,
        "content": content,
        "time": created_at
    }


    # ======================================
    # 发给目标用户
    # ======================================

    try:

        safe_send(
            target_conn,
            private_message
        )

    except OSError:

        send_error(
            conn,
            "USER_OFFLINE",
            f"{target} 当前无法接收消息"
        )

        return


    # ======================================
    # 回发给发送者
    # ======================================

    try:

        safe_send(
            conn,
            private_message
        )

    except OSError:

        return


    print(
        f"[私聊] "
        f"{username} -> "
        f"{target}: "
        f"{content}"
    )


# ==========================================
# 客户端清理
# ==========================================

def cleanup_client(
    username,
    conn
):
    """
    Client 断开以后统一清理。
    """

    removed = False


    if username:

        removed = (
            client_manager
            .remove_user(
                username,
                conn
            )
        )


    # ======================================
    # shutdown
    # ======================================

    try:

        conn.shutdown(
            socket.SHUT_RDWR
        )

    except OSError:

        pass


    # ======================================
    # close
    # ======================================

    try:

        conn.close()

    except OSError:

        pass


    # 如果用户根本没有成功登录，
    # 就没有必要广播退出
    if not removed:

        return


    print(
        f"[INFO] "
        f"{username} 已下线，"
        f"当前在线 "
        f"{client_manager.count()} 人"
    )


    # ======================================
    # 广播退出通知
    # ======================================

    broadcast(
        {
            "type": "system",
            "content":
                f"{username} 退出聊天室"
        }
    )


    # ======================================
    # 更新在线列表
    # ======================================

    broadcast_user_list()


# ==========================================
# 单客户端线程
# ==========================================

def handle_client(
    conn,
    addr
):
    """
    每一个 Client 都会由
    一个独立 Thread 执行这个函数。
    """

    username = ""

    buffer = b""


    print(
        f"[INFO] "
        f"收到新连接：{addr}"
    )


    try:

        # ==================================
        # 第一条消息必须是 login
        # ==================================

        try:

            login_message, buffer = (
                receive_json(
                    conn,
                    buffer
                )
            )


        except UnicodeDecodeError:

            send_error(
                conn,
                "INVALID_ENCODING",
                "登录消息必须使用 UTF-8"
            )

            return


        except json.JSONDecodeError:

            send_error(
                conn,
                "INVALID_JSON",
                "登录消息 JSON 格式错误"
            )

            return


        # Client连接后马上断开
        if login_message is None:

            return


        if not isinstance(
            login_message,
            dict
        ):

            return


        # ==================================
        # 检查 type
        # ==================================

        if (
            login_message.get("type")
            != "login"
        ):

            safe_send(
                conn,
                {
                    "type":
                        "login_result",

                    "success":
                        False,

                    "error":
                        "第一条消息必须是 login"
                }
            )

            return


        # ==================================
        # 获取 username
        # ==================================

        username = login_message.get(
            "username",
            ""
        )


        if not isinstance(
            username,
            str
        ):

            safe_send(
                conn,
                {
                    "type":
                        "login_result",

                    "success":
                        False,

                    "error":
                        "昵称格式错误"
                }
            )

            return


        username = username.strip()


        if not username:

            safe_send(
                conn,
                {
                    "type":
                        "login_result",

                    "success":
                        False,

                    "error":
                        "昵称不能为空"
                }
            )

            return


        # ==================================
        # 添加在线用户
        # ==================================

        success = (
            client_manager
            .add_user(
                username,
                conn
            )
        )


        # 重复昵称
        if not success:

            safe_send(
                conn,
                {
                    "type":
                        "login_result",

                    "success":
                        False,

                    "code":
                        "DUPLICATE_USERNAME",

                    "error":
                        "该昵称已经被使用"
                }
            )

            return


        # ==================================
        # 登录成功
        # ==================================

        safe_send(
            conn,
            {
                "type":
                    "login_result",

                "success":
                    True,

                "username":
                    username
            }
        )


        print(
            f"[INFO] "
            f"{username} 登录成功，"
            f"当前在线 "
            f"{client_manager.count()} 人"
        )


        # ==================================
        # 通知其他用户
        # ==================================

        broadcast(
            {
                "type": "system",
                "content":
                    f"{username} 加入聊天室"
            },
            sender=conn
        )


        # ==================================
        # 更新用户列表
        # ==================================

        broadcast_user_list()


        # ==================================
        # 主消息循环
        # ==================================

        while True:

            try:

                message, buffer = (
                    receive_json(
                        conn,
                        buffer
                    )
                )


            except UnicodeDecodeError:

                send_error(
                    conn,
                    "INVALID_ENCODING",
                    "消息必须使用 UTF-8"
                )

                continue


            except json.JSONDecodeError:

                send_error(
                    conn,
                    "INVALID_JSON",
                    "JSON 格式错误"
                )

                continue


            # ==================================
            # Client 关闭连接
            # ==================================

            if message is None:

                print(
                    f"[INFO] "
                    f"{username} "
                    f"连接已经关闭"
                )

                break


            if not message:

                continue


            if not isinstance(
                message,
                dict
            ):

                send_error(
                    conn,
                    "INVALID_MESSAGE",
                    "消息必须是 JSON 对象"
                )

                continue


            # ==================================
            # 根据 type 分发
            # ==================================

            msg_type = message.get(
                "type"
            )


            if msg_type == "message":

                handle_public_message(
                    username,
                    conn,
                    message
                )


            elif msg_type == "private":

                handle_private_message(
                    username,
                    conn,
                    message
                )


            elif msg_type == "quit":

                print(
                    f"[INFO] "
                    f"{username} 正常退出"
                )

                break


            else:

                send_error(
                    conn,
                    "UNKNOWN_MESSAGE_TYPE",
                    f"未知消息类型："
                    f"{msg_type}"
                )


    # ======================================
    # Client 强制关闭
    # ======================================

    except ConnectionResetError:

        print(
            f"[WARN] "
            f"{username or addr} "
            f"异常断开"
        )


    except BrokenPipeError:

        print(
            f"[WARN] "
            f"{username or addr} "
            f"连接损坏"
        )


    except OSError as e:

        print(
            f"[WARN] "
            f"{username or addr} "
            f"Socket 异常："
            f"{e}"
        )


    except Exception as e:

        print(
            f"[ERROR] "
            f"{username or addr} "
            f"发生未知异常："
            f"{e}"
        )


    finally:

        # 无论正常退出还是异常断开，
        # 最终都进入这里清理。

        cleanup_client(
            username,
            conn
        )


        print(
            f"[INFO] "
            f"客户端线程结束："
            f"{addr}"
        )


# ==========================================
# 打印历史记录
# ==========================================

def print_history():
    """
    Server 启动时读取 SQLite 历史记录。
    """

    try:

        rows = load_messages()

    except sqlite3.Error as e:

        print(
            "[ERROR] "
            "历史记录读取失败：",
            e
        )

        return


    print()

    print(
        "=" * 60
    )

    print(
        "历史聊天记录"
    )

    print(
        "=" * 60
    )


    if not rows:

        print(
            "暂无历史记录"
        )


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
                f"{username}: "
                f"{content}"
            )


        elif message_type == "private":

            print(
                f"[{created_at}] "
                f"[私聊] "
                f"{username} -> "
                f"{target}: "
                f"{content}"
            )


    print(
        "=" * 60
    )

    print()


# ==========================================
# Server 主函数
# ==========================================

def main():

    # ======================================
    # 初始化 SQLite
    # ======================================

    try:

        init_database()

    except sqlite3.Error as e:

        print(
            "[ERROR] "
            "数据库初始化失败：",
            e
        )

        return


    # ======================================
    # 打印历史记录
    # ======================================

    print_history()


    # ======================================
    # 创建 TCP Server Socket
    # ======================================

    server_socket = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )


    # Server关闭后马上重启，
    # 降低 Address already in use 的概率

    server_socket.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1
    )


    try:

        # ==================================
        # 绑定 IP / Port
        # ==================================

        server_socket.bind(
            (
                HOST,
                PORT
            )
        )


        # ==================================
        # 开始监听
        # ==================================

        server_socket.listen()


        print(
            f"ChatRoom Server "
            f"已启动："
            f"{HOST}:{PORT}"
        )


        print(
            "等待客户端连接..."
        )


        # ==================================
        # 持续 accept
        # ==================================

        while True:

            conn, addr = (
                server_socket.accept()
            )


            print(
                f"[INFO] "
                f"新客户端："
                f"{addr}"
            )


            # 每个 Client 一个 Thread

            thread = threading.Thread(
                target=handle_client,
                args=(
                    conn,
                    addr
                ),
                daemon=True
            )


            thread.start()


    except KeyboardInterrupt:

        print()

        print(
            "收到 Ctrl+C，"
            "Server 准备关闭..."
        )


    except OSError as e:

        print(
            "[ERROR] "
            "Server 运行异常：",
            e
        )


    finally:

        try:

            server_socket.close()

        except OSError:

            pass


        print(
            "Server 已关闭"
        )


# ==========================================
# Python 程序入口
# ==========================================

if __name__ == "__main__":

    main()