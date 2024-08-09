class Flooding:
    def __init__(self):
        self.visited_nodes = set()

    def flood(self, current_node, neighbors):
        if current_node in self.visited_nodes:
            return
        self.visited_nodes.add(current_node)
        print(f"Flooding message from {current_node}")
        for neighbor in neighbors:
            self.flood(neighbor, neighbors)
