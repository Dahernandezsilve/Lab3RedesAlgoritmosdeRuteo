import json

class NodeConfig:
    def __init__(self, names_file: str, topo_file: str):
        self.names = self.loadConfig(names_file)
        self.topo = self.loadConfig(topo_file)
        self.nodes = self.names['config']
        self.topology = self.topo['config']
        self.node_id = None
        self.neighbors = []

    def loadConfig(self, file_path):
        with open(file_path, 'r') as file:
            content = file.read()
            content = content.replace("'", '"')
            return json.loads(content)
    
    def set_node(self, node_id: str):
        self.node_id = node_id
        if node_id in self.topology:
            self.neighbors = self.topology[node_id]

    def get_node_info(self):
        if self.node_id in self.nodes:
            return {
                'id': self.node_id,
                'address': self.nodes[self.node_id],
                'neighbors': [self.nodes[neighbor] for neighbor in self.neighbors]
            }
        return None

if __name__ == "__main__":
    config = NodeConfig('../config/names2024-randomX-2024.txt', '../config/topo2024-randomX-2024.txt')
    config.set_node('A')
    node_info = config.get_node_info()
    if node_info:
        print(config.names)
        print(f"Node ID: {node_info['id']}")
        print(f"Node Address: {node_info['address']}")
        print(f"Neighbors: {node_info['neighbors']}")
    else:
        print("Node not found.")
