import socket
import threading
import json
import heapq

class Dijkstra:
    def __init__(self, node_id, neighbors, graph, weights):
        self.node_id = node_id
        self.neighbors = neighbors
        self.graph = graph
        self.visited_nodes = set()
        self.running = True
        self.distances = {node: float('inf') for node in neighbors}
        self.distances[self.node_id] = 0
        self.predecessors = {}
    
    def start_node(self):
        self.listener_thread = threading.Thread(target=self.listen)
        self.listener_thread.start()

    def listen(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.neighbors[self.node_id][0],
                    self.neighbors[self.node_id][1]))
            s.listen()
            while self.running:
                conn, addr = s.accept()
                with conn:
                    data = conn.recv(1024)
                    if data:
                        message = json.loads(data.decode('utf-8'))
                        self.handle_message(message)

    def send_message(self, target_node, message):
        if target_node in self.neighbors:
            ip, port = self.neighbors[target_node]
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((ip, port))
                s.sendall(json.dumps(message).encode('utf-8'))

    def dijkstra(self):
        pq = [(0, self.node_id)]  # Cola de prioridad con (distancia, nodo)
        while pq:
            current_distance, current_node = heapq.heappop(pq)

            if current_distance > self.distances[current_node]:
                continue

            for neighbor, weight in self.graph.get(current_node, {}).items():
                distance = current_distance + weight

                if distance < self.distances[neighbor]:
                    self.distances[neighbor] = distance
                    self.predecessors[neighbor] = current_node
                    heapq.heappush(pq, (distance, neighbor))
        
        print(f"Node {self.node_id} shortest paths: {self.distances}")

    def handle_message(self, message):
        if message['payload'] == "STOP":
            print(f"Node {self.node_id} received STOP message. Stopping...")
            self.running = False
            return
        print(f"Node {self.node_id} received message: {message['payload']}")
        self.dijkstra()

    def stop_node(self):
        if self.running:
            self.running = False
            self.listener_thread.join()  # Asegura que el hilo de escucha termine
            print(f"Node {self.node_id} has terminated.")

