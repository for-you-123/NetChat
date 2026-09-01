import json
import socket
import threading
import tkinter as tk
from tkinter import messagebox
from common.config import HOST,PORT,MAX_MESSAGE_LENGTH,LOGIN_TIMEOUT
from common.protocol import send_json,receive_json
class ChatClientApp:
    def __init__(self):
        self.client_socket=None
        self.username=""
        self.connected=False
        self.receive_buffer=b""
        self.login_window=None
        self.chat_window=None
        self.username_entry=None
        self.chat_text=None
        self.message_entry=None
        self.user_listbox=None
        self.login_button=None
        self.send_button=None
        self.private_button=None
    def send_data(self,data):
        if self.client_socket is None:
            raise ConnectionError("尚未连接服务器")
        send_json(self.client_socket,data)
    def create_login_window(self):
        self.login_window=tk.Tk()
        self.login_window.title("登录聊天室")
        self.login_window.geometry("340x220")
        self.login_window.resizable(False,False)
        title_label=tk.Label(self.login_window,text="Python ChatRoom",font=("Arial",16))
        title_label.pack(pady=20)
        nickname_label=tk.Label(self.login_window,text="请输入昵称")
        nickname_label.pack(pady=(0,5))
        self.username_entry=tk.Entry(self.login_window,font=("Arial",12))
        self.username_entry.pack(padx=30,fill="x")
        self.login_button=tk.Button(self.login_window,text="进入聊天室",command=self.login)
        self.login_button.pack(pady=20)
        self.username_entry.bind("<Return>",lambda event:self.login())
        self.username_entry.focus()
    def login(self):
        username=self.username_entry.get().strip()
        if not username:
            messagebox.showwarning("提示","昵称不能为空")
            return
        self.login_button.config(state="disabled")
        try:
            self.client_socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            self.client_socket.settimeout(LOGIN_TIMEOUT)
            self.client_socket.connect((HOST,PORT))
            self.receive_buffer=b""
            self.send_data({"type":"login","username":username})
            response,self.receive_buffer=receive_json(self.client_socket,self.receive_buffer)
            if response is None:
                raise ConnectionError("服务器已经断开")
            if response.get("type")!="login_result":
                raise ConnectionError("服务器登录响应异常")
            if not response.get("success",False):
                error=response.get("error","登录失败")
                messagebox.showerror("登录失败",error)
                self.cleanup_socket()
                return
            self.username=username
            self.connected=True
            self.client_socket.settimeout(None)
        except ConnectionRefusedError:
            messagebox.showerror("连接失败","无法连接服务器。\n请确认 server.py 是否已经启动。")
            self.cleanup_socket()
            return
        except socket.timeout:
            messagebox.showerror("连接超时","服务器长时间没有响应。")
            self.cleanup_socket()
            return
        except (ConnectionResetError,ConnectionError,OSError) as e:
            messagebox.showerror("连接失败",f"网络连接失败：{e}")
            self.cleanup_socket()
            return
        except (json.JSONDecodeError,UnicodeDecodeError):
            messagebox.showerror("登录失败","服务器返回的数据无法解析。")
            self.cleanup_socket()
            return
        finally:
            try:
                self.login_button.config(state="normal")
            except tk.TclError:
                pass
        self.login_window.destroy()
        self.create_chat_window()
    def create_chat_window(self):
        self.chat_window=tk.Tk()
        self.chat_window.title(f"Python ChatRoom - {self.username}")
        self.chat_window.geometry("760x520")
        content_frame=tk.Frame(self.chat_window)
        content_frame.pack(fill="both",expand=True,padx=10,pady=10)
        self.chat_text=tk.Text(content_frame,state="disabled",wrap="word")
        self.chat_text.pack(side="left",fill="both",expand=True)
        user_frame=tk.Frame(content_frame,width=160)
        user_frame.pack(side="right",fill="y",padx=(10,0))
        user_label=tk.Label(user_frame,text="在线用户",font=("Arial",11,"bold"))
        user_label.pack(pady=(0,5))
        self.user_listbox=tk.Listbox(user_frame)
        self.user_listbox.pack(fill="both",expand=True)
        bottom_frame=tk.Frame(self.chat_window)
        bottom_frame.pack(fill="x",padx=10,pady=(0,10))
        self.message_entry=tk.Entry(bottom_frame,font=("Arial",11))
        self.message_entry.pack(side="left",fill="x",expand=True)
        self.private_button=tk.Button(bottom_frame,text="私聊",command=self.send_private_message)
        self.private_button.pack(side="right",padx=5)
        self.send_button=tk.Button(bottom_frame,text="群发",command=self.send_message)
        self.send_button.pack(side="right")
        self.message_entry.bind("<Return>",lambda event:self.send_message())
        self.chat_window.protocol("WM_DELETE_WINDOW",self.close)
        receive_thread=threading.Thread(target=self.receive_messages,daemon=True)
        receive_thread.start()
        self.display_message("[系统] 已成功连接服务器")
        self.message_entry.focus()
        self.chat_window.mainloop()
    def display_message(self,message):
        try:
            self.chat_text.config(state="normal")
            self.chat_text.insert(tk.END,message+"\n")
            self.chat_text.config(state="disabled")
            self.chat_text.see(tk.END)
        except tk.TclError:
            pass
    def update_user_list(self,usernames):
        try:
            self.user_listbox.delete(0,tk.END)
            for name in usernames:
                self.user_listbox.insert(tk.END,name)
        except tk.TclError:
            pass
    def get_valid_content(self):
        content=self.message_entry.get().strip()
        if not content:
            return None
        if len(content)>MAX_MESSAGE_LENGTH:
            messagebox.showwarning("消息过长",f"消息不能超过 {MAX_MESSAGE_LENGTH} 个字符。")
            return None
        return content
    def send_message(self):
        if not self.connected:
            messagebox.showwarning("无法发送","当前已经与服务器断开连接。")
            return
        content=self.get_valid_content()
        if content is None:
            return
        try:
            self.send_data({"type":"message","content":content})
            self.message_entry.delete(0,tk.END)
        except (BrokenPipeError,ConnectionResetError,OSError):
            self.handle_disconnect()
    def send_private_message(self):
        if not self.connected:
            messagebox.showwarning("无法发送","当前已经与服务器断开连接。")
            return
        selection=self.user_listbox.curselection()
        if not selection:
            messagebox.showwarning("提示","请先选择一个在线用户。")
            return
        target=self.user_listbox.get(selection[0])
        if target==self.username:
            messagebox.showwarning("提示","不能私聊自己。")
            return
        content=self.get_valid_content()
        if content is None:
            return
        try:
            self.send_data({"type":"private","target":target,"content":content})
            self.message_entry.delete(0,tk.END)
        except (BrokenPipeError,ConnectionResetError,OSError):
            self.handle_disconnect()
    def receive_messages(self):
        while self.connected:
            try:
                message,self.receive_buffer=receive_json(self.client_socket,self.receive_buffer)
                if message is None:
                    self.schedule_disconnect()
                    break
                if not message:
                    continue
                if not isinstance(message,dict):
                    continue
                msg_type=message.get("type")
                if msg_type=="message_sent":
                    content=message.get("content","")
                    message_time=message.get("time","")
                    text=f"[{message_time}] 我: {content}"
                    self.chat_window.after(0,self.display_message,text)
                elif msg_type=="message":
                    sender=message.get("username","")
                    content=message.get("content","")
                    message_time=message.get("time","")
                    text=f"[{message_time}] {sender}: {content}"
                    self.chat_window.after(0,self.display_message,text)
                elif msg_type=="system":
                    content=message.get("content","")
                    self.chat_window.after(0,self.display_message,f"[系统] {content}")
                elif msg_type=="user_list":
                    usernames=message.get("users",[])
                    self.chat_window.after(0,self.update_user_list,usernames)
                elif msg_type=="private":
                    sender=message.get("from","")
                    target=message.get("to","")
                    content=message.get("content","")
                    message_time=message.get("time","")
                    if sender==self.username:
                        text=f"[{message_time}] [私聊] 我 -> {target}: {content}"
                    else:
                        text=f"[{message_time}] [私聊] {sender} -> 我: {content}"
                    self.chat_window.after(0,self.display_message,text)
                elif msg_type=="error":
                    code=message.get("code","")
                    content=message.get("content","未知错误")
                    self.chat_window.after(0,self.show_server_error,code,content)
            except json.JSONDecodeError:
                print("[ERROR] Server返回非法JSON")
            except UnicodeDecodeError:
                print("[ERROR] Server返回非法UTF‑8")
            except (ConnectionResetError,BrokenPipeError,OSError):
                self.schedule_disconnect()
                break
            except Exception as e:
                print("[ERROR] 接收线程异常：",e)
                self.schedule_disconnect()
                break
    def show_server_error(self,code,content):
        text=content
        if code:
            text+=f"\n\n错误代码：{code}"
        messagebox.showerror("服务器错误",text)
    def schedule_disconnect(self):
        try:
            self.chat_window.after(0,self.handle_disconnect)
        except tk.TclError:
            pass
    def handle_disconnect(self):
        if not self.connected:
            return
        self.connected=False
        self.display_message("[系统] 与服务器的连接已经断开")
        try:
            self.message_entry.config(state="disabled")
            self.send_button.config(state="disabled")
            self.private_button.config(state="disabled")
            self.user_listbox.delete(0,tk.END)
        except tk.TclError:
            pass
        try:
            messagebox.showwarning("连接断开","与服务器的连接已经断开。\n请关闭客户端后重新连接。")
        except tk.TclError:
            pass
    def cleanup_socket(self):
        self.connected=False
        if self.client_socket is None:
            return
        try:
            self.client_socket.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            self.client_socket.close()
        except OSError:
            pass
        self.client_socket=None
    def close(self):
        if self.connected:
            try:
                self.send_data({"type":"quit"})
            except OSError:
                pass
        self.cleanup_socket()
        try:
            self.chat_window.destroy()
        except tk.TclError:
            pass
    def run(self):
        self.create_login_window()
        self.login_window.mainloop()
if __name__=="__main__":
    app=ChatClientApp()
    app.run()
