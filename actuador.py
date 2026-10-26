import docker
import time

def desplegar_cargas():
    cliente = docker.from_env()
    
    # 1. Las tareas que entraron al sistema (peso en MB)
    cargas_tareas_mb = [20, 30, 15, 40, 25]
    
    # 2. El resultado ficticio de tu Algoritmo Genético (Cromosoma Ganador)
    # Tarea 0 -> Nodo 0, Tarea 1 -> Nodo 2, Tarea 2 -> Nodo 1, etc.
    cromosoma_ganador = [0, 2, 1, 2, 3] 
    
    nodos_nombres = ["nodo_0", "nodo_1", "nodo_2", "nodo_3"]
    
    print("=====================================================")
    print(" ORQUESTADOR: Desplegando balanceo de carga en nodos ")
    print("=====================================================\n")

    # 3. Recorremos el cromosoma para aplicar la asignación
    for id_tarea, id_nodo in enumerate(cromosoma_ganador):
        nombre_nodo = nodos_nombres[id_nodo]
        peso_mb = cargas_tareas_mb[id_tarea]
        
        print(f"[*] Asignando Tarea {id_tarea} ({peso_mb} MB) ---> {nombre_nodo.upper()}")
        
        # Construimos el mismo comando que usaste manualmente en el Paso 3
        comando = f"dd if=/dev/zero of=/dev/shm/tarea_{id_tarea} bs=1M count={peso_mb}"
        
        try:
            # Obtenemos el objeto del contenedor y ejecutamos el comando en segundo plano (detach=True)
            contenedor = cliente.containers.get(nombre_nodo)
            contenedor.exec_run(comando, detach=True)
        except docker.errors.NotFound:
            print(f"[ERROR] El contenedor {nombre_nodo} no existe o está apagado.")

    print("\n[ÉXITO] Despliegue completado. Las tareas están corriendo en RAM.")
    print("Ejecuta 'python monitor_cluster.py' para ver el balanceo físico real.")

if __name__ == "__main__":
    desplegar_cargas()