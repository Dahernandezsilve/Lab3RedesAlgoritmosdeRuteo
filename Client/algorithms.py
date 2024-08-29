import heapq

# Unicamente es necesario el algoritmo de Dijkstra, la lógica de Flooding está internamente en el cliente (router.py)
# De esta manera se puede hacer Link State Routing con Dijkstra y Flooding.
def dijkstra(start_node, end_node, table):
    shortest_paths = {node: float('inf') for node in table}
    shortest_paths[start_node] = 0
    predecessors = {node: None for node in table}
    priority_queue = [(0, start_node)]
    
    while priority_queue:
        current_distance, current_node = heapq.heappop(priority_queue)
        if current_node == end_node:
            break

        if current_distance > shortest_paths.get(current_node, float('inf')):
            continue
        for neighbor, weight in table.get(current_node, {}).get('table',{}).items():
            distance = current_distance + weight
            if distance < shortest_paths[neighbor]:
                shortest_paths[neighbor] = distance
                predecessors[neighbor] = current_node
                heapq.heappush(priority_queue, (distance, neighbor))

    path = []
    current_node = end_node
    while current_node is not None:
        path.insert(0, current_node)
        current_node = predecessors.get(current_node, None)

    if shortest_paths.get(end_node, float('inf')) == float('inf'):
        return None, float('inf')
    
    return path, shortest_paths[end_node]