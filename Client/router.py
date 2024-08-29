import asyncio
from nodeConfig import NodeConfig
from accountManager import AccountManager
from communicationManager import CommunicationManager
from MessageHandler import MessageHandler
import sys
import threading
from algorithms import dijkstra
import json
from time import sleep

async def start_node(node_id: str, password: str, routing_algorithm: str, type_names: str, type_topo: str):
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
        comm_manager = CommunicationManager(account_manager.client, nodeConfig=config, routing_algorithm=routing_algorithm)
        print("🧠🧹",comm_manager.weights)
        message_handler = MessageHandler(account_manager.client, comm_manager)
        message = {
            'type': 'send_routing',
            'to': 'val21240@alumchat.lol',
            'from': username,
            'data': 'Hello, this is a routing message.',
            'hops': len(config.names['config'])
        }
        if routing_algorithm == 'flooding':
            threading.Thread(target=comm_manager.sendRoutingMessageNeighbors, args=(message,)).start()
        else:
            threading.Thread(target=comm_manager.sendRoutingMessageDijkstra, args=(message,)).start()
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

if __name__ == "__main__":

    if len(sys.argv) != 4:
        print("Usage: python router.py <node_id> <password> <routing_algorithm>")
        sys.exit(1)

    node_id = sys.argv[1]
    password = sys.argv[2]
    routing_algorithm = sys.argv[3]
    asyncio.run(start_node(node_id, password, routing_algorithm, '../config/names2024-randomX-2024.txt', '../config/topo2024-randomX-2024.txt'))
