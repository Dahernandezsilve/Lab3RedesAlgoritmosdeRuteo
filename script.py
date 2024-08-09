from linkStateRouting import LinkStateRouting
from config import NODES

# Crear la instancia del enrutamiento de estado de enlace utilizando NODES
lsr = LinkStateRouting(NODES)

# Ejecutar Dijkstra para encontrar los caminos más cortos desde 'A'
shortest_paths = lsr.run_dijkstra('A')
print("Shortest paths from A:", shortest_paths)

# Ejecutar Flooding desde 'A' hacia sus vecinos
neighbors = NODES['A']['neighbors']  # Obtener los vecinos del nodo 'A'
lsr.run_flooding('A', neighbors)
