"""
Cálculo del Ranking de Debilidad de Naciones para el algoritmo Round-Robin.

Ver:
- Game Manual, sección "Actions & Events":
  "Sorted Orders are executed using a round robin algorithm with the weakest
  nation in a game moving first. The strongest nation moves last. Standings
  are generally based on number of provinces, but troop counts, economy may
  also be considered..."
- Modelo Conceptual de Simulación - Age of Conquest, sección 4.1 y 9.1:
  "recalcularRanking(): determina orden round-robin según provincias/tropas/economía."
- Formalización Cuantitativa, sección "Fundamentos de Simulación en Modo WEGO".
"""

from __future__ import annotations

from typing import Optional

from src.entidades.nacion import Nacion
from src.entidades.provincia import Provincia


def calcular_tropas_totales_nacion(nacion: Nacion, mapa: dict[int, Provincia]) -> int:
    """Calcula la sumatoria de tropas en todas las provincias de una nación."""
    total = 0
    for prov_id in nacion.provincias:
        prov = mapa.get(prov_id)
        if prov and prov.propietario == nacion.id_nacion:
            total += prov.tropas
    return total


def calcular_puntaje_fuerza_nacion(nacion: Nacion, mapa: dict[int, Provincia]) -> tuple[int, int, int, int]:
    """
    Retorna una tupla representativa de la fuerza de una nación:
    (número_provincias, tropas_totales, tesoreria, id_nacion)

    Se usa para ordenar: valores menores indican mayor debilidad.
    """
    num_provincias = len(nacion.provincias)
    tropas_totales = calcular_tropas_totales_nacion(nacion, mapa)
    tesoreria = nacion.tesoreria
    return (num_provincias, tropas_totales, tesoreria, nacion.id_nacion)


def calcular_ranking_debilidad(
    naciones: dict[int, Nacion],
    mapa: dict[int, Provincia],
    solo_activas: bool = True,
) -> list[int]:
    """
    Calcula el ranking de debilidad de las naciones.

    Retorna una lista ordenada de `id_nacion` donde:
    - Índice 0 = Nación más débil (prioridad 1 en Round-Robin, ejecuta primero).
    - Último índice = Nación más fuerte (ejecuta de último).

    Criterios de ordenamiento (de menor a mayor fuerza):
    1. Cantidad de provincias bajo su control.
    2. Cantidad total de tropas desplegadas.
    3. Tesorería acumulada.
    4. ID de nación (desempate determinista).
    """
    candidatas: list[Nacion] = []
    for nacion in naciones.values():
        if solo_activas and not nacion.activa:
            continue
        candidatas.append(nacion)

    # Ordenar de menor a mayor fuerza (la más débil queda primero)
    candidatas_ordenadas = sorted(
        candidatas,
        key=lambda n: calcular_puntaje_fuerza_nacion(n, mapa),
    )

    return [n.id_nacion for n in candidatas_ordenadas]


def asignar_prioridades_ranking(
    naciones: dict[int, Nacion],
    mapa: dict[int, Provincia],
) -> dict[int, int]:
    """
    Mapea cada `id_nacion` a su número de prioridad en el ranking (1 = más débil).
    Este valor se asigna al campo `prioridad_nacion` de los eventos en la FEL.
    """
    ranking = calcular_ranking_debilidad(naciones, mapa, solo_activas=False)
    prioridades: dict[int, int] = {}
    for posicion, id_nacion in enumerate(ranking, start=1):
        prioridades[id_nacion] = posicion
    return prioridades
