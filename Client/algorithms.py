import heapq

def dijkstra(start_node, end_node, table):
    # Diccionario para almacenar la distancia más corta desde start_node a cada nodo
    
    shortest_paths = {node: float('inf') for node in table}
    shortest_paths[start_node] = 0
    # Diccionario para almacenar el predecesor de cada nodo en la ruta óptima
    predecessors = {node: None for node in table}

    # Cola de prioridad para explorar los nodos en orden de distancia
    priority_queue = [(0, start_node)]
    
    while priority_queue:
        current_distance, current_node = heapq.heappop(priority_queue)

        # Si llegamos al nodo de destino, rompemos el bucle
        if current_node == end_node:
            break

        # Si la distancia actual es mayor que la ya almacenada, omitimos este nodo
        if current_distance > shortest_paths[current_node]:
            continue

        # Explorar los vecinos del nodo actual
        for neighbor, weight in table[current_node]['table'].items():
            distance = current_distance + weight

            # Si encontramos una ruta más corta al vecino, actualizamos
            if distance < shortest_paths[neighbor]:
                shortest_paths[neighbor] = distance
                predecessors[neighbor] = current_node
                heapq.heappush(priority_queue, (distance, neighbor))

    # Construir la ruta más corta desde el nodo inicio hasta el nodo destino
    path = []
    current_node = end_node
    while current_node is not None:
        path.insert(0, current_node)
        current_node = predecessors[current_node]

    # Si no hay camino válido
    if shortest_paths[end_node] == float('inf'):
        return None, float('inf')
    
    return path, shortest_paths[end_node]