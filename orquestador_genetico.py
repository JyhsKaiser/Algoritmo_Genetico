import docker
import numpy as np

# =====================================================================
# 1. CONFIGURACIÓN E INTERACCIÓN CON DOCKER
# =====================================================================
cliente_docker = docker.from_env()
NODOS_NOMBRES = ["nodo_0", "nodo_1", "nodo_2", "nodo_3"]
NUM_ALELOS = len(NODOS_NOMBRES)

def limpiar_nodos():
    """Borra las tareas anteriores de la RAM (/dev/shm) para evitar saturación."""
    print("Limpiando memoria de los nodos...")
    for nombre in NODOS_NOMBRES:
        try:
            cliente_docker.containers.get(nombre).exec_run("sh -c 'rm -f /dev/shm/tarea_*'", detach=True)
        except docker.errors.NotFound:
            pass

def obtener_capacidades_reales():
    """Lee el límite de RAM real de cada contenedor en MB."""
    capacidades = []
    for nombre in NODOS_NOMBRES:
        contenedor = cliente_docker.containers.get(nombre)
        stats = contenedor.stats(stream=False)
        limite_mb = stats['memory_stats']['limit'] / (1024 * 1024)
        capacidades.append(limite_mb)
    return np.array(capacidades)

# =====================================================================
# 2. PARÁMETROS DEL PROBLEMA Y DEL ALGORITMO
# =====================================================================
# Leemos las capacidades DIRECTO desde Docker, ya no son inventadas
CAPACIDAD_NODOS = obtener_capacidades_reales()

NUM_GENES = 15  # 15 tareas a procesar
# Generamos 15 tareas aleatorias con un peso de entre 5 MB y 15 MB
CARGA_GENES = np.random.randint(5, 15, size=NUM_GENES) 

TAMANO_POBLACION = 40
MAX_GENERACIONES = 50
PROB_CRUZAMIENTO = 0.8
PROB_MUTACION = 0.1

# =====================================================================
# 3. LÓGICA DEL ALGORITMO GENÉTICO (Tu código original)
# =====================================================================
def calcular_fitness_cromosoma(cromosoma):
    carga_por_nodo = np.zeros(NUM_ALELOS)
    for gen_idx, alelo_nodo in enumerate(cromosoma):
        carga_por_nodo[alelo_nodo] += CARGA_GENES[gen_idx]
    
    uso_relativo = carga_por_nodo / CAPACIDAD_NODOS
    desbalance = np.var(uso_relativo)
    penalizacion_sobrecarga = np.sum(np.maximum(0, uso_relativo - 1.0)) * 10
    
    return 1.0 / (1.0 + desbalance + penalizacion_sobrecarga)

def inicializar_poblacion():
    return np.random.randint(0, NUM_ALELOS, size=(TAMANO_POBLACION, NUM_GENES))

def seleccion_por_torneo(poblacion, aptitudes, k=3):
    indices = np.random.choice(len(poblacion), size=k, replace=False)
    return poblacion[indices[np.argmax(aptitudes[indices])]].copy()

def mutar_cromosoma(cromosoma):
    for i in range(NUM_GENES):
        if np.random.rand() < PROB_MUTACION:
            cromosoma[i] = np.random.randint(0, NUM_ALELOS)
    return cromosoma

def ejecutar_ag():
    poblacion = inicializar_poblacion()
    print("\nCalculando balanceo óptimo...")
    
    for gen in range(MAX_GENERACIONES):
        aptitudes = np.array([calcular_fitness_cromosoma(c) for c in poblacion])
        mejor_actual = poblacion[np.argmax(aptitudes)].copy()
        nueva_poblacion = [mejor_actual]
        
        while len(nueva_poblacion) < TAMANO_POBLACION:
            p1 = seleccion_por_torneo(poblacion, aptitudes)
            p2 = seleccion_por_torneo(poblacion, aptitudes)
            
            # Cruzamiento
            if np.random.rand() < PROB_CRUZAMIENTO:
                corte = np.random.randint(1, NUM_GENES - 1)
                h1 = np.concatenate([p1[:corte], p2[corte:]])
                h2 = np.concatenate([p2[:corte], p1[corte:]])
            else:
                h1, h2 = p1.copy(), p2.copy()
                
            nueva_poblacion.append(mutar_cromosoma(h1))
            if len(nueva_poblacion) < TAMANO_POBLACION:
                nueva_poblacion.append(mutar_cromosoma(h2))
                
        poblacion = np.array(nueva_poblacion)
        
    aptitudes_finales = np.array([calcular_fitness_cromosoma(c) for c in poblacion])
    return poblacion[np.argmax(aptitudes_finales)]

# =====================================================================
# 4. DESPLIEGUE EN LA INFRAESTRUCTURA (Actuador)
# =====================================================================
if __name__ == "__main__":
    limpiar_nodos()
    
    print(f"Capacidades Físicas Detectadas: {CAPACIDAD_NODOS} MB")
    print(f"Tareas a procesar (MB): {CARGA_GENES}")
    
    # 1. La IA toma la decisión
    cromosoma_ganador = ejecutar_ag()
    print(f"\nDecisión del AG (Cromosoma): {cromosoma_ganador}\n")
    
    # 2. Despliegue automático
    print("Inyectando cargas a los contenedores...")
    for id_tarea, id_nodo in enumerate(cromosoma_ganador):
        nombre_nodo = NODOS_NOMBRES[id_nodo]
        peso_mb = CARGA_GENES[id_tarea]
        comando = f"dd if=/dev/zero of=/dev/shm/tarea_{id_tarea} bs=1M count={peso_mb}"
        cliente_docker.containers.get(nombre_nodo).exec_run(comando, detach=True)
        
    print("[ÉXITO] Clúster balanceado. Ejecuta 'python monitor_cluster.py' o 'docker stats' para verificar.")