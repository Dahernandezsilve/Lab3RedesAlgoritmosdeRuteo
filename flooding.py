class Flooding:
    def flood(self, start_node, neighbors):
        print(f"Flooding from {start_node} to {neighbors}")
        for neighbor in neighbors:
            print(f"Message sent from {start_node} to {neighbor}")
