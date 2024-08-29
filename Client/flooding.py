import socket
import threading
import json


class Flooding:
    def __init__(self, node_id, neighbors):
        self.node_id = node_id
        self.neighbors = neighbors
        self.visited_nodes = set()
        self.running = True  # Control para detener el bucle

    def start_node(self):
        self.listener_thread = threading.Thread(target=self.listen)
        self.listener_thread.start()

    def listen(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.neighbors[self.node_id][0],
                    self.neighbors[self.node_id][1]))
            s.listen()
            while self.running:  # Seguir escuchando mientras que el nodo esté abierto
                conn, addr = s.accept()
                with conn:
                    data = conn.recv(1024)
                    if data:
                        message = json.loads(data.decode('utf-8'))
                        self.handle_message(message)

    def flood(self, message):
        if message["from"] in self.visited_nodes:
            return
        self.visited_nodes.add(message["from"])
        print(f"Flooding message from {message['from']} to neighbors of {self.node_id}")
        for neighbor, (ip, port) in self.neighbors.items():
            if neighbor != self.node_id:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((ip, port))
                    s.sendall(json.dumps(message).encode('utf-8'))

    def handle_message(self, message):
        if message['payload'] == "STOP":  # Comando especial para detener el nodo
            print(f"Node {self.node_id} is stopping.")
            self.running = False
            return
        print(f"Node {self.node_id} received message: {message['payload']}")
        self.flood(message)

    def stop_node(self):
        self.running = False
        self.listener_thread.join()
        print(f"Node {self.node_id} has terminated.")
