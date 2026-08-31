import socket
import threading
import json
import tkinter as tk
from tkinter import messagebox
HOST="127.0.0.1"
PORT=5000
MAX_MESSAGE_LENGTH=500
client_socket=None
username=""
connected=False
receive_buffer=b""
def send_json(data):
    if client_socket is None:
        raise ConnectionError("尚未连接服务器")
    text=json.dumps(data,ensure_ascii=False)
    packet=(text+"\n").encode("utf-8")
    client_socket.sendall(packet)
def receive_json():
    global receive_buffer
    while b"\n" not in receive_buffer:
        chunk=client_socket.recv(4096)
        if not chunk:
            return None
        receive_buffer+=chunk
    line,receive_buffer=receive_buffer.split(b"\n",1)
    if not line:
        return {}
    text=line.decode("utf-8")
    return json.loads(text)
login_window=tk.Tk()
login_window.title("登录聊天室")
login_window.geometry("340x220")
login_window.resizable(False,False)
title_label=tk.Label(login_window,text="Python ChatRoom",font=("Arial",16))
title_label.pack(pady=20)
username_entry=tk.Entry(login_window,font=("Arial",12))
username_entry.pack(padx=30,fill="x")
login_button=None
def login():
    global client_socket
    global username
    global connected
    global receive_buffer
    username=username_entry.get().strip()
    if not username:
        messagebox.showwarning("提示","昵称不能为空")
        return
    login_button.config(state="disabled")
    try:
        client_socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        client_socket.settimeout(5)
        client_socket.connect((HOST,PORT))
        receive_buffer=b""
        send_json({"type":"login","username":username})
        response=receive_json()
        if response is None:
            raise ConnectionError("服务器已经断开")
        if response.get("type")!="login_result":
            raise ConnectionError("服务器登录响应异常")
        if not response.get("success",False):
            error=response.get("error","登录失败")
            messagebox.showerror("登录失败",error)
            client_socket.close()
            client_socket=None
            return
        client_socket.settimeout(None)
        connected=True
    except ConnectionRefusedError:
        messagebox.showerror("连接失败","无法连接服务器。\n请确认 server.py 是否已经启动。")
        cleanup_login_socket()
        return
    except socket.timeout:
        messagebox.showerror("连接超时","服务器长时间没有响应。")
        cleanup_login_socket()
        return
    except (ConnectionResetError,ConnectionError,OSError) as e:
        messagebox.showerror("连接失败",f"网络连接失败：{e}")
        cleanup_login_socket()
        return
    except (json.JSONDecodeError,UnicodeDecodeError):
        messagebox.showerror("登录失败","服务器返回了无法解析的数据。")
        cleanup_login_socket()
        return
    finally:
        try:
            login_button.config(state="normal")
        except tk.TclError:
            pass
    login_window.destroy()
    open_chat_window()
def cleanup_login_socket():
    global client_socket
    global connected
    connected=False
    if client_socket is not None:
        try:
            client_socket.close()
        except OSError:
            pass
    client_socket=None
login_button=tk.Button(login_window,text="进入聊天室",command=login)
login_button.pack(pady=20)
username_entry.bind("<Return>",lambda event:login())
username_entry.focus()
def open_chat_window():
    global chat_window
    global chat_text
    global message_entry
    global user_listbox
    global send_button
    global private_button
    chat_window=tk.Tk()
    chat_window.title(f"Python ChatRoom - {username}")
    chat_window.geometry("760x520")
    content_frame=tk.Frame(chat_window)
    content_frame.pack(fill="both",expand=True,padx=10,pady=10)
    chat_text=tk.Text(content_frame,state="disabled",wrap="word")
    chat_text.pack(side="left",fill="both",expand=True)
    user_frame=tk.Frame(content_frame,width=160)
    user_frame.pack(side="right",fill="y",padx=(10,0))
    user_label=tk.Label(user_frame,text="在线用户",font=("Arial",11,"bold"))
    user_label.pack(pady=(0,5))
    user_listbox=tk.Listbox(user_frame)
    user_listbox.pack(fill="both",expand=True)
    bottom_frame=tk.Frame(chat_window)
    bottom_frame.pack(fill="x",padx=10,pady=(0,10))
    message_entry=tk.Entry(bottom_frame,font=("Arial",11))
    message_entry.pack(side="left",fill="x",expand=True)
    private_button=tk.Button(bottom_frame,text="私聊",command=send_private_message)
    private_button.pack(side="right",padx=5)
    send_button=tk.Button(bottom_frame,text="群发",command=send_message)
    send_button.pack(side="right")
    message_entry.bind("<Return>",lambda event:send_message())
    chat_window.protocol("WM_DELETE_WINDOW",close_chat)
    receive_thread=threading.Thread(target=receive_messages,daemon=True)
    receive_thread.start()
    display_message("[系统] 已成功连接服务器")
    message_entry.focus()
    chat_window.mainloop()
