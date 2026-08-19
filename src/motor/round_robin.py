"""
Algoritmo Round-Robin para el Despacho de Órdenes Ordenadas.

Ver:
- Game Manual, sección "Actions & Events":
  "Sorted Orders are executed using a round robin algorithm with the weakest
  nation in a game moving first. The strongest nation moves last...
  A nation will get all sorted orders executed until a movement/attack event
  is found after which the next nation can execute again..."
- Modelo Conceptual de Simulación - Age of Conquest, sección 9.2:
  "Round-robin de órdenes ordenadas (movimientos/ataques)".
- Formalización Cuantitativa, sección "Algoritmo del Despachador de la LEF".
"""

from __future__ import annotations

from typing import Any, Callable, Optional

from src.motor.fel import Evento, TipoEvento

# Tipos de eventos que provocan la cesión inmediata del turno en el Round-Robin
EVENTOS_DE_CESION = {
    TipoEvento.MOVIMIENTO,
    TipoEvento.ATAQUE,
}


def es_evento_de_cesion(tipo: TipoEvento) -> bool:
    """
    Determina si un tipo de orden cede el turno a la siguiente nación.
    Solo movimientos y ataques provocan la alternancia (Game Manual §Actions & Events).
    """
    return tipo in EVENTOS_DE_CESION


def ejecutar_round_robin(
    ranking_naciones: list[int],
    ordenes: list[Evento],
    ejecutor_orden: Optional[Callable[[Evento], Any]] = None,
) -> list[Evento]:
    """
    Ejecuta las órdenes ordenadas siguiendo el algoritmo Round-Robin regulado
    por el Ranking de Debilidad.

    Parámetros:
    - `ranking_naciones`: Lista de IDs de naciones ordenada de más débil (actúa primero)
      a más fuerte (actúa de último).
    - `ordenes`: Lista de eventos de fase ORDENADA a procesar.
    - `ejecutor_orden`: Función opcional `callback(evento)` que aplica el efecto
      de la orden en el estado del juego al momento de ser despachada.

    Retorna:
    - Lista de `Evento` en el orden cronológico exacto en que fueron ejecutados.
    """
    # 1. Agrupar órdenes por nación en colas FIFO independientes
    colas_por_nacion: dict[int, list[Evento]] = {id_n: [] for id_n in ranking_naciones}
    
    # También aceptar órdenes de naciones que quizás no estén en el ranking explícito
    for orden in ordenes:
        if orden.id_nacion not in colas_por_nacion:
            colas_por_nacion[orden.id_nacion] = []
        colas_por_nacion[orden.id_nacion].append(orden)

    # Asegurar que todas las naciones con órdenes participen en el orden de ranking
    orden_naciones = [n for n in ranking_naciones if n in colas_por_nacion]
    for n in colas_por_nacion:
        if n not in orden_naciones:
            orden_naciones.append(n)

    eventos_ejecutados: list[Evento] = []

    def hay_ordenes_pendientes() -> bool:
        return any(len(cola) > 0 for cola in colas_por_nacion.values())

    # 2. Bucle principal de Round-Robin
    while hay_ordenes_pendientes():
        for id_nacion in orden_naciones:
            cola = colas_por_nacion.get(id_nacion, [])
            if not cola:
                continue

            # La nación ejecuta órdenes hasta encontrar un MOVIMIENTO o ATAQUE
            while cola:
                orden_actual = cola.pop(0)

                # Despachar orden (ejecutar efecto si se proporcionó callback)
                if ejecutor_orden:
                    ejecutor_orden(orden_actual)
                eventos_ejecutados.append(orden_actual)

                # Si es un evento de movimiento o ataque, se cede el turno
                if es_evento_de_cesion(orden_actual.tipo_evento):
                    break

    return eventos_ejecutados
