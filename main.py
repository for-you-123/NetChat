import tkinter as tk
def enter_chatroom():
    nickname = nickname_entry.get()
    print("你输入的昵称是：", nickname)
root = tk.Tk()
root.title("Python 聊天室")
root.geometry("400x250")
title_label = tk.Label(
    root,
    text="欢迎使用 Python 聊天室",
    font=("Arial", 18)
)
title_label.pack(pady=30)
nickname_frame = tk.Frame(root)
nickname_frame.pack(pady=10)
nickname_label = tk.Label(
    nickname_frame,
    text="昵称："
)
nickname_label.pack(side="left")
nickname_entry = tk.Entry(
    nickname_frame,
    width=20
)
nickname_entry.pack(side="left")
entry_button = tk.Button(
    root,
    text = "进入聊天室",
    command=enter_chatroom
)
entry_button.pack(pady=15)
status_label = tk.Label(
    root,
    text = ""
)
status_label.pack()
root.mainloop()