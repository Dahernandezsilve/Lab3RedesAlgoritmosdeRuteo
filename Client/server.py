from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from client import XMPPClient
from accountManager import AccountManager
from communicationManager import CommunicationManager
from MessageHandler import MessageHandler
from utils import xml_to_json
import json
import asyncio

# Inicializar la aplicación FastAPI
app = FastAPI()

# Diccionario para almacenar los clientes conectados
clients = {}

# Clase para manejar los mensajes recibidos en el WebSocket
class WebSocketMessageHandler(MessageHandler):
    def __init__(self, client, comm_manager: CommunicationManager, websocket: WebSocket) -> None:
        super().__init__(client, comm_manager)
        self.websocket = websocket


# Ruta para la conexión WebSocket
@app.websocket("/ws/{username}/{password}")
async def websocket_endpoint(websocket: WebSocket, username: str, password: str):
    await websocket.accept()
    
    account_manager = AccountManager('alumchat.lol', 5222)
    try:
        account_manager.login(username, password)
    except Exception as e:
        error_message = {"status": "error", "message": "Login failed. Please check your credentials"}
        print(f"Error: {e}")
        await websocket.send_text(json.dumps(error_message))
        await websocket.close()
        return

    clients[username] = account_manager.client
    comm_manager = CommunicationManager(account_manager.client, websocket, account_manager=account_manager)
    message_handler = WebSocketMessageHandler(account_manager.client, comm_manager, websocket)
    
    try:
        roster_response = comm_manager.show_users()
        user_list = {"status": "success", "action": "contacts", "users": roster_response}
        await websocket.send_text(json.dumps(user_list))
    except Exception as e:
        error_message = {"status": "error", "message": f"Failed to retrieve user list: {str(e)}"}
        await websocket.send_text(json.dumps(error_message))

    try:
        await comm_manager.load_and_join_bookmarked_groups()
        user_list = {"status": "success", "message": "Groups loaded succesfully"}
        await websocket.send_text(json.dumps(user_list))
    except Exception as e:
        error_message = {"status": "error", "message": f"Failed to retrieve bookmarks list: {str(e)}"}
        await websocket.send_text(json.dumps(error_message))

    # Inicia la recepción de mensajes
    asyncio.create_task(message_handler.receive_messages())

    while True:
        try:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message["action"] == "show_all_users": # Mostrar todos los usuarios
                try:
                    users = comm_manager.search_all_users()
                    user_list = {"status": "success", "action": "show_all_users", "users": users}
                    await websocket.send_text(json.dumps(user_list))
                except Exception as e:
                    error_message = {"status": "error", "message": f"Failed to retrieve user list: {str(e)}"}
                    await websocket.send_text(json.dumps(error_message))
            
            elif message["action"] == "show_all_groups": # Mostrar todos los grupos
                try:
                    comm_manager.discover_group_chats()
                except Exception as e:
                    error_message = {"status": "error", "message": f"Failed to discovery groups: {str(e)}"}
                    await websocket.send_text(json.dumps(error_message))

            elif message["action"] == "accept_subscription": # Aceptar solicitud de suscripción
                try:
                    print(f"Accepting subscription from {message}")
                    comm_manager.accept_subscription(message["from"])
                    account_manager.client.get_rosterWithoutResponse()
                except Exception as e:
                    error_message = {"status": "error", "message": f"Failed to accept subscription: {str(e)}"}
                    await websocket.send_text(json.dumps(error_message))

            elif message["action"] == "send_message": # Enviar mensaje
                to = message["to"]
                body = message["body"]
                comm_manager.send_message(to, body)
                response = {"status": "success", "message": f"Message sent to {to}"}
                await websocket.send_text(json.dumps(response))

            elif message["action"] == "create_group": # Crear grupo
                try:
                    group_name = message["groupName"]
                    group_description = message["groupDescription"]
                    await comm_manager.join_group_chat(f"{group_name}@conference.{account_manager.client.server}")
                    await comm_manager.create_group(group_name, group_description)
                    await comm_manager.add_group_to_bookmarks(group_name+"@conference."+account_manager.client.server, group_name+"@conference."+account_manager.client.server+"/"+account_manager.client.username)
                except Exception as e:
                    error_message = {"status": "error", "message": f"Failed to create group chat: {str(e)}"}
                    await websocket.send_text(json.dumps(error_message))

            elif message["action"] == "logout": # Cerrar sesion
                try:
                    await account_manager.logClose()
                    response = {"status": "success", "action": "logoutAccept"}
                except Exception as e:
                    error_message = {"status": "error", "message": f"Failed to logout: {str(e)}"}
                    await websocket.send_text(json.dumps(error_message))

            elif message["action"] == "add_contact": # Agregar contacto
                try:
                    contact_username = message["contact_username"]
                    custom_message = message.get("custom_message", "")
                    comm_manager.add_contact(contact_username, custom_message)
                    response = {"status": "success", "message": f"Contact {contact_username} added successfully with message: {custom_message}"}
                    await websocket.send_text(json.dumps(response))
                except Exception as e:
                    error_message = {"status": "error", "message": f"Failed to add contact: {str(e)}"}
                    await websocket.send_text(json.dumps(error_message))

            elif message["action"] == "delete_account": # Eliminar cuenta
                try:
                    account_manager.delete_account()
                    response = {"status": "success", "message": f"Account {account_manager.client.username} deleted successfully"}
                    await websocket.send_text(json.dumps(response))
                except Exception as e:
                    error_message = {"status": "error", "message": f"Failed to delete account: {str(e)}"}
                    await websocket.send_text(json.dumps(error_message))

            elif message["action"] == "join_group": # Unirse a grupo
                try:
                    group_name = message["group_jid"]
                    await comm_manager.join_group_chat(group_name)
                    await comm_manager.add_group_to_bookmarks(group_name, group_name+"/"+account_manager.client.username)
                except Exception as e:
                    error_message = {"status": "error", "message": f"Failed to join group chat: {str(e)}"}
                    await websocket.send_text(json.dumps(error_message))

            elif message["action"] == "send_file": # Enviar archivo
                try:
                    to = message["to"]
                    fileName = message["fileName"]
                    fileType = message["fileType"]
                    fileSize = message["fileSize"]
                    fileData = message["fileData"]
                    await comm_manager.send_file(to, fileName, fileSize, fileType, fileData)

                    response = {"status": "success", "message": f"File {fileName} sended successfully"}
                    await websocket.send_text(json.dumps(response))
                except Exception as e:
                    error_message = {"status": "error", "message": f"Failed to send file: {str(e)}"}
                    await websocket.send_text(json.dumps(error_message))

            elif message["action"] == "set_presence": # Cambiar presencia
                try:
                    presence = message["presence"]
                    status = message["status"]
                    comm_manager.set_presence(presence, status)
                    response = {"status": "success", "message": f"Presence changed successfully"}
                    await websocket.send_text(json.dumps(response))
                except Exception as e:
                    error_message = {"status": "error", "message": f"Failed to change presence: {str(e)}"}
                    await websocket.send_text(json.dumps(error_message))

        except WebSocketDisconnect:
            account_manager.logout()
            break
        except Exception as e: # Manejar errores
            print(f"Error in websocket communication: {e}")
            response = {"status": "error", "message": "Failed to send message"}
            await websocket.send_text(json.dumps(response))
            break

    account_manager.logout()
    del clients[username]


# Ruta para el registro de usuarios
@app.websocket("/register")
async def register_user(websocket: WebSocket):
    await websocket.accept()
    try:
        data = await websocket.receive_text()
        message = json.loads(data)
        username = message["username"]
        password = message["password"]
        name = message["name"]
        email = message["email"]

        account_manager = AccountManager('alumchat.lol', 5222)

        # Registro de cuenta
        account_manager.register_account(username, password, name, email)
        
        # Cerrar sesión
        account_manager.logout()

        response = {"status": "success", "message": f"User {username} registered successfully."}
        await websocket.send_text(json.dumps(response))
    except Exception as e:
        response = {"status": "error", "message": str(e)}
        await websocket.send_text(json.dumps(response))
    finally:
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
