import socket
import threading
import json
import sqlite3
from database import(init_database,save_message,load_messages)
HOST="127.0.0.1"
PORT=5000
MAX_MESSAGE_LENGTH=500
users={}
users_lock=threading.Lock()
send_lock=threading.Lock()
def send_json(conn,data):
    text=json.dumps(data,ensure_ascii=False)
    packet=(text+"\n").encode("utf-8")
    with send_lock:
        conn.sendall(packet)
def send_error(conn,code,content):
    try:
        send_json(conn,{"type":"error","code":code,"content":content})
    except OSError:
        pass
def receive_json(conn,buffer):
    while b"\n" not in buffer:
        chunk=conn.recv(4096)
        if not chunk:
            return None,buffer
        buffer+=chunk
    line,buffer=buffer.split(b"\n",1)
    if not line:
        return {},buffer
    text=line.decode("utf-8")
    message=json.loads(text)
    return message,buffer
def get_online_users():
    with users_lock:
        return list(users.keys())
def broadcast(data,sender=None):
    with users_lock:
        connections=list(users.items())
    for username,conn in connections:
        if conn==sender:
            continue
        try:
            send_json(conn,data)
        except OSError:
            print(f"[WARN] 向 {username} 发送失败")
def broadcast_user_list():
    usernames=get_online_users()
    data={"type":"user_list","users":usernames}
    with users_lock:
        connections=list(users.items())
    for username,conn in connections:
        try:
            send_json(conn,data)
        except OSError:
            print(f"[WARN] 向 {username} 发送用户列表失败")
def validate_content(content):
    if not isinstance(content,str):
        return False,"消息内容必须是字符串"
    content=content.strip()
    if not content:
        return False,"消息不能为空"
    if len(content)>MAX_MESSAGE_LENGTH:
        return False,f"消息不能超过 {MAX_MESSAGE_LENGTH} 个字符"
    return True,content
def cleanup_client(username,conn):
    removed=False
    if username:
        with users_lock:
            if username in users and users[username]==conn:
                del users[username]
                removed=True
    try:
        conn.shutdown(socket.SHUT_RDWR)
    except OSError:
        pass
    try:
        conn.close()
    except OSError:
        pass
    if removed:
        print(f"[INFO] {username} 已下线")
        broadcast({"type":"system","content":f"{username} 退出聊天室"})
        broadcast_user_list()
def handle_public_message(username,conn,message):
    success,result=validate_content(message.get("content"))
    if not success:
        send_error(conn,"INVALID_MESSAGE",result)
        return
    content=result
    try:
        save_message(username=username,content=content,message_type="message",target=None)
    except sqlite3.Error as e:
        print("[ERROR] 数据库保存失败：",e)
        send_error(conn,"DATABASE_ERROR","消息保存失败，请稍后重试")
        return
    broadcast({"type":"message","username":username,"content":content},sender=conn)
    send_json(conn,{"type":"message_sent","content":content})
    print(f"[群聊] {username}: {content}")
def handle_private_message(username,conn,message):
    target=message.get("target","")
    if not isinstance(target,str):
        send_error(conn,"INVALID_TARGET","私聊目标格式错误")
        return
    target=target.strip()
    if not target:
        send_error(conn,"EMPTY_TARGET","请选择私聊用户")
        return
    if target==username:
        send_error(conn,"SELF_PRIVATE_MESSAGE","不能私聊自己")
        return
    success,result=validate_content(message.get("content"))
    if not success:
        send_error(conn,"INVALID_MESSAGE",result)
        return
    content=result
    with users_lock:
        target_conn=users.get(target)
    if target_conn is None:
        send_error(conn,"USER_OFFLINE",f"{target} 当前不在线")
        return
    try:
        save_message(username=username,content=content,message_type="private",target=target)
    except sqlite3.Error as e:
        print("[ERROR] 私聊保存失败：",e)
        send_error(conn,"DATABASE_ERROR","私聊消息保存失败")
        return
    private_message={"type":"private","from":username,"to":target,"content":content}
    try:
        send_json(target_conn,private_message)
    except OSError:
        send_error(conn,"USER_OFFLINE",f"{target} 当前无法接收消息")
        return
    send_json(conn,private_message)
    print(f"[私聊] {username} -> {target}: {content}")
def handle_client(conn,addr):
    username=""
    buffer=b""
    print(f"[INFO] 新连接：{addr}")
    try:
        try:
            login_message,buffer=receive_json(conn,buffer)
        except UnicodeDecodeError:
            send_error(conn,"INVALID_ENCODING","消息必须使用 UTF-8")
            return
        except json.JSONDecodeError:
            send_error(conn,"INVALID_JSON","登录消息不是合法 JSON")
            return
        if login_message is None:
            return
        if login_message.get("type")!="login":
            send_json(conn,{"type":"login_result","success":False,"error":"第一条消息必须是 login"})
            return
        username=login_message.get("username","")
        if not isinstance(username,str):
            send_json(conn,{"type":"login_result","success":False,"error":"昵称格式错误"})
            return
        username=username.strip()
        if not username:
            send_json(conn,{"type":"login_result","success":False,"error":"昵称不能为空"})
            return
        with users_lock:
            if username in users:
                duplicate=True
            else:
                users[username]=conn
                duplicate=False
        if duplicate:
            send_json(conn,{"type":"login_result","success":False,"code":"DUPLICATE_USERNAME","error":"该昵称已经被使用"})
            return
        send_json(conn,{"type":"login_result","success":True,"username":username})
        print(f"[INFO] {username} 登录成功")
        broadcast({"type":"system","content":f"{username} 加入聊天室"},sender=conn)
        broadcast_user_list()
        while True:
            try:
                message,buffer=receive_json(conn,buffer)
            except UnicodeDecodeError:
                send_error(conn,"INVALID_ENCODING","消息编码必须使用 UTF-8")
                continue
            except json.JSONDecodeError:
                send_error(conn,"INVALID_JSON","JSON 格式错误")
                continue
            if message is None:
                print(f"[INFO] {username} 连接关闭")
                break
            if not message:
                continue
            if not isinstance(message,dict):
                send_error(conn,"INVALID_MESSAGE","消息必须是 JSON 对象")
                continue
            msg_type=message.get("type")
            if msg_type=="message":
                handle_public_message(username,conn,message)
            elif msg_type=="private":
                handle_private_message(username,conn,message)
            elif msg_type=="quit":
                print(f"[INFO] {username} 正常退出")
                break
            else:
                send_error(conn,"UNKNOWN_MESSAGE_TYPE",f"未知消息类型：{msg_type}")
    except ConnectionResetError:
        print(f"[WARN] {username or addr} 异常断开连接")
    except BrokenPipeError:
        print(f"[WARN] {username or addr} 连接已损坏")
    except OSError as e:
        print(f"[WARN] {username or addr} 网络异常：{e}")
    except Exception as e:
        print(f"[ERROR] 处理客户端 {username or addr} 发生异常：{e}")
    finally:
        cleanup_client(username,conn)
        print(f"[INFO] 客户端线程结束：{addr}")
def print_history():
    try:
        rows=load_messages()
    except sqlite3.Error as e:
        print("[ERROR] 读取历史记录失败：",e)
        return
    print()
    print("="*60)
    print("历史聊天记录")
    print("="*60)
    if not rows:
        print("暂无历史记录")
    for row in rows:
        message_id,username,content,message_type,target,created_at=row
        if message_type=="message":
            print(f"[{created_at}] [群聊] {username}: {content}")
        elif message_type=="private":
            print(f"[{created_at}] [私聊] {username} -> {target}: {content}")
    print("="*60)
    print()
def main():
    try:
        init_database()
    except sqlite3.Error as e:
        print("[ERROR] 数据库初始化失败：",e)
        return
    print_history()
    server_socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    try:
        server_socket.bind((HOST,PORT))
        server_socket.listen()
        print(f"Server启动成功：{HOST}:{PORT}")
        print("等待客户端连接...")
        while True:
            try:
                conn,addr=server_socket.accept()
            except OSError:
                break
            thread=threading.Thread(target=handle_client,args=(conn,addr),daemon=True)
            thread.start()
    except KeyboardInterrupt:
        print()
        print("收到 Ctrl+C，Server准备关闭")
    except OSError as e:
        print("[ERROR] Server启动失败：",e)
    finally:
        try:
            server_socket.close()
        except OSError:
            pass
        print("Server已关闭")
if __name__=="__main__":
    main()
