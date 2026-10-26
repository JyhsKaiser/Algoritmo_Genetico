import numpy as np

# =====================================================================
# 1. CONFIGURACIÓN DEL ENTORNO DEL SISTEMA DISTRIBUIDO
# =====================================================================
# Un "Gen" representa una tarea. Un "Alelo" es el nodo al que se asigna.
NUM_GENES = 20                   # Cantidad de tareas/contenedores a balancear.
NUM_ALELOS = 4                   # Cantidad de nodos físicos en el clúster (Ej: 0, 1, 2, 3).
CAPACIDAD_NODOS = np.array([100, 100, 150, 80])       # Capacidad de cómputo de cada nodo.
CARGA_GENES = np.random.randint(5, 25, size=NUM_GENES) # Peso (carga) simulada de cada tarea.

# =====================================================================
# 2. PARÁMETROS DEL ALGORITMO GENÉTICO
# =====================================================================
TAMANO_POBLACION = 40            # Cantidad de cromosomas (soluciones) por generación.
MAX_GENERACIONES = 60            # Condición de parada: número máximo de iteraciones.
PROB_CRUZAMIENTO = 0.8           # Probabilidad (80%) de que dos cromosomas padres se crucen.
PROB_MUTACION = 0.1              # Probabilidad (10%) de que un gen mute (cambie de alelo).

# =====================================================================
# 3. FUNCIONES DEL ALGORITMO GENÉTICO
# =====================================================================

def calcular_fitness_cromosoma(cromosoma):
    """
    Función Objetivo (Fitness).
    Evalúa qué tan buena es la distribución de carga dictada por el cromosoma.
    Buscamos MINIMIZAR la varianza de carga (desbalance) entre los nodos.
    
    Args:
        cromosoma (np.array): Arreglo de genes (asignaciones de tareas a nodos).
    Returns:
        float: Valor de aptitud (fitness). Mayor es mejor.
    """
    carga_por_nodo = np.zeros(NUM_ALELOS)
    
    # Decodificación: Leemos cada gen del cromosoma
    for gen_idx, alelo_nodo in enumerate(cromosoma):
        carga_por_nodo[alelo_nodo] += CARGA_GENES[gen_idx]
    
    # Calculamos el porcentaje de uso de cada nodo según su capacidad física
    uso_relativo = carga_por_nodo / CAPACIDAD_NODOS
    
    # Métrica 1: Desbalance (Varianza). Queremos que todos los nodos trabajen al mismo %
    desbalance = np.var(uso_relativo)
    
    # Métrica 2: Penalización severa si un nodo excede el 100% de su capacidad
    penalizacion_sobrecarga = np.sum(np.maximum(0, uso_relativo - 1.0)) * 10
    
    # Costo total a minimizar
    costo_total = desbalance + penalizacion_sobrecarga
    
    # Invertimos el costo para que el AG maximice el Fitness (1 / 1 + costo)
    aptitud = 1.0 / (1.0 + costo_total)
    return aptitud


def inicializar_poblacion(tamano_poblacion, num_genes, num_alelos):
    """
    Crea la Generación 0 (Población inicial).
    Cada cromosoma se genera asignando aleatoriamente un alelo (nodo) a cada gen (tarea).
    """
    # Matriz bidimensional: Filas = Cromosomas, Columnas = Genes
    poblacion = np.random.randint(0, num_alelos, size=(tamano_poblacion, num_genes))
    return poblacion


def seleccion_por_torneo(poblacion, array_aptitudes, k=3):
    """
    Operador de Selección.
    Elige 'k' cromosomas al azar y hace que "compitan". El que tenga mejor fitness gana
    el derecho a reproducirse. Esto mantiene presión selectiva.
    """
    # Elegimos 'k' índices de cromosomas al azar
    indices_participantes = np.random.choice(len(poblacion), size=k, replace=False)
    
    # Buscamos cuál de los participantes tiene la aptitud más alta
    indice_ganador = indices_participantes[np.argmax(array_aptitudes[indices_participantes])]
    
    # Retornamos una copia del cromosoma ganador para evitar modificar el original
    return poblacion[indice_ganador].copy()


def cruzamiento_un_punto(cromosoma_padre1, cromosoma_padre2):
    """
    Operador de Cruzamiento (Crossover).
    Simula la reproducción sexual intercambiando segmentos de genes entre dos padres
    para generar dos hijos.
    """
    # Verificamos si ocurre el cruzamiento basado en la probabilidad definida
    if np.random.rand() < PROB_CRUZAMIENTO:
        # Elegimos un punto de corte aleatorio en el cromosoma (entre el gen 1 y el penúltimo)
        punto_corte = np.random.randint(1, NUM_GENES - 1)
        
        # El Hijo 1 toma la primera parte del Padre 1 y la segunda del Padre 2
        cromosoma_hijo1 = np.concatenate([cromosoma_padre1[:punto_corte], cromosoma_padre2[punto_corte:]])
        # El Hijo 2 toma la primera parte del Padre 2 y la segunda del Padre 1
        cromosoma_hijo2 = np.concatenate([cromosoma_padre2[:punto_corte], cromosoma_padre1[punto_corte:]])
        
        return cromosoma_hijo1, cromosoma_hijo2
    
    # Si no hay cruzamiento, los hijos son clones exactos de los padres
    return cromosoma_padre1.copy(), cromosoma_padre2.copy()


