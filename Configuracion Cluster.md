# Laboratorio: Simulación de Clúster Distribuido Heterogéneo en una Sola PC con Docker

## 1. Objetivo

Configurar un entorno de pruebas local utilizando contenedores Docker para simular nodos con capacidades de hardware heterogéneas (CPU y RAM diferenciadas), el cual servirá como infraestructura objetivo para un algoritmo genético de balanceo de carga.

---

## 2. Configuración de la Infraestructura Virtual (Nodos)

Se levantaron 4 contenedores ligeros basados en Alpine Linux, aplicando restricciones estrictas de recursos mediante las banderas nativas de Docker (`--cpus` y `-m`).

### Comandos de Despliegue:

```bash
# Nodo 0: Capacidad media (0.5 CPUs, 100 MB RAM)
docker run -d --name nodo_0 --cpus="0.5" -m 100m alpine sleep infinity

# Nodo 1: Capacidad media (0.5 CPUs, 100 MB RAM)
docker run -d --name nodo_1 --cpus="0.5" -m 100m alpine sleep infinity

# Nodo 2: Nodo principal / de mayor capacidad (1.0 CPU, 150 MB RAM)
docker run -d --name nodo_2 --cpus="1.0" -m 150m alpine sleep infinity

# Nodo 3: Nodo de menor capacidad (0.3 CPUs, 80 MB RAM)
docker run -d --name nodo_3 --cpus="0.3" -m 80m alpine sleep infinity
```

docker stats

## 4. Paso 2: Conexión del Orquestador (Python) con Docker Engine

Se implementó un script en Python utilizando la librería SDK `docker` para comunicarse directamente con el daemon local de Docker, inspeccionar los contenedores activos y extraer la métrica de memoria RAM real asignada a cada nodo.

### Instalación de Dependencias:

```bash
pip install docker

```

---

## 5. Paso 3: Inyección de Carga Real a los Contenedores

Para simular la ejecución de tareas (`CARGA_GENES`) sin depender de software de terceros dentro de los nodos, se utilizó el sistema de archivos temporal `/dev/shm` nativo de Linux, el cual almacena datos directamente en la memoria RAM.

### Comandos de Inyección de Carga (Stress Testing):

```bash
# Simular una tarea de 50 MB asignada al nodo_2
docker exec nodo_2 dd if=/dev/zero of=/dev/shm/carga_tarea_1 bs=1M count=50

# Simular una tarea de 20 MB asignada al nodo_0
docker exec nodo_0 dd if=/dev/zero of=/dev/shm/carga_tarea_2 bs=1M count=20

# Liberacion de carga
docker exec nodo_2 rm /dev/shm/carga_tarea_1
docker exec nodo_0 rm /dev/shm/carga_tarea_2
```

## 6. Paso 4: Automatización del Despliegue (El Actuador)

Se desarrolló el componente "Actuador" del orquestador, el cual sirve de puente entre la decisión matemática del Algoritmo Genético y la infraestructura de contenedores.

Este script toma un cromosoma (arreglo de asignaciones) y utiliza la librería `docker` de Python para inyectar dinámicamente las cargas de memoria correspondientes a cada nodo, sin intervención manual.

### Código de Implementación (`actuador.py`):

```python
import docker

def desplegar_cargas():
    cliente = docker.from_env()

    cargas_tareas_mb = [20, 30, 15, 40, 25] # Pesos en MB
    cromosoma_ganador = [0, 2, 1, 2, 3]     # IDs de nodos asignados
    nodos_nombres = ["nodo_0", "nodo_1", "nodo_2", "nodo_3"]

    for id_tarea, id_nodo in enumerate(cromosoma_ganador):
        nombre_nodo = nodos_nombres[id_nodo]
        peso_mb = cargas_tareas_mb[id_tarea]

        comando = f"dd if=/dev/zero of=/dev/shm/tarea_{id_tarea} bs=1M count={peso_mb}"

        contenedor = cliente.containers.get(nombre_nodo)
        contenedor.exec_run(comando, detach=True)

if __name__ == "__main__":
    desplegar_cargas()
```
