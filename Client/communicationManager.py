from client import XMPPClient
import json
import asyncio
from accountManager import AccountManager
import time
from time import sleep 
from algorithms import dijkstra

# Clase para gestionar la comunicación con otros usuarios
class CommunicationManager:
    # Inicializar la clase con el cliente XMPP y el WebSocket
    def __init__(self, client: XMPPClient, websocket = None, account_manager: AccountManager = None, nodeConfig = None,  routing_algorithm='dijkstra') -> None:
        self.client = client
        self.websocket = websocket
        self.account_manager = account_manager
        self.bookmarksCM = {}
        self.config = nodeConfig
        self.node_id = self.config.node_id
        self.names = self.config.names
        self.neighbors = self.config.neighbors
        self.topology = self.config.topology
        self.routing_algorithm = routing_algorithm
        self.weights = {}
        self.weightsInitial = {}
        self.table = {}
        self.version = 0
        for neighbor in self.neighbors:
            user = self.names['config'][neighbor]
            self.weights[user] = {}


    def sendEcho(self):
        while True:
            sleep(20)
            print("🧠",self.neighbors)
            for neighbor in self.neighbors:
                user = self.names['config'][neighbor]
                start = time.perf_counter()
                self.weightsInitial[user] = start
                self.sendRoutingMessage(user, json.dumps({"type": "echo"}))



    def sendTableToNeighbors(self):
        for neighbor in self.neighbors:
            user = self.names['config'][neighbor]
            self.sendRoutingMessage(user, json.dumps({"type": "weights", "table": self.table[user], "version": self.table[user]["version"], "from": self.node_id}))


    def sendRoutingMessage(self, to, json):
        newMessage = f'<message to="{to}" type="chat"><body>{json}</body></message>'
        print(f"🗂️ Sending routing message to {to}: {newMessage}")
        self.client.send(newMessage)


    def sendRoutingMessageDijkstra(self, jsonS):
        print("🧠 🚗Messsage")
        to = jsonS['to']
        for names in self.names['config']:
            if self.names['config'][names] == to:
                to = names                
        graph = self.table.copy()
        for node in self.topology:
            if node not in graph:
                graph[node] = {}
            for neighbor in self.topology[node]:
                if neighbor not in graph[node]:
                    graph[node][neighbor] = float('inf') 
        path, timeShortestPath = dijkstra(self.node_id, to, graph)

        if path is None:
            print("✖️ Error: No hay camino disponible")
            return
        if len(path) < 2:
            print("✖️ Error: No hay camino disponible")
        else:
            nextNode = path[1]
            nextUser = self.names['config'][nextNode]
            toUser = jsonS['to']
            if nextUser == toUser:
                response = {
                    "type": "message",
                    "from": jsonS['from'],
                    "to": toUser,
                    "data": jsonS['data'],
                }
                self.sendRoutingMessage(toUser, json.dumps(response))
            else:
                if jsonS['hops'] <= 0:
                    print("📩 There are no more hops.")
                else:
                    response = {
                        "type": "send_routing",
                        "from": jsonS["from"],
                        "to": toUser,
                        "data": jsonS['data'],
                        "hops": jsonS['hops']-1,
                    }

                    self.sendRoutingMessage(nextUser, json.dumps(response))

    def sendRoutingMessageNeighbors(self, json):
        to = json['to']
        jsonS = json['from']
        toUser = json['to']
        data = json['data']
        for neighbor in self.neighbors:
            user = self.names['config'][neighbor]
            if user == to:
                response = {
                    "type": "message",
                    "from": jsonS['from'],
                    "to": toUser,
                    "data": jsonS['data'],
                }
                self.sendRoutingMessage(user, json.dunps(response))
            self.sendRoutingMessage(user, json)


    # Método para enviar un mensaje
    def send_message(self, to: str, body: str) -> None:
        self.client.send_message(to, body)


    # Método para manejar mensajes recibidos
    async def handle_received_message(self, message: str, from_attr: str, id_message: str) -> str:
        print(f"Handling received message: {message}")
        json_message = {
            "message": message,
            "from": from_attr,
            "id_message": id_message 
        }

        if json_message:
            print(f"Sending message to WebSocket: {json_message}")
            await self.websocket.send_text(json.dumps(json_message))
        await asyncio.sleep(1) 