from algorithms.dijkstra import Dijkstra
import threading
import time

neighbors = {
    "A": ("127.0.0.1", 5000),
    "B": ("127.0.0.1", 5001),
    "C": ("127.0.0.1", 5002),
}

graph = {
    "A": {"B": 1, "C": 4},
    "B": {"A": 1, "C": 2},
    "C": {"A": 4, "B": 2}
}

# Inicializar y comenzar los tres nodos
node_A = Dijkstra("A", neighbors, graph)
node_B = Dijkstra("B", neighbors, graph)
node_C = Dijkstra("C", neighbors, graph)

node_A.start_node()
node_B.start_node()
node_C.start_node()

import time

time.sleep(2)

def send_messages(node):
    while node.running:
        user_input = input(f"Enter a message to trigger Dijkstra on {node.node_id} or type 'STOP' to terminate: ")
        message = {
            "type": "message",
            "from": node.node_id,
            "to": "ALL",
            "hops": 0,
            "headers": [],
            "payload": user_input
        }
        if user_input == "STOP":
            node.send_message(node.node_id, message)
            node.stop_node()
        else:
            node.dijkstra()

# Crear hilos para enviar mensajes desde cada nodo
thread_A = threading.Thread(target=send_messages, args=(node_A,))
thread_B = threading.Thread(target=send_messages, args=(node_B,))
thread_C = threading.Thread(target=send_messages, args=(node_C,))

thread_A.start()
thread_B.start()
thread_C.start()

# Espera a que los hilos terminen antes de cerrar los nodos
thread_A.join()
thread_B.join()
thread_C.join()