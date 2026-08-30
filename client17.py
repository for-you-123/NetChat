import socket
import threading
import json
import tkinter as tk
from tkinter import messagebox
HOST = "127.0.0.1"
PORT = 5000
client_socket = None
username = ""

def send_json(data):
    text = json.dumps(
        data,
        ensure_ascii=False
    )
    client_socket.send(
        text.encode("utf-8")
    )

login_window = tk.Tk()
login_window.title(
    "登录聊天室"
)
login_window.geometry(
    "320x200"
)
login_window.resizable(
    False,
    False
)
title_label = tk.Label(
    login_window,
    text="Python ChatRoom",
    font=("Arial", 16)
)
title_label.pack(
    pady=20
)
username_entry = tk.Entry(
    login_window,
    font=("Arial", 12)
)
username_entry.pack(
    padx=30,
    fill="x"
)

def login():
    global client_socket
    global username
    username = (
        username_entry
        .get()
        .strip()
    )
    if not username:
        messagebox.showwarning(
            "提示",
            "昵称不能为空"
        )
        return
    try:
        client_socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )
        client_socket.connect(
            (HOST, PORT)
        )
        send_json(
            {
                "type": "login",
                "username": username
            }
        )
    except ConnectionRefusedError:
        messagebox.showerror(
            "连接失败",
            "服务器可能没有启动"
        )
        return
    except Exception as e:
        messagebox.showerror(
            "连接失败",
            str(e)
        )
        return
    login_window.destroy()
    open_chat_window()

login_button = tk.Button(
    login_window,
    text="进入聊天室",
    command=login
)
login_button.pack(
    pady=20
)
username_entry.bind(
    "<Return>",
    lambda event: login()
)

def open_chat_window():
    global chat_window
    global chat_text
    global message_entry
    global user_listbox
    chat_window = tk.Tk()
    chat_window.title(
        f"Python ChatRoom - {username}"
    )
    chat_window.geometry(
        "720x500"
    )
    content_frame = tk.Frame(
        chat_window
    )
    content_frame.pack(
        fill="both",
        expand=True,
        padx=10,
        pady=10
    )
    chat_text = tk.Text(
        content_frame,
        state="disabled",
        wrap="word"
    )
    chat_text.pack(
        side="left",
        fill="both",
        expand=True
    )
    user_frame = tk.Frame(
        content_frame,
        width=160
    )
    user_frame.pack(
        side="right",
        fill="y",
        padx=(10, 0)
    )
    user_label = tk.Label(
        user_frame,
        text="在线用户",
        font=("Arial", 11, "bold")
    )
    user_label.pack(
        pady=(0, 5)
    )
    user_listbox = tk.Listbox(
        user_frame
    )
    user_listbox.pack(
        fill="both",
        expand=True
    )
    bottom_frame = tk.Frame(
        chat_window
    )
    bottom_frame.pack(
        fill="x",
        padx=10,
        pady=(0, 10)
    )
    message_entry = tk.Entry(
        bottom_frame,
        font=("Arial", 11)
    )
    message_entry.pack(
        side="left",
        fill="x",
        expand=True
    )
    private_button = tk.Button(
        bottom_frame,
        text="私聊",
        command=send_private_message
    )
    private_button.pack(
        side="right",
        padx=5
    )
    send_button = tk.Button(
        bottom_frame,
        text="群发",
        command=send_message
    )
    send_button.pack(
        side="right"
    )
    message_entry.bind(
        "<Return>",
        lambda event: send_message()
    )
    chat_window.protocol(
        "WM_DELETE_WINDOW",
        close_chat
    )
    receive_thread = threading.Thread(
        target=receive_messages,
        daemon=True
    )
    receive_thread.start()
    message_entry.focus()
    chat_window.mainloop()

def display_message(message):
    chat_text.config(
        state="normal"
    )
    chat_text.insert(
        tk.END,
        message + "\n"
    )
    chat_text.config(
        state="disabled"
    )
    chat_text.see(
        tk.END
    )

def update_user_list(usernames):
    user_listbox.delete(
        0,
        tk.END
    )
    for name in usernames:
        user_listbox.insert(
            tk.END,
            name
        )

def send_message():
    content = (
        message_entry
        .get()
        .strip()
    )
    if not content:
        return
    try:
        send_json(
            {
                "type": "message",
                "content": content
            }
        )
        display_message(
            f"我: {content}"
        )
        message_entry.delete(
            0,
            tk.END
        )
    except Exception as e:
        messagebox.showerror(
            "发送失败",
            str(e)
        )

def send_private_message():
    selection = (
        user_listbox
        .curselection()
    )
    if not selection:
        messagebox.showwarning(
            "提示",
            "请先选择一个在线用户"
        )
        return
    target = user_listbox.get(
        selection[0]
    )
    if target == username:
        messagebox.showwarning(
            "提示",
            "不能私聊自己"
        )
        return
    content = (
        message_entry
        .get()
        .strip()
    )
    if not content:
        return
    try:
        send_json(
            {
                "type": "private",
                "target": target,
                "content": content
            }
        )
        message_entry.delete(
            0,
            tk.END
        )
    except Exception as e:
        messagebox.showerror(
            "私聊发送失败",
            str(e)
        )

def receive_messages():
    while True:
        try:
            raw = client_socket.recv(
                1024
            )
            if not raw:
                break
            message = json.loads(
                raw.decode("utf-8")
            )
            msg_type = message.get(
                "type"
            )
            if msg_type == "message":
                sender = message.get(
                    "username",
                    ""
                )
                content = message.get(
                    "content",
                    ""
                )
                text = (
                    f"{sender}: {content}"
                )
                chat_window.after(
                    0,
                    display_message,
                    text
                )
            elif msg_type == "system":
                content = message.get(
                    "content",
                    ""
                )
                chat_window.after(
                    0,
                    display_message,
                    f"[系统] {content}"
                )
            elif msg_type == "user_list":
                usernames = message.get(
                    "users",
                    []
                )
                chat_window.after(
                    0,
                    update_user_list,
                    usernames
                )
            elif msg_type == "private":
                sender = message.get(
                    "from",
                    ""
                )
                target = message.get(
                    "to",
                    ""
                )
                content = message.get(
                    "content",
                    ""
                )
                if sender == username:
                    text = (
                        f"[私聊] 我 -> "
                        f"{target}: {content}"
                    )
                else:
                    text = (
                        f"[私聊] {sender} -> "
                        f"我: {content}"
                    )
                chat_window.after(
                    0,
                    display_message,
                    text
                )
            elif msg_type == "error":
                content = message.get(
                    "content",
                    "未知错误"
                )
                chat_window.after(
                    0,
                    show_error,
                    content
                )
        except json.JSONDecodeError:
            print(
                "收到非法 JSON"
            )
        except ConnectionResetError:
            print(
                "服务器连接已断开"
            )
            break
        except OSError:
            break
        except Exception as e:
            print(
                "接收消息失败：",
                e
            )
            break

def show_error(content):
    messagebox.showerror(
        "服务器错误",
        content
    )

def close_chat():
    try:
        send_json(
            {
                "type": "quit"
            }
        )
    except:
        pass
    try:
        client_socket.close()
    except:
        pass
    chat_window.destroy()

login_window.mainloop()
