"""
Órdenes Estáticas del turno: Reclutamiento, Construcción, Fortificación y Pillaje.

Ver:
- Game Manual, sección "Actions & Events": "Static Orders are non-interactive
  and are executed first, in any order: recruit troops, build watchtower,
  fortify, pillage, diplomacy/messaging, distribute money, festivals."
- Formalización Cuantitativa y Lógica del Sistema - AgeofConquest,
  parámetros `Cost_recruit`, `Cost_wall` y sección "Submodelo de Atrición,
  Pillaje y Revueltas" (pillaje: oro inmediato, -15% felicidad, cooldown 12
  turnos sin poder reclutar/cobrar impuestos).

Estas órdenes no existían en los submodelos de economía (Henyer) ni de
combate/diplomacia/motor (Ismael) — se implementan aquí como parte de la
integración de la interfaz de consola, ya que el bucle de turnos necesita
un handler ejecutable para cada `TipoEvento` estático de la FEL.
"""

from __future__ import annotations

from dataclasses import dataclass

from .entidades.nacion import Nacion
from .entidades.provincia import Provincia
from .parametros import (
    COST_RECRUIT,
    COST_WALL,
    PILLAGE_COOLDOWN_TURNS,
    PILLAGE_HAPPINESS_PENALTY,
    R_PILLAGE,
)


@dataclass
class ResultadoAccionEstatica:
    """Resultado uniforme de una orden estática, para mostrarla en la consola."""
    exito: bool
    mensaje: str


def reclutar_tropas(nacion: Nacion, provincia: Provincia, cantidad_soldados: int) -> ResultadoAccionEstatica:
    """
    Recluta tropas en una provincia propia, a razón de Cost_recruit oro por cada
    100 soldados (ver parametros.COST_RECRUIT). No se puede reclutar en una
    provincia bajo cooldown de pillaje (Provincia.esta_pillada()).
    """
    if provincia.propietario != nacion.id_nacion:
        return ResultadoAccionEstatica(False, f"La provincia {provincia.id_provincia} no pertenece a la nación {nacion.id_nacion}.")
    if provincia.esta_pillada():
        return ResultadoAccionEstatica(False, f"La provincia {provincia.id_provincia} está en cooldown de pillaje, no puede reclutar.")
    if cantidad_soldados <= 0:
        return ResultadoAccionEstatica(False, "La cantidad de soldados a reclutar debe ser mayor a 0.")

    costo = (cantidad_soldados * COST_RECRUIT) // 100
    costo = max(costo, 1)
    if nacion.tesoreria < costo:
        return ResultadoAccionEstatica(False, f"Oro insuficiente para reclutar {cantidad_soldados} soldados (costo: {costo}, tesorería: {nacion.tesoreria}).")

    nacion.tesoreria -= costo
    provincia.tropas += cantidad_soldados
    return ResultadoAccionEstatica(True, f"Reclutados {cantidad_soldados} soldados en provincia {provincia.id_provincia} por {costo} oro.")


def construir_muralla(nacion: Nacion, provincia: Provincia) -> ResultadoAccionEstatica:
    """Construye una muralla defensiva (+100% defensa, ver Bon_wall_def) en una provincia propia."""
    if provincia.propietario != nacion.id_nacion:
        return ResultadoAccionEstatica(False, f"La provincia {provincia.id_provincia} no pertenece a la nación {nacion.id_nacion}.")
    if provincia.muralla:
        return ResultadoAccionEstatica(False, f"La provincia {provincia.id_provincia} ya tiene muralla.")
    if nacion.tesoreria < COST_WALL:
        return ResultadoAccionEstatica(False, f"Oro insuficiente para construir muralla (costo: {COST_WALL}, tesorería: {nacion.tesoreria}).")

    nacion.tesoreria -= COST_WALL
    provincia.muralla = True
    return ResultadoAccionEstatica(True, f"Muralla construida en provincia {provincia.id_provincia} por {COST_WALL} oro.")


def construir_torre_vigia(nacion: Nacion, provincia: Provincia) -> ResultadoAccionEstatica:
    """
    Construye una torre de vigía (detección temprana de movimientos enemigos
    cercanos). No tiene contraparte cuantitativa exacta en la Formalización más
    allá de su existencia booleana (P_V_i), por lo que se le asigna un costo
    simbólico razonable (mitad del costo de una muralla).
    """
    if provincia.propietario != nacion.id_nacion:
        return ResultadoAccionEstatica(False, f"La provincia {provincia.id_provincia} no pertenece a la nación {nacion.id_nacion}.")
    if provincia.torre_vigia:
        return ResultadoAccionEstatica(False, f"La provincia {provincia.id_provincia} ya tiene torre de vigía.")

    costo_torre = COST_WALL // 2
    if nacion.tesoreria < costo_torre:
        return ResultadoAccionEstatica(False, f"Oro insuficiente para construir torre de vigía (costo: {costo_torre}, tesorería: {nacion.tesoreria}).")

    nacion.tesoreria -= costo_torre
    provincia.torre_vigia = True
    return ResultadoAccionEstatica(True, f"Torre de vigía construida en provincia {provincia.id_provincia} por {costo_torre} oro.")


def pillar_provincia(nacion: Nacion, provincia: Provincia) -> ResultadoAccionEstatica:
    """
    Pilla una provincia propia: otorga oro inmediato proporcional a la población
    (r_pillage), pero penaliza -15% de felicidad e impone un cooldown de 12
    turnos sin poder reclutar ni cobrar impuestos/comercio en esa provincia.
    Ver Formalización Cuantitativa, parámetros R_PILLAGE, PILLAGE_HAPPINESS_PENALTY,
    PILLAGE_COOLDOWN_TURNS.
    """
    if provincia.propietario != nacion.id_nacion:
        return ResultadoAccionEstatica(False, f"La provincia {provincia.id_provincia} no pertenece a la nación {nacion.id_nacion}.")
    if provincia.esta_pillada():
        return ResultadoAccionEstatica(False, f"La provincia {provincia.id_provincia} ya está en cooldown de pillaje.")

    # R_PILLAGE = 0.01 (1/100) => oro = floor(r_pillage * poblacion) = poblacion // 100
    oro_obtenido = provincia.poblacion // 100
    nacion.tesoreria += oro_obtenido
    provincia.felicidad = max(0, provincia.felicidad - PILLAGE_HAPPINESS_PENALTY)
    provincia.cooldown_pillaje = PILLAGE_COOLDOWN_TURNS

    return ResultadoAccionEstatica(
        True,
        f"Provincia {provincia.id_provincia} pillada: +{oro_obtenido} oro, "
        f"-{PILLAGE_HAPPINESS_PENALTY}% felicidad, cooldown {PILLAGE_COOLDOWN_TURNS} turnos.",
    )


def reducir_cooldowns_pillaje(mapa: dict[int, Provincia]) -> None:
    """Hook de fin de turno: decrementa en 1 el cooldown de pillaje de cada provincia."""
    for provincia in mapa.values():
        if provincia.cooldown_pillaje > 0:
            provincia.cooldown_pillaje -= 1
