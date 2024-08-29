import asyncio
import xml.etree.ElementTree as ET
from typing import Optional
from communicationManager import CommunicationManager
from utils import split_xml_messages, split_presence_messages, split_all_messages, parse_bookmarks_response, split_iq_messages
import json
import requests
import base64
import uuid
import re
import time
from tabulate import tabulate
from algorithms import dijkstra

# Clase para manejar mensajes XMPP
class MessageHandler:
    # Inicializar la clase con el cliente XMPP y el gestor de comunicación
    def __init__(self, client, comm_manager: CommunicationManager) -> None:
        self.client = client
        self.comm_manager = comm_manager
        self.message_queue = asyncio.Queue()
        self.processed_message_ids = set() # Conjunto para almacenar los IDs de los mensajes procesados

        # Método para recibir mensajes del servidor XMPP
    async def receive_messages(self):
        while True:
            try:
                if self.client.bufferMessagesToClean:
                    # Procesar mensajes almacenados en bufferMessagesToClean
                    for buffered_message in self.client.bufferMessagesToClean:
                        await self.message_queue.put(buffered_message)
                    self.client.bufferMessagesToClean.clear()

                # Recibir nuevo mensaje
                message = await asyncio.to_thread(self.client.receive)

                if message:
                    await self.message_queue.put(message)
                    await self.process_messages()
                else:
                    await asyncio.sleep(1)  # Esperar antes de volver a intentar si no hay datos
                    
            except Exception as e:
                print(f"Error in receive_messages: {e}")
                await asyncio.sleep(1)  # Esperar un momento en caso de error para evitar un bucle rápido


    # Método para procesar mensajes en la cola
    async def process_messages(self):
        while not self.message_queue.empty():
            message = await self.message_queue.get()
            messages = split_all_messages(message)
            for msg in messages:
                await self.handle_message(msg)


    # Método para manejar responses XMPP
    async def handle_message(self, message: str):
        
        if "<message" in message:
            await self.handle_chat_message(message)
        elif "<iq" in message:
            iq_messages = split_iq_messages(message)
            for message in iq_messages:
                await self.handle_iq_message(message)
        elif "<presence" in message:
            await self.handle_presence_message(message)
        else:
            print(f"Unknown message type: {message}")


    # Método para manejar mensajes de chat
    async def handle_chat_message(self, message: str):
        print(f"Processing chat message: {message}")
        try:
            messages = split_xml_messages(message)
            for messag in messages:
                root = ET.fromstring(messag)
                # Buscar el elemento <body> sin importar el espacio de nombres
                body = root.find(".//body")
                from_attr = root.attrib.get('from', 'unknown')
                if body is not None:
                    body_text = body.text
                    jsonBody = json.loads(body_text)
                    from_attr = from_attr.split('/')[0]
                    if jsonBody['type'] == 'echo':
                        print(f"☁️ Echo message received: {jsonBody['type']}")
                        response = {
                            "type": "echo_response",
                        }
                        self.comm_manager.sendRoutingMessage(from_attr.split('/')[0], json.dumps(response))
                    if jsonBody['type'] == 'echo_response':
                        print(f" Echo response received: {jsonBody['type']}")
                        endTime = time.perf_counter()
                        startTime = self.comm_manager.weightsInitial[from_attr]
                        print("🤔" ,startTime, endTime)
                        print(f"⏱️ Elapsed time: {endTime - startTime} seconds")
                        elapsedTime = endTime - startTime
                        self.comm_manager.weights[from_attr] = elapsedTime
                        weightsNodes = {}
                        for key, value in self.comm_manager.weights.items():
                            for neighbor in self.comm_manager.neighbors:
                                if self.comm_manager.names['config'][neighbor] == key:
                                    try:
                                        weightsNodes[neighbor] = float(value)
                                    except:
                                        continue
                                        
                        newTable = {
                            'type': 'weights',
                            'from': self.client.username + '@alumchat.lol',
                            'version': self.comm_manager.version + 1,
                            'table': weightsNodes
                        }
                        self.comm_manager.version += 1
                        for neighbor in self.comm_manager.neighbors:
                            user = self.comm_manager.names['config'][neighbor]
                            self.comm_manager.sendRoutingMessage(user, json.dumps(newTable))

                    if jsonBody['type'] == 'send_routing':
                        if self.comm_manager.routing_algorithm == 'dijkstra':
                            to = jsonBody['to']
                            for names in self.comm_manager.names['config']:
                                if self.comm_manager.names['config'][names] == to:
                                    to = names
                            path, anotherPath = dijkstra(self.comm_manager.node_id, to, self.comm_manager.table)
                            if len(path) < 2:
                                print("✖️ Error: No hay camino disponible")
                            else:
                                nextNode = path[1]
                                nextUser = self.comm_manager.names['config'][nextNode]
                                toUser = jsonBody['to']
                                if nextUser == toUser:
                                    response = {
                                        "type": "message",
                                        "from": jsonBody['from'],
                                        "to": toUser,
                                        "data": jsonBody['data'],
                                    }
                                    self.comm_manager.sendRoutingMessage(toUser, json.dumps(response))
                                else:
                                    if jsonBody['hops'] <= 0:
                                        print("📩 There are no more hops.")
                                    else:
                                        response = {
                                            "type": "send_routing",
                                            "from": jsonBody["from"],
                                            "to": toUser,
                                            "data": jsonBody['data'],
                                            "hops": jsonBody['hops']-1,
                                        }
                                        self.comm_manager.sendRoutingMessage(nextUser, json.dumps(response))
                        elif self.comm_manager.routing_algorithm == 'flooding':
                            for neighbor in self.comm_manager.neighbors:
                                user = self.comm_manager.names['config'][neighbor]
                                if user == jsonBody['to']:
                                    response = {
                                        "type": "message",
                                        "from": jsonBody['from'],
                                        "to": jsonBody['to'],
                                        "data": jsonBody['data'],
                                    }
                                    self.comm_manager.sendRoutingMessage(user, json.dumps(response))
                                    return
                            if jsonBody['hops'] > 0:
                                response = {
                                    "type": "send_routing",
                                    "from": jsonBody['from'],
                                    "to": jsonBody['to'],
                                    "data": jsonBody['data'],
                                    "hops": jsonBody['hops']-1,
                                }
                                for neighbor in self.comm_manager.neighbors:
                                    user = self.comm_manager.names['config'][neighbor]
                                    self.comm_manager.sendRoutingMessage(user, json.dumps(response))
                            else:
                                print("📩 There are no more hops.")
                        else:
                            print("🚫 Error: Routing algorithm not supported")
                    if jsonBody['type'] == 'weights':
                        fromUser = jsonBody['from']
                        version = jsonBody['version']

                        for names in self.comm_manager.names['config']:
                            if self.comm_manager.names['config'][names] == fromUser:
                                fromUser = names

                        if version > self.comm_manager.table.get(fromUser,{}).get('version', 0):
                            
                            self.comm_manager.table[fromUser]= {}
                            self.comm_manager.table[fromUser]['version'] = version
                            self.comm_manager.table[fromUser] = {'table': jsonBody['table']}
                            self.comm_manager.table[fromUser]['version'] = version 
                            print("🖼️", self.comm_manager.neighbors)
                            for neighbor in self.comm_manager.neighbors:
                                user = self.comm_manager.names['config'][neighbor]
                                self.comm_manager.sendRoutingMessage(user, json.dumps(jsonBody))
                        headers = ['Neighbor', 'Weight']
                        rows = [(key, value) for key, value in self.comm_manager.table.items()]
                        print(tabulate(rows, headers=headers, tablefmt='grid'))


                    print(f"Chat message body: {body.text}")
                    print(f"Message received from: {from_attr}")
                else:
                    print("Chat message body not found")
        except ET.ParseError:
            print("Error parsing chat message")


    # Método para manejar mensajes IQ
    async def handle_iq_message(self, message: str):
        print(f"Processing IQ message: {message}")
        try:
            root = ET.fromstring(message)
            iq_type = root.attrib.get('type')
            iq_id = root.attrib.get('id')
            iq_from = root.attrib.get('from')
            iq_to = root.attrib.get('to')

            # Espacios de nombres
            namespace_ping = 'urn:xmpp:ping'
            namespace_version = 'jabber:iq:version'
            namespace_bind = 'urn:ietf:params:xml:ns:xmpp-bind'
            namespace_session = 'urn:ietf:params:xml:ns=xmpp-session'

            # Manejar diferentes tipos de IQ
            if iq_type == 'get':
                if root.find(f".//{{{namespace_ping}}}ping") is not None:
                    # Responder al ping
                    response = (
                        f'<iq type="result" id="{iq_id}" from="{iq_to}" to="{iq_from}"/>'
                    )
                    self.client.send(response)
                elif root.find(f".//{{{namespace_version}}}query") is not None:
                    # Responder a la consulta de versión
                    version_response = (
                        f'<iq type="result" id="{iq_id}" from="{iq_to}" to="{iq_from}">'
                        '<query xmlns="jabber:iq:version">'
                        '<name>DiegosClient</name>'
                        '<version>1.0</version>'
                        '<os>Windows 11</os>'
                        '</query>'
                        '</iq>'
                    )
                    self.client.send(version_response)
                elif root.find(f".//{{{namespace_bind}}}bind") is not None:
                    # Responder a la solicitud de enlace
                    bind_response = (
                        f'<iq type="result" id="{iq_id}" from="{iq_to}" to="{iq_from}">'
                        '<bind xmlns="urn:ietf:params:xml:ns:xmpp-bind">'
                        f'<jid>{iq_to}</jid>'
                        '</bind>'
                        '</iq>'
                    )
                    self.client.send(bind_response)
                else:
                    # Manejar otros tipos de IQ si es necesario
                    print(f"Unhandled IQ message query: {ET.tostring(root, encoding='unicode')}")
            elif iq_type == 'result':
                print(f"Handled IQ message type result: {ET.tostring(root, encoding='unicode')}")

                xml_text = ET.tostring(root, encoding='unicode')
                id_pattern = re.compile(r'id="disco1"')
                bookmark_pattern = re.compile(r'<storage xmlns="storage:bookmarks">')
                
                if id_pattern.search(xml_text):
                    rooms = []
                    try:
                        root = ET.fromstring(xml_text)
                        item_count = 0
                        for item_elem in root.findall(".//{http://jabber.org/protocol/disco#items}item"):
                            jid = item_elem.get("jid", "N/A")
                            name = item_elem.get("name", "N/A")

                            print(f"Item {item_count}: JID={jid}, Name={name}")
                            
                            rooms.append({
                                "jid": jid,
                                "name": name,
                            })
                            item_count += 1
                        groups_list = {"status": "success", "action": "show_all_groups", "groups": rooms}
                        await self.comm_manager.websocket.send_text(json.dumps(groups_list))
                    except ET.ParseError:
                        print("Error parsing discovery response")
                elif root.find(".//{storage:bookmarks}storage") is not None:
                    bookmarks = parse_bookmarks_response(xml_text)
                    if len(bookmarks)>0:
                        for book in bookmarks:
                            await self.comm_manager.join_group_chat(book['jid'])
                        response = {
                            "status": "success",
                            "action": "bookmarks",
                            "message": bookmarks,
                         }
                        await self.comm_manager.websocket.send_text(json.dumps(response))
                elif root.find(".//{jabber:iq:roster}query") is not None:
                    users = []
                    try:
                        # Extraer información de los elementos <item>
                        for item in root.findall(".//{jabber:iq:roster}item"):
                            jid = item.get("jid")
                            name = item.get("name", "")
                            subscription = item.get("subscription", "")
                            
                            if subscription != "none":
                                users.append({"jid": jid, "name": name})
                        
                        # Preparar la lista de usuarios para enviar por WebSocket
                        user_list = {"status": "success", "action": "contacts", "users": users}
                        await self.comm_manager.websocket.send_text(json.dumps(user_list))
                    
                    except ET.ParseError:
                        print("Error parsing XML element")
                else:
                    namespace = '{urn:xmpp:http:upload:0}'
                    slot = root.find(f'.//{namespace}slot')
                    if slot is not None:

                        put_element = slot.find(f'{namespace}put')
                        get_element = slot.find(f'{namespace}get')
                        
                        put_url = put_element.attrib.get('url') if put_element is not None else None
                        get_url = get_element.attrib.get('url') if get_element is not None else None

                        if put_url and get_url:
                            print(f"Received upload URLs:\nPUT: {put_url}\nGET: {get_url}")

                            # Llamar a upload_file con las URLs obtenidas
                            await self.upload_file(put_url, get_url)
                        else:
                            print("Error: Upload URLs not found in the IQ result")
                    else:
                        print("Error: 'slot' element not found in the IQ result")

            elif iq_type == 'error':
                # Manejar mensajes IQ de tipo error
                error_code = root.find('.//error').attrib.get('code', 'unknown')
                error_text = root.find('.//error').text
                print(f"Error received: code={error_code}, text={error_text}")
            else:
                # Manejar otros tipos de IQ si es necesario
                print(f"Unhandled IQ message type: {iq_type}")

        except ET.ParseError:
            print("Error parsing IQ message")
        except Exception as e:
            print(f"Unexpected error processing IQ message: {e}")


    # Método para configurar la función de devolución de llamada de carga
    async def set_upload_callback(self, callback) -> None:
        self.client.uploadCallback = callback


    # Método para subir un archivo al servidor
    async def upload_file(self, put_url: str, get_url: str) -> None:
        if self.client.file_data is not None:
            try:
                # Subir el archivo usando requests
                print("Uploading file...")
                print(f"PUT URL: {put_url}")
                print(f"File size: {self.client.file_data} bytes")
                headers = {'Content-Type': 'application/octet-stream'}
                file_data = base64.b64decode(self.client.file_data)
                response = requests.put(put_url, data=file_data, headers=headers, verify=False)
                print(f"Upload response: {response}")
                if response.status_code == 201:
                    print("File uploaded successfully")
                    await self.send_file_message(get_url, self.client.file_meta.get('to'))
                else:
                    print(f"Failed to upload file: {response.status_code}")
            except Exception as e:
                print(f"Error during file upload: {e}")
        else:
            print("Error: No file data available for upload.")


    # Método para enviar un mensaje de chat con la URL del archivo
    async def send_file_message(self, get_url: str, to: str) -> None:
        # Generar un identificador único para el mensaje
        id_message = str(uuid.uuid4())
        
        # Construir el mensaje de chat con la URL del archivo y el id_message
        if 'conference' in to:
            message = f"""
            <message type='groupchat' to='{to}' from='{self.client.username}' id='{id_message}'>
                <body>{get_url}</body>
            </message>
            """
        else:
            message = f"""
            <message type='chat' to='{to}' from='{self.client.username}' id='{id_message}'>
                <body>{get_url}</body>
            </message>
            """
        try:
            # Enviar el mensaje al destinatario
            self.client.send(message)
            print(f"File message sent to {to} with URL: {get_url} and ID: {id_message}")
            
            # Limpiar datos del archivo después de enviar
            self.client.file_data = None
            self.client.file_meta = {}
            
            # Enviar una respuesta al cliente con el estado y el id_message
            response = {
                "status": "success",
                "action": "fileUrl",
                "url": get_url,
                "id_message": id_message,
                'to': to
            }
            await self.comm_manager.websocket.send_text(json.dumps(response))
        except Exception as e:
            print(f"Error sending file message: {e}")
            # Enviar una respuesta de error al cliente
            response = {
                "status": "error",
                "action": "fileUrl",
                "error": str(e),
                "id_message": id_message
            }
        await self.comm_manager.websocket.send_text(json.dumps(response))


    # Método para manejar mensajes de presencia
    async def handle_presence_message(self, message: str):
        print(f"Processing presence message: {message}")
        try:
            # Dividir el mensaje en fragmentos de presencia
            presence_messages = split_presence_messages(message)
            for presence in presence_messages:
                try:
                    # Intentar analizar cada fragmento de presencia como XML
                    print(f"Individual presence message: {presence}")
                    root = ET.fromstring(presence)

                    # Obtener el tipo de presencia y el JID del remitente
                    presence_type = root.attrib.get('type', 'available')
                    from_jid = root.attrib.get('from', 'unknown')

                    # Obtener el estado y el show, sin tener en cuenta el espacio de nombres
                    show = root.find(".//show")
                    status = root.find(".//status")
                    show_text = show.text if show is not None else 'unknown'
                    status_text = status.text if status is not None else 'unknown'

                    print(f"Presence type: {presence_type}, from: {from_jid}, show: {show_text}, status: {status_text}")

                    # Crear el mensaje para el frontend
                    presence_info = {
                        "from": from_jid,
                        "type": presence_type,
                        "show": show_text,
                        "status": status_text
                    }

                    # Enviar la información al frontend
                    user_list = {"status": "success", "action": "presence_update", "presence": presence_info}
                    await self.comm_manager.websocket.send_text(json.dumps(user_list))

                    # Manejar diferentes tipos de presencia
                    if presence_type == 'unavailable':
                        # El usuario ha cerrado sesión o está desconectado
                        print(f"User {from_jid} is now unavailable.")

                    elif presence_type == 'subscribed':
                        # El otro usuario aceptó tu solicitud de amistad
                        print(f"User {from_jid} accepted your contact request.")
                        # Actualizar el roster
                        roster_response = await asyncio.to_thread(self.comm_manager.show_users)
                        user_list = {"status": "success", "action": "contacts", "users": roster_response}
                        await self.comm_manager.websocket.send_text(json.dumps(user_list))

                except ET.ParseError as e:
                    print(f"Error parsing individual presence message: {presence}")
                    print(f"ParseError details: {e}")
                except Exception as e:
                    print(f"Unexpected error processing presence message: {presence}")
                    print(f"Error details: {e}")
        except Exception as e:
            print(f"Error processing presence messages: {message}")
            print(f"Error details: {e}")