from client import XMPPClient
from utils import log_message

# Clase utilizada para la creación y gestión de cuentas de usuario
class AccountManager:
    def __init__(self, server: str, port: int) -> None:
        self.server = server
        self.port = port
        self.client = XMPPClient(server, port, '', '', '')


    # Método para registrar una cuenta de usuario
    def register_account(self, username: str, password: str, name: str = '', email: str = '') -> None:
        self.client.connect_without_auth()
        register_request = (
            f"<iq type='set' id='reg1'>"
            f"<query xmlns='jabber:iq:register'>"
            f"<username>{username}</username>"
            f"<password>{password}</password>"
            f"<name>{name}</name>"  
            f"<email>{email}</email>" 
            f"</query>"
            f"</iq>"
        )
        self.client.send(register_request)
        response = self.client.receive()
        if 'type="result"' in response:
            log_message("Info", "Account registered successfully.")
        else:
            log_message("Error", "Account registration failed.")
        self.client.disconnect()


    # Método para iniciar sesión en una cuenta de usuario
    def login(self, username: str, password: str) -> None:
        self.client.username = username
        self.client.password = password
        self.client.connect()
        self.client.send("<presence><status>Online</status></presence>")
        

    # Método para cerrar sesión en una cuenta de usuario
    def logout(self) -> None:
        self.client.disconnect()

    async def logClose(self) -> None:
        self.client.send("</stream:stream>")
        self.client.disconnect()


    # Método para eliminar una cuenta de usuario
    def delete_account(self) -> None:
        self.client.send("<iq type='set' id='delete1'><query xmlns='jabber:iq:register'><remove/></query></iq>")
        self.client.receive()
        self.client.disconnect()
