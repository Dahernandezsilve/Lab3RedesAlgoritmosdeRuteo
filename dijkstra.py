class Dijkstra:
    def __init__(self, graph):
        self.graph = graph

    def find_shortest_path(self, start_node):
        unvisited_nodes = list(self.graph.keys())
        shortest_path = {}
        for node in unvisited_nodes:
            shortest_path[node] = float('inf')
        shortest_path[start_node] = 0

        while unvisited_nodes:
            current_node = min(
                (node for node in unvisited_nodes), key=lambda node: shortest_path[node]
            )
            unvisited_nodes.remove(current_node)

            for neighbor, weight in self.graph[current_node].items():
                tentative_value = shortest_path[current_node] + weight
                if tentative_value < shortest_path[neighbor]:
                    shortest_path[neighbor] = tentative_value

        return shortest_path