def display_message(message):
    try:
        chat_text.config(state="normal")
        chat_text.insert(tk.END,message+"\n")
        chat_text.config(state="disabled")
        chat_text.see(tk.END)
    except tk.TclError:
        pass
def update_user_list(usernames):
    try:
        user_listbox.delete(0,tk.END)
        for name in usernames:
            user_listbox.insert(tk.END,name)
    except tk.TclError:
        pass
def show_server_error(code,content):
    text=content
    if code:
        text+=f"\n\n错误代码：{code}"
    messagebox.showerror("服务器错误",text)
def handle_disconnect():
    global connected
    if not connected:
        return
    connected=False
    display_message("[系统] 与服务器的连接已经断开")
    try:
        message_entry.config(state="disabled")
        send_button.config(state="disabled")
        private_button.config(state="disabled")
        user_listbox.delete(0,tk.END)
    except tk.TclError:
        pass
    try:
        messagebox.showwarning("连接断开","与服务器的连接已经断开。\n请关闭客户端后重新连接。")
    except tk.TclError:
        pass
def get_valid_content():
    content=message_entry.get().strip()
    if not content:
        return None
    if len(content)>MAX_MESSAGE_LENGTH:
        messagebox.showwarning("消息过长",f"消息不能超过 {MAX_MESSAGE_LENGTH} 个字符。")
        return None
    return content
def send_message():
    if not connected:
        messagebox.showwarning("无法发送","当前已经与服务器断开连接。")
        return
    content=get_valid_content()
    if content is None:
        return
    try:
        send_json({"type":"message","content":content})
        message_entry.delete(0,tk.END)
    except (BrokenPipeError,ConnectionResetError,OSError):
        handle_disconnect()
def send_private_message():
    if not connected:
        messagebox.showwarning("无法发送","当前已经与服务器断开连接。")
        return
    selection=user_listbox.curselection()
    if not selection:
        messagebox.showwarning("提示","请先选择一个在线用户。")
        return
    target=user_listbox.get(selection[0])
    if target==username:
        messagebox.showwarning("提示","不能私聊自己。")
        return
    content=get_valid_content()
    if content is None:
        return
    try:
        send_json({"type":"private","target":target,"content":content})
        message_entry.delete(0,tk.END)
    except (BrokenPipeError,ConnectionResetError,OSError):
        handle_disconnect()
def receive_messages():
    while True:
        try:
            message=receive_json()
            if message is None:
                chat_window.after(0,handle_disconnect)
                break
            if not message:
                continue
            if not isinstance(message,dict):
                continue
            msg_type=message.get("type")
            if msg_type=="message_sent":
                content=message.get("content","")
                chat_window.after(0,display_message,f"我: {content}")
            elif msg_type=="message":
                sender=message.get("username","")
                content=message.get("content","")
                chat_window.after(0,display_message,f"{sender}: {content}")
            elif msg_type=="system":
                content=message.get("content","")
                chat_window.after(0,display_message,f"[系统] {content}")
            elif msg_type=="user_list":
                usernames=message.get("users",[])
                chat_window.after(0,update_user_list,usernames)
            elif msg_type=="private":
                sender=message.get("from","")
                target=message.get("to","")
                content=message.get("content","")
                if sender==username:
                    text=f"[私聊] 我 -> {target}: {content}"
                else:
                    text=f"[私聊] {sender} -> 我: {content}"
                chat_window.after(0,display_message,text)
            elif msg_type=="error":
                code=message.get("code","")
                content=message.get("content","未知错误")
                chat_window.after(0,show_server_error,code,content)
        except json.JSONDecodeError:
            print("[ERROR] Server返回非法JSON")
        except UnicodeDecodeError:
            print("[ERROR] Server返回非UTF-8数据")
        except (ConnectionResetError,BrokenPipeError,OSError):
            try:
                chat_window.after(0,handle_disconnect)
            except tk.TclError:
                pass
            break
        except Exception as e:
            print("[ERROR] 接收线程异常：",e)
            try:
                chat_window.after(0,handle_disconnect)
            except tk.TclError:
                pass
            break
def close_chat():
    global connected
    connected=False
    if client_socket is not None:
        try:
            send_json({"type":"quit"})
        except OSError:
            pass
        try:
            client_socket.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            client_socket.close()
        except OSError:
            pass
    try:
        chat_window.destroy()
    except tk.TclError:
        pass
login_window.mainloop()
