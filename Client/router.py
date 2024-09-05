import asyncio
from nodeConfig import NodeConfig
from accountManager import AccountManager
from communicationManager import CommunicationManager
from MessageHandler import MessageHandler
import sys
import threading
import tkinter as tk
from tkinter import simpledialog


# Función para mostrar una ventana de entrada con tkinter
def ask_for_message():
    root = tk.Tk()
    root.withdraw()  # Oculta la ventana principal

    recipient = simpledialog.askstring(
        "Recipient", "Escribe la dirección del destinatario (e.g., user@server.lol):")
    message = simpledialog.askstring(
        "Message", "Escribe el mensaje que deseas enviar:")

    root.destroy()  # Cierra la ventana

    return recipient, message


async def startNode(node_id: str, password: str, routing_algorithm: str, type_names: str, type_topo: str, sendMessage=False):
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

        if sendMessage:
            recipient, user_input = ask_for_message()
            if recipient and user_input:  # Verifica que no sean None
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

        if comm_manager.routing_algorithm == 'flooding':
            await message_handler.receive_messages()
        else:
            comm_manager.sendEcho()
            await message_handler.receive_messages()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Cerrar sesión
        account_manager.logout()


def asyncNode(node_id: str, password: str, routing_algorithm: str, type_names: str, type_topo: str, sendMessage=False):
    asyncio.run(startNode(node_id, password, routing_algorithm,
                type_names, type_topo, sendMessage))


if __name__ == "__main__":

    if sys.argv[1] == 'true':
        threads = []
        threads.append(threading.Thread(target=asyncNode, args=(
            'B', 'ines130602', sys.argv[2], '../config/names2024-Conjunto1-9-4-2024.txt', '../config/topo2024-Conjunto1-9-4-2024.txt')))
        threads.append(threading.Thread(target=asyncNode, args=(
            'C', '123', sys.argv[2], '../config/names2024-Conjunto1-9-4-2024.txt', '../config/topo2024-Conjunto1-9-4-2024.txt')))
        # threads.append(threading.Thread(target=asyncNode, args=('A', '1234', sys.argv[2], '../config/names2024-randomX-2024.txt', '../config/topo2024-randomX-2024.txt')))
        # threads.append(threading.Thread(target=asyncNode, args=('E', '1234', sys.argv[2], '../config/names2024-randomX-2024.txt', '../config/topo2024-randomX-2024.txt')))

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

    else:
        node_id = sys.argv[1]
        password = sys.argv[2]
        routing_algorithm = sys.argv[3]
        asyncio.run(startNode(node_id, password, routing_algorithm,
                    '../config/names2024-Conjunto1-9-4-2024.txt', '../config/topo2024-Conjunto1-9-4-2024.txt', True))
