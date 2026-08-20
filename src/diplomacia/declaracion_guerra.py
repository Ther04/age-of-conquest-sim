"""
Submodelo de Declaración de Guerra y Penalizaciones de Felicidad.

Ver:
- Formalización Cuantitativa y Lógica del Sistema - AgeofConquest,
  secciones "Paso 3: Decaimiento y Ajuste de Moral/Felicidad" y
  "Función de Penalización por Declaración de Guerra".
- Modelo Conceptual de Simulación - Age of Conquest, sección 9.4:
  "Evento de declaración de guerra (con cálculo de felicidad)".
- Game Manual, sección "Diplomacy".

Reglas clave:
1. No se puede declarar guerra si ya existe una relación activa distinta a NEUTRAL,
   o si hay un Ceasefire activo (debe cancelarse primero).
2. Penalización instantánea a la nación agresora:
   N_F_war_pen = Pen_war_decl (-4) + (Pen_war_active (-8) * N_W_active_rival) + Pen_war_multi (-10 si declaraciones > 1)
   Se descuenta inmediatamente de la felicidad de sus provincias y de su promedio nacional.
3. La nación atacada (objetivo) NO recibe penalización moral por ser atacada.
4. Penalización recurrente por turno:
   max(Pen_war_recur_cap (-3), Pen_war_recur (-1) * N_W_active) por cada turno en guerra.
"""

from __future__ import annotations

from typing import Any, Optional

from src.entidades.nacion import Nacion
from src.entidades.provincia import Provincia
from src.entidades.relacion_diplomatica import RelacionDiplomatica, TipoRelacion
from src.parametros import (
    PEN_WAR_ACTIVE,
    PEN_WAR_DECL,
    PEN_WAR_MULTI,
    PEN_WAR_RECUR,
    PEN_WAR_RECUR_CAP,
)


def calcular_penalizacion_declaracion_guerra(
    guerras_activas_rival: int,
    es_multiguerra: bool = False,
) -> int:
    """
    Calcula la penalización instantánea de felicidad para la nación agresora:
    N_F_war_pen = Pen_war_decl + (Pen_war_active * N_W_active_rival) + (Pen_war_multi if es_multiguerra else 0)
    """
    penalizacion = PEN_WAR_DECL + (PEN_WAR_ACTIVE * guerras_activas_rival)
    if es_multiguerra:
        penalizacion += PEN_WAR_MULTI
    return penalizacion


def calcular_penalizacion_recurrente_guerra(guerras_activas_nacion: int) -> int:
    """
    Calcula la penalización recurrente por turno de guerra (tope -3%):
    P_F_war_effect = max(Pen_war_recur_cap, Pen_war_recur * N_W_active)
    """
    if guerras_activas_nacion <= 0:
        return 0
    return max(PEN_WAR_RECUR_CAP, PEN_WAR_RECUR * guerras_activas_nacion)


def declarar_guerra(
    nacion_agresora: Nacion,
    nacion_objetivo: Nacion,
    relacion: RelacionDiplomatica,
    mapa: dict[int, Provincia],
    declaraciones_en_turno: int = 1,
    turno_actual: int = 1,
) -> dict[str, Any]:
    """
    Ejecuta una declaración de guerra formal entre dos naciones.

    Valida:
    - Que la relación sea NEUTRAL y sin ceasefire pendiente.

    Aplica:
    - Cambio de relación a GUERRA.
    - Incremento del contador de guerras activas en ambas naciones.
    - Penalización instantánea de felicidad sobre las provincias de la nación agresora.
    """
    if relacion.tipo != TipoRelacion.NEUTRAL:
        raise ValueError(
            f"No se puede declarar guerra con relación '{relacion.tipo.value}'. "
            "Debe cancelarse la relación primero (genera un ceasefire)."
        )

    if relacion.turnos_ceasefire_restante > 0:
        raise ValueError(
            f"No se puede declarar guerra durante un ceasefire activo "
            f"({relacion.turnos_ceasefire_restante} turnos restantes)."
        )

    # 1. Calcular penalización instantánea
    es_multiguerra = declaraciones_en_turno > 1
    penalizacion = calcular_penalizacion_declaracion_guerra(
        guerras_activas_rival=nacion_objetivo.guerras_activas,
        es_multiguerra=es_multiguerra,
    )

    # 2. Transición diplomática a GUERRA
    relacion.tipo = TipoRelacion.GUERRA
    relacion.turno_inicio = turno_actual
    relacion.turnos_ceasefire_restante = 0

    nacion_agresora.guerras_activas += 1
    nacion_objetivo.guerras_activas += 1

    # 3. Aplicar penalización de moral a la nación agresora (provincias y promedio)
    for prov_id in nacion_agresora.provincias:
        prov = mapa.get(prov_id)
        if prov:
            prov.felicidad = max(0, min(100, prov.felicidad + penalizacion))

    nacion_agresora.felicidad_promedio = max(0, min(100, nacion_agresora.felicidad_promedio + penalizacion))

    return {
        "agresor": nacion_agresora.id_nacion,
        "objetivo": nacion_objetivo.id_nacion,
        "penalizacion_aplicada": penalizacion,
        "guerras_agresor": nacion_agresora.guerras_activas,
        "guerras_objetivo": nacion_objetivo.guerras_activas,
        "turno": turno_actual,
    }


def aplicar_penalizacion_recurrente_guerras(
    naciones: dict[int, Nacion],
    mapa: dict[int, Provincia],
) -> None:
    """
    Hook de fin de turno (Paso 3 de la Formalización Cuantitativa):
    Aplica el desgaste recurrente de felicidad a todas las naciones con guerras activas.
    """
    for nacion in naciones.values():
        if not nacion.activa or nacion.guerras_activas <= 0:
            continue

        pen_recurrente = calcular_penalizacion_recurrente_guerra(nacion.guerras_activas)
        if pen_recurrente != 0:
            for prov_id in nacion.provincias:
                prov = mapa.get(prov_id)
                if prov:
                    prov.felicidad = max(0, min(100, prov.felicidad + pen_recurrente))
            nacion.felicidad_promedio = max(0, min(100, nacion.felicidad_promedio + pen_recurrente))