def mutar_cromosoma(cromosoma, num_alelos):
    """
    Operador de Mutación.
    Introduce variabilidad genética alterando aleatoriamente el alelo de algunos genes.
    Ayuda a evitar que el algoritmo se estanque en óptimos locales.
    """
    # Recorremos cada gen del cromosoma
    for idx_gen in range(NUM_GENES):
        # Lanzamos un dado probabilístico para cada gen
        if np.random.rand() < PROB_MUTACION:
            # Si ocurre mutación, cambiamos la asignación de esa tarea a un nodo aleatorio
            cromosoma[idx_gen] = np.random.randint(0, num_alelos)
            
    return cromosoma


# =====================================================================
# 4. CICLO DE VIDA DEL ALGORITMO GENÉTICO (Bucle Principal)
# =====================================================================
def ejecutar_algoritmo_genetico():
    """
    Orquesta la evolución de la población a través de múltiples generaciones.
    """
    # 1. Crear la primera generación de cromosomas
    poblacion_actual = inicializar_poblacion(TAMANO_POBLACION, NUM_GENES, NUM_ALELOS)
    
    print("Iniciando evolución del Algoritmo Genético...\n")
    
    # 2. Bucle generacional (Evolución)
    for generacion in range(MAX_GENERACIONES):
        
        # Evaluar el fitness de toda la población actual
        aptitudes = np.array([calcular_fitness_cromosoma(cromosoma) for cromosoma in poblacion_actual])
        
        # ELITISMO: Preservar el mejor cromosoma (el individuo más apto) intacto
        indice_mejor_cromosoma = np.argmax(aptitudes)
        mejor_cromosoma_historico = poblacion_actual[indice_mejor_cromosoma].copy()
        
        # Crear la estructura para la siguiente generación
        nueva_poblacion = [mejor_cromosoma_historico]
        
        # 3. Llenar el resto de la nueva población mediante reproducción
        while len(nueva_poblacion) < TAMANO_POBLACION:
            
            # Selección de padres
            padre1 = seleccion_por_torneo(poblacion_actual, aptitudes)
            padre2 = seleccion_por_torneo(poblacion_actual, aptitudes)
            
            # Cruzamiento para generar hijos
            hijo1, hijo2 = cruzamiento_un_punto(padre1, padre2)
            
            # Mutación de los hijos e inserción en la nueva población
            nueva_poblacion.append(mutar_cromosoma(hijo1, NUM_ALELOS))
            
            # Nos aseguramos de no exceder el tamaño de la población al insertar el segundo hijo
            if len(nueva_poblacion) < TAMANO_POBLACION:
                nueva_poblacion.append(mutar_cromosoma(hijo2, NUM_ALELOS))
                
        # 4. Reemplazo generacional
        poblacion_actual = np.array(nueva_poblacion)
        
        # Monitoreo de la convergencia (cada 10 generaciones)
        if generacion % 10 == 0 or generacion == MAX_GENERACIONES - 1:
            print(f"Generación {generacion:02d} | Fitness del mejor cromosoma: {aptitudes[indice_mejor_cromosoma]:.10f}")

    # Retornamos el mejor cromosoma encontrado en la última generación
    aptitudes_finales = np.array([calcular_fitness_cromosoma(cromo) for cromo in poblacion_actual])
    cromosoma_optimo = poblacion_actual[np.argmax(aptitudes_finales)]
    
    return cromosoma_optimo

# =====================================================================
# 5. EJECUCIÓN Y DECODIFICACIÓN DEL MEJOR CROMOSOMA
# =====================================================================
if __name__ == "__main__":
    cromosoma_ganador = ejecutar_algoritmo_genetico()

    print("\n=======================================================")
    print("EL ALGORITMO HA CONVERGIDO. MEJOR CROMOSOMA ENCONTRADO:")
    print(f"Genes: {cromosoma_ganador}")
    print("=======================================================\n")
    
    # Decodificación del cromosoma para interpretar el balanceo físico
    for nodo_id in range(NUM_ALELOS):
        # Encontrar qué genes (tareas) tienen el alelo correspondiente a este nodo
        genes_en_nodo = np.where(cromosoma_ganador == nodo_id)[0]
        
        # Sumar la carga (peso) de esos genes
        carga_total_nodo = np.sum(CARGA_GENES[genes_en_nodo])
        
        capacidad_max = CAPACIDAD_NODOS[nodo_id]
        porcentaje_uso = (carga_total_nodo / capacidad_max) * 100
        
        print(f"[Nodo {nodo_id} - Cap: {capacidad_max}]")
        print(f"  -> Tareas asignadas: {genes_en_nodo.tolist()}")
        print(f"  -> Carga resultante: {carga_total_nodo} ({porcentaje_uso:.1f}% de uso)\n")