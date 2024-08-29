from algorithms.flooding import Flooding
import threading
import time

neighbors = {
    "A": ("127.0.0.1", 5000),
    "B": ("127.0.0.1", 5001),
    "C": ("127.0.0.1", 5002),
}

# Inicializar y comenzar los tres nodos
node_A = Flooding("A", neighbors)
node_B = Flooding("B", neighbors)
node_C = Flooding("C", neighbors)

node_A.start_node()
node_B.start_node()
node_C.start_node()

# Esperar a que todos los nodos estén listos
time.sleep(2)


def send_messages(node):
    while node.running:
        user_input = input(f"Enter a message to flood from {node.node_id}: ")
        message = {
            "type": "message",
            "from": node.node_id,
            "to": "ALL",
            "hops": 0,
            "headers": [],
            "payload": user_input
        }
        node.flood(message)


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

node_A.stop_node()
node_B.stop_node()
node_C.stop_node()
