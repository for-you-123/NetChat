import socket
HOST = "127.0.0.1"
PORT = 5000
client_socket = socket.socket(
    socket.AF_INET,
    socket.SOCK_STREAM
)
try:
    print("正在连接服务器...")
    client_socket.connect((HOST, PORT))
    print("连接服务器成功")
    print("输入 quit 可以退出")
    while True:
        message = input("我：")
        client_socket.send(message.encode("utf-8"))
        if message == "quit":
            print("已退出聊天室")
            break
        reply_data = client_socket.recv(1024)
        if not reply_data:
            print("服务器已断开连接")
            break
        reply = reply_data.decode("utf-8")
        print("服务器：", reply)
        if reply == "quit":
            print("服务器结束了聊天")
            break
except ConnectionRefusedError:
    print("连接失败：服务器可能没有启动")
except ConnectionResetError:
    print("连接已断开")
except Exception as e:
    print("发生异常：", e)
finally:
    client_socket.close()
    print("客户端关闭")