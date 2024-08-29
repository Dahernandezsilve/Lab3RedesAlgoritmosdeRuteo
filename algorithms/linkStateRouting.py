from Client.algorithms.dijkstra import Dijkstra
from Client.algorithms.flooding import Flooding

class LinkStateRouting:
    def __init__(self, node_tables):
        self.node_tables = node_tables

    def run_dijkstra(self, start_node):
        dijkstra = Dijkstra(self.node_tables)
        return dijkstra.find_shortest_path(start_node)

    def run_flooding(self, start_node, neighbors):
        flooding = Flooding()
        flooding.flood(start_node, neighbors)
