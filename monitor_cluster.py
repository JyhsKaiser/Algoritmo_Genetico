import docker

def escanear_nodos_locales():
    # 1. Nos conectamos al motor de Docker local de tu PC
    cliente = docker.from_env()
    
    print("Conectado a Docker. Buscando nodos del clúster...\n")
    
    # 2. Obtenemos la lista de contenedores activos
    nodos_encontrados = []
    for contenedor in cliente.containers.list():
        if contenedor.name.startswith("nodo_"):
            nodos_encontrados.append(contenedor)
            
    # Ordenamos para que salgan en orden: nodo_0, nodo_1...
    nodos_encontrados.sort(key=lambda x: x.name)
    
    if not nodos_encontrados:
        print("No se encontraron nodos. ¿Están corriendo los contenedores?")
        return

    # 3. Extraemos la información real de cada nodo
    capacidades_reales_ram = []
    
    for nodo in nodos_encontrados:
        # Extraemos una "foto" actual de sus estadísticas (stream=False evita un bucle infinito)
        stats = nodo.stats(stream=False)
        
        # La API de Docker devuelve los datos en bytes. Convertimos a Megabytes (MB)
        limite_memoria_mb = stats['memory_stats']['limit'] / (1024 * 1024)
        uso_memoria_mb = stats['memory_stats']['usage'] / (1024 * 1024)
        
        capacidades_reales_ram.append(limite_memoria_mb)
        
        print(f"[{nodo.name.upper()}] - Estado: {nodo.status}")
        print(f"  -> Límite de RAM configurado: {limite_memoria_mb:.1f} MB")
        print(f"  -> RAM actual en uso: {uso_memoria_mb:.2f} MB\n")
        
    print("==================================================")
    print(f"NUEVO ARREGLO CAPACIDAD_NODOS PARA TU ALGORITMO: {capacidades_reales_ram}")
    print("==================================================")

if __name__ == "__main__":
    escanear_nodos_locales()