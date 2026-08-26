import socket
import tkinter as tk
from tkinter import messagebox
HOST = "127.0.0.1"
PORT = 5000
client_socket = socket.socket(
    socket.AF_INET,
    socket.SOCK_STREAM
)
try:
    client_socket.connect((HOST, PORT))
except ConnectionRefusedError:
    print("服务器未启动")
    exit()
root = tk.Tk()
root.title("Python ChatRoom")
root.geometry("500x400")
chat_text = tk.Text(
    root,
    state="disabled"
)
chat_text.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=10
)
message_entry = tk.Entry(root)
message_entry.pack(
    fill="x",
    padx=10,
    pady=5
)
def send_message():
    message = message_entry.get()
    if not message.strip():
        return
    try:
        client_socket.send(
            message.encode("utf-8")
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
send_button = tk.Button(
    root,
    text="发送",
    command=send_message
)
send_button.pack(
    pady=5
)
message_entry.bind(
    "<Return>",
    lambda event: send_message()
)
root.mainloop()