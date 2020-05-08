"""
Серверное приложение для соединений
"""
import asyncio
from asyncio import transports


class ClientProtocol(asyncio.Protocol):
    login: str
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None

    def data_received(self, data: bytes):
        decoded = data.decode()
        print(decoded)

        if self.login is None:
            # login:User
            login_exist = False
            if decoded.startswith("login:"):
                login = decoded.replace("login:", "").replace("\r\n", "")
                for client in self.server.clients:
                    if client.login == login:
                        login_exist = True
                        break
                if login_exist:
                    self.transport.write(f"Логин {login} занят, попробуйте другой".encode())
                    self.connection_lost()
                else:
                    self.login = login
                    self.transport.write(
                         f"Привет, {self.login}!\r\n>>> Вот последние сообщения чата:".encode()
                         )
                    self.send_history()
                    self.send_message(f"Пользователь {self.login} зашел в чат")
        else:
            self.send_message(decoded)

    def send_message(self, message):
        format_string = f"<{self.login}> {message}"
        self.server.messages.append(format_string)
        encoded = format_string.encode()
        for client in self.server.clients:
            if client.login != self.login:
                client.transport.write(encoded)

    def send_history(self):
        if len(self.server.messages) == 0:
            self.transport.write(
                f"Сообщений в чате нет!".encode()
            )
        else:
            if len(self.server.messages) <= 10:
                n = -len(self.server.messages)
            else:
                n = -10
            for i in range(n, 0):
                self.transport.write(
                    f"{self.server.messages[i]}\r\n".encode()
                )

    def connection_made(self, transport: transports.Transport):
        self.transport = transport
        self.server.clients.append(self)
        print("Соединение установлено")

    def connection_lost(self, exception):
        if self.login is not None:
            self.send_message(f"Пользователь {self.login} покинул чат!")
        self.server.clients.remove(self)
        print("Соединение разорвано")


class Server:
    clients: list
    messages: list

    def __init__(self):
        self.clients = []
        self.messages = []

    def create_protocol(self):
        return ClientProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.create_protocol,
            "127.0.0.1",
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
