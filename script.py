from linkStateRouting import LinkStateRouting

# Definir la topología del grafo (ejemplo)
graph = {
    'A': {'B': 1, 'C': 4},
    'B': {'A': 1, 'C': 2, 'D': 5},
    'C': {'A': 4, 'B': 2, 'D': 1},
    'D': {'B': 5, 'C': 1}
}

node_tables = graph  # Esta sería la tabla de los demás nodos

# Crear la instancia del enrutamiento de estado de enlace
lsr = LinkStateRouting(node_tables)

# Ejecutar Dijkstra
shortest_paths = lsr.run_dijkstra('A')
print("Shortest paths from A:", shortest_paths)

# Ejecutar Flooding
lsr.run_flooding('A', ['B', 'C', 'D'])
