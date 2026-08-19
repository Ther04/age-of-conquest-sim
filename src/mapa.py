"""
Estructura inicial del mapa: genera las provincias del juego y su adyacencia.

Ver: CLAUDE.md §6 — "No se requiere GUI gráfica ni mapa visual"; el simulador
     solo necesita un grafo lógico de provincias conectadas para poder
     resolver movimiento de tropas, ataques, bloqueo naval y revueltas
     (ver funciones ProvinciaEsFronterizaConEnemigo / SeleccionarVecinaVulnerable
     en la Formalización Cuantitativa).

Este módulo NO calcula economía, felicidad ni combate — solo construye el
estado inicial de las provincias y expone utilidades básicas de adyacencia.
Los módulos de economía y de combate/motor de turnos consumen esta estructura.
"""

from __future__ import annotations

from .entidades.provincia import Provincia
from .parametros import TOTAL_PROVINCES, TOTAL_POPULATION


def crear_mapa_anillo(num_provincias: int = TOTAL_PROVINCES) -> dict[int, Provincia]:
    """
    Crea un mapa lógico simple en topología de anillo: cada provincia `i` es
    vecina de `(i-1)` y `(i+1)` módulo `num_provincias`.

    Es la representación mínima necesaria para resolver adyacencia; no
    pretende representar la geografía real del juego original (el proyecto
    no requiere replicar mapas, ver tarea.md).
    """
    if num_provincias <= 0:
        raise ValueError("num_provincias debe ser mayor a 0")

    poblacion_por_provincia = TOTAL_POPULATION // num_provincias
    mapa: dict[int, Provincia] = {}

    for i in range(num_provincias):
        vecino_izquierda = (i - 1) % num_provincias
        vecino_derecha = (i + 1) % num_provincias
        vecinos = [vecino_izquierda] if num_provincias == 1 else sorted({vecino_izquierda, vecino_derecha})

        mapa[i] = Provincia(
            id_provincia=i,
            poblacion=poblacion_por_provincia,
            felicidad=50,
            comercio_base=10,
            vecinos=vecinos,
        )

    return mapa


def obtener_vecinas(mapa: dict[int, Provincia], id_provincia: int) -> list[Provincia]:
    """Retorna las provincias adyacentes a `id_provincia` dentro de `mapa`."""
    provincia = mapa[id_provincia]
    return [mapa[vecino_id] for vecino_id in provincia.vecinos]


def son_adyacentes(mapa: dict[int, Provincia], id_a: int, id_b: int) -> bool:
    return id_b in mapa[id_a].vecinos
