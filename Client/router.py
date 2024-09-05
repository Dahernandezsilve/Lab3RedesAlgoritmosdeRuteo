import asyncio
from nodeConfig import NodeConfig
from accountManager import AccountManager
from communicationManager import CommunicationManager
from MessageHandler import MessageHandler
import sys
import threading
import tkinter as tk
from tkinter import ttk
import json 

# Variable global para controlar el ciclo de mensajes
running = True

# Función para mostrar una ventana de entrada personalizada con tkinter


def ask_for_message():
    def send_message():
        nonlocal recipient, message
        recipient = recipient_entry.get()
        message = message_entry.get(
            "1.0", tk.END).strip()  # Obtener texto completo
        root.quit()  # Cerrar ventana al hacer clic en Enviar

    recipient = None
    message = None

    root = tk.Tk()
    root.title("Enviar mensaje")
    root.geometry("400x300")
    root.configure(bg="#F0F0F0")

    # Etiquetas y entradas
    ttk.Label(root, text="Destinatario:", font=("Arial", 12)).pack(pady=10)
    recipient_entry = ttk.Entry(root, width=40)
    recipient_entry.pack(pady=5)

    ttk.Label(root, text="Mensaje:", font=("Arial", 12)).pack(pady=10)
    message_entry = tk.Text(root, width=40, height=5)
    message_entry.pack(pady=5)

    # Botón de enviar
    send_button = ttk.Button(root, text="Enviar", command=send_message)
    send_button.pack(pady=10)

    root.mainloop()
    root.destroy()  # Cierra la ventana después de obtener los datos

    return recipient, message

# Función para enviar mensajes en un bucle continuo


def message_sender(comm_manager, username, routing_algorithm,  type_names, type_topo):
    global running
    config = NodeConfig(type_names, type_topo)
    config.set_node(node_id)
    while running:
        recipient, user_input = ask_for_message()
        for user in config.names['config']:
            if config.names['config'][user] == recipient:
                recipient = user
        
        print("💻💻💻💻",recipient)
        recipient = config.names['config'][recipient]
        if recipient and user_input:
            direct = False
            for neighbor in config.neighbors:
                user = config.names['config'][neighbor]
                if user == recipient:
                    print("📨 Enviando mensaje directo a", recipient)
                    message = {
                        "type": "message",
                        "from": username,
                        "to": recipient,
                        "data": user_input,
                    }
                    if routing_algorithm == 'flooding':
                        threading.Thread(
                            target=comm_manager.sendRoutingMessageNeighbors, args=(message,)).start()
                    else:
                        threading.Thread(
                            target=comm_manager.sendRoutingMessage, args=(recipient, json.dumps(message),)).start()
                    direct = True
                    break    
            if direct == False:
                message = {
                    'type': 'send_routing',
                    'to': recipient,
                    'from': username,
                    'data': user_input,
                    'hops': len(config.names['config'])
                }
                if routing_algorithm == 'flooding':
                    threading.Thread(
                        target=comm_manager.sendRoutingMessageNeighbors, args=(message,)).start()
                else:
                    threading.Thread(
                        target=comm_manager.sendRoutingMessageDijkstra, args=(message,)).start()


async def startNode(node_id: str, password: str, routing_algorithm: str, type_names: str, type_topo: str, sendMessage=False):
    global running
    server = 'alumchat.lol'
    port = 5222

    config = NodeConfig(type_names, type_topo)
    config.set_node(node_id)

    account_manager = AccountManager(server, port)
    username = config.get_node_info()['address']
    password = password
    user = username.split('@')[0]

    try:
        account_manager.login(user, password)
        comm_manager = CommunicationManager(
            account_manager.client, nodeConfig=config, routing_algorithm=routing_algorithm)
        print("🧠🧹", comm_manager.weights)
        message_handler = MessageHandler(account_manager.client, comm_manager)

        # Continuar recibiendo mensajes
        # Si se ha seleccionado 'flooding', mostrar la ventana de mensajes
        threading.Thread(target=message_sender, args=(comm_manager, username, routing_algorithm, type_names, type_topo)).start()

        print("🧠ECHOTHREAD", comm_manager.weights)
        print("🧠ECHOTHREAD", routing_algorithm)
        if routing_algorithm == 'dijkstra':
            threading.Thread(target=comm_manager.sendEcho).start()
        await message_handler.receive_messages()

    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Detener el ciclo de mensajes
        running = False

        # Cerrar sesión
        account_manager.logout()


def asyncNode(node_id: str, password: str, routing_algorithm: str, type_names: str, type_topo: str, sendMessage=False):
    asyncio.run(startNode(node_id, password, routing_algorithm,
                type_names, type_topo, sendMessage))


if __name__ == "__main__":

    if sys.argv[1] == 'true':

        threads = []
        threads.append(threading.Thread(target=asyncNode, args=(
            'C', 'ines130602', sys.argv[2], '../config/names2024-Conjunto1-9-4-2024.txt', '../config/topo2024-Conjunto1-9-4-2024.txt')))
        threads.append(threading.Thread(target=asyncNode, args=(
            'F', '123', sys.argv[2], '../config/names2024-Conjunto1-9-4-2024.txt', '../config/topo2024-Conjunto1-9-4-2024.txt')))

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

    else:

        node_id = sys.argv[1]
        password = sys.argv[2]
        routing_algorithm = sys.argv[3]
        asyncio.run(startNode(node_id, password, routing_algorithm,
                    '../config/names2024-randomX-2024.txt', '../config/topo2024-randomX-2024.txt', True))
