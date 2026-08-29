import socket
import threading
import tkinter as tk
from tkinter import messagebox
HOST = "127.0.0.1"
PORT = 5000
client_socket = None
username = ""
login_window = tk.Tk()
login_window.title("登录聊天室")
login_window.geometry("300x180")
login_window.resizable(False, False)
title_label = tk.Label(
    login_window,
    text="Python ChatRoom",
    font=("Arial", 16)
)
title_label.pack(
    pady=15
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
    username = username_entry.get().strip()
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
        client_socket.send(
            username.encode("utf-8")
        )
    except ConnectionRefusedError:
        messagebox.showerror(
            "连接失败",
            "服务器未启动"
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
    pady=15
)
username_entry.bind(
    "<Return>",
    lambda event: login()
)
def open_chat_window():
    global chat_window
    global chat_text
    global message_entry
    chat_window = tk.Tk()
    chat_window.title(
        f"Python ChatRoom - {username}"
    )
    chat_window.geometry(
        "600x450"
    )
    chat_text = tk.Text(
        chat_window,
        state="disabled",
        wrap="word"
    )
    chat_text.pack(
        fill="both",
        expand=True,
        padx=10,
        pady=10
    )
    bottom_frame = tk.Frame(
        chat_window
    )
    bottom_frame.pack(
        fill="x",
        padx=10,
        pady=5
    )
    message_entry = tk.Entry(
        bottom_frame
    )
    message_entry.pack(
        side="left",
        fill="x",
        expand=True
    )
    send_button = tk.Button(
        bottom_frame,
        text="发送",
        command=send_message
    )
    send_button.pack(
        side="right",
        padx=(5, 0)
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
def send_message():
    message = message_entry.get().strip()
    if not message:
        return
    try:
        client_socket.send(
            message.encode("utf-8")
        )
        display_message(
            f"我：{message}"
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
def receive_messages():
    while True:
        try:
            data = client_socket.recv(
                1024
            )
            if not data:
                break
            message = data.decode(
                "utf-8"
            )
            chat_window.after(
                0,
                display_message,
                message
            )
        except ConnectionResetError:
            break
        except OSError:
            break
        except Exception as e:
            print(
                "接收失败：",
                e
            )
            break
def close_chat():
    try:
        client_socket.send(
            "quit".encode("utf-8")
        )
    except:
        pass
    try:
        client_socket.close()
    except:
        pass
    chat_window.destroy()
login_window.mainloop()