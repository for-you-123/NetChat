import tkinter as tk
from datetime import datetime
def send_message():
    message = message_entry.get()
    if message.strip() == "":
        return
    current_time = datetime.now().strftime("%H:%M")
    chat_text.config(state="normal")
    chat_text.insert(
        "end",
        f"[{current_time}] 我：{message}\n"
    )
    chat_text.config(state="disabled")
    message_entry.delete(0, "end")
def send_by_enter(event):
    send_message()
root = tk.Tk()
root.title("Python 聊天室")
root.geometry("700x500")
title_label = tk.Label(
    root,
    text="Python 聊天室",
    font=("Arial", 18)
)
title_label.pack(pady=10)
main_frame = tk.Frame(root)
main_frame.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=10
)
chat_frame = tk.Frame(
    main_frame,
    bd=1,
    relief="solid"
)
chat_frame.pack(
    side="left",
    fill="both",
    expand=True,
    padx=(0, 10)
)
scrollbar = tk.Scrollbar(chat_frame)
scrollbar.pack(
    side="right",
    fill="y"
)
chat_text = tk.Text(
    chat_frame,
    state="disabled",
    yscrollcommand=scrollbar.set
)
chat_text.pack(
    side="left",
    fill="both",
    expand=True
)
scrollbar.config(
    command=chat_text.yview
)
user_frame = tk.Frame(
    main_frame,
    width=150,
    bd=1,
    relief="solid"
)
user_frame.pack(
    side="right",
    fill="y"
)
user_label = tk.Label(
    user_frame,
    text="在线用户",
    font=("Arial", 12)
)
user_label.pack(pady=10)

user_list = tk.Listbox(
    user_frame,
    width=15
)
user_list.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=(0, 10)
)
user_list.insert("end", "张三")
user_list.insert("end", "李四")
user_list.insert("end", "王五")
input_frame = tk.Frame(root)
input_frame.pack(
    fill="x",
    padx=10,
    pady=(0, 10)
)
message_entry = tk.Entry(
    input_frame
)
message_entry.pack(
    side="left",
    fill="x",
    expand=True,
    padx=(0, 10)
)
message_entry.bind(
    "<Return>",
    send_by_enter
)
send_button = tk.Button(
    input_frame,
    text="发送",
    command=send_message
)
send_button.pack(
    side="right"
)
root.mainloop()