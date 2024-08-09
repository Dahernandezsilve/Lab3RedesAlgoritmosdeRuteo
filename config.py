import json

def load_config(path):
    with open(path, 'r') as file:
        return json.load(file)
    
def process_config(names_config, topology_config):
    nodes = {}
    for node, jid in names_config["config"].items():
        nodes[node] = {
            "jid": jid,
            "neighbors": topology_config["config"].get(node, [])
        }
    return nodes

def loadTopologyAndNames():
    names_config = load_config('names.json')
    topology_config = load_config('topology.json')
    return process_config(names_config, topology_config)

NODES = loadTopologyAndNames()