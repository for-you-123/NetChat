import threading
class ClientManager:
    def __init__(self):
        self.users = {}
        self.lock = threading.Lock()
    def add_user(
        self,
        username,
        conn
    ):
        """
        添加用户。

        成功：
            True

        重复昵称：
            False
        """
        with self.lock:
            if username in self.users:
                return False
            self.users[username] = conn
            return True
    def remove_user(
        self,
        username,
        conn
    ):
        with self.lock:
            if (
                username in self.users
                and
                self.users[username] == conn
            ):
                del self.users[username]
                return True
            return False
    def get_user(
        self,
        username
    ):
        with self.lock:

            return self.users.get(
                username
            )
    def get_usernames(self):
        with self.lock:

            return list(
                self.users.keys()
            )

    def get_connections(self):
        """
        返回：

        [
            ("张三", connA),
            ("李四", connB)
        ]
        """
        with self.lock:
            return list(
                self.users.items()
            )
    def count(self):
        with self.lock:
            return len(
                self.users
            )