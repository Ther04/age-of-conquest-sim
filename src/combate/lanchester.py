"""
Submodelo de Resolución de Combate — Ley Lineal de Lanchester Discreta.

Ver:
- Formalización Cuantitativa y Lógica del Sistema - AgeofConquest,
  secciones "Submodelo de Resolución de Combate",
  "Algoritmo de Resolución de Combate Lanchester" y
  "Ejemplo 2: Simulación de Combate en Aritmética Entera".
- Modelo Conceptual de Simulación - Age of Conquest, sección 9.3:
  "Evento de combate".
- Game Manual, sección "Combat".

Reglas clave:
1. Determinista (sin números aleatorios).
2. Aritmética entera en base porcentual (multiplicada por 100).
3. Bonificaciones y penalizaciones aditivas (no multiplicativas):
   - Muralla en defensa: +100%
   - Gobernante atacando: +100%
   - Gobernante defendiendo: +30%
   - Ataque naval sobre tierra / combate naval: -30%
4. Bajas proporcionales enteras con mínimo de 1 superviviente para el ganador.
5. Condición de Jaque Mate: si el gobernante de una nación muere en batalla,
   esa nación queda eliminada de inmediato y transfiere todo su territorio al vencedor.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.entidades.gobernante import Gobernante
from src.entidades.nacion import Nacion
from src.entidades.provincia import Provincia
from src.parametros import (
    BON_RULER_ATK,
    BON_RULER_DEF,
    BON_WALL_DEF,
    PEN_NAVAL_ATK,
)


@dataclass
class ResultadoCombate:
    """Detalle completo del resultado de una resolución de combate."""
    id_provincia: int
    id_nacion_atk: int
    id_nacion_def: int
    ganador: int
    perdedor: int
    fc_atacante: int
    fc_defensor: int
    tropas_iniciales_atk: int
    tropas_iniciales_def: int
    tropas_sobrevivientes: int
    cambio_propietario: bool
    jaque_mate: bool = False
    gobernante_eliminado: Optional[int] = None


def calcular_fuerza_atacante(
    tropas_atk: int,
    gobernante_presente: bool = False,
    es_naval: bool = False,
) -> int:
    """
    Calcula la Fuerza de Combate Efectiva del Atacante (FC_A).
    FC_A = M_atk * (100 + 100 * Bon_ruler_atk * I(rey) - 100 * Pen_naval_atk * IsNaval)
    """
    bono_rey = int(100 * BON_RULER_ATK) if gobernante_presente else 0
    pen_naval = int(100 * PEN_NAVAL_ATK) if es_naval else 0
    multiplicador = 100 + bono_rey - pen_naval
    return tropas_atk * multiplicador


def calcular_fuerza_defensora(
    tropas_def: int,
    tiene_muralla: bool = False,
    gobernante_presente: bool = False,
) -> int:
    """
    Calcula la Fuerza de Combate Efectiva del Defensor (FC_D).
    FC_D = P_M_i * (100 + 100 * Bon_wall_def * P_W_i + 100 * Bon_ruler_def * I(rey))
    """
    bono_muralla = int(100 * BON_WALL_DEF) if tiene_muralla else 0
    bono_rey = int(100 * BON_RULER_DEF) if gobernante_presente else 0
    multiplicador = 100 + bono_muralla + bono_rey
    return tropas_def * multiplicador


def transferir_todas_las_tierras(
    nacion_perdedora: Nacion,
    nacion_ganadora: Nacion,
    mapa: dict[int, Provincia],
) -> None:
    """
    Transfiere todas las provincias restantes de una nación eliminada por Jaque Mate
    a la nación vencedora.
    """
    provincias_a_transferir = list(nacion_perdedora.provincias)
    for prov_id in provincias_a_transferir:
        prov = mapa.get(prov_id)
        if prov:
            prov.propietario = nacion_ganadora.id_nacion
            nacion_ganadora.provincias.add(prov_id)
    nacion_perdedora.provincias.clear()


def resolver_combate(
    provincia: Provincia,
    nacion_atk: Nacion,
    nacion_def: Nacion,
    tropas_atk: int,
    es_naval: bool = False,
    gobernante_atk_presente: bool = False,
    gobernante_def_presente: bool = False,
    gobernante_atk: Optional[Gobernante] = None,
    gobernante_def: Optional[Gobernante] = None,
    mapa: Optional[dict[int, Provincia]] = None,
) -> ResultadoCombate:
    """
    Resuelve el combate en una provincia según la Formalización Cuantitativa.

    Aplica:
    1. Comparación de FC_A vs FC_D en enteros.
    2. Reducción a 0 de las tropas del perdedor.
    3. Cálculo entero de sobrevivientes del bando ganador:
       - Si gana Atacante: max(1, floor(M_atk * (1 - FC_D / FC_A)))
       - Si gana Defensor: max(1, floor(P_M_i * (1 - FC_A / FC_D)))
    4. Ajuste de felicidad nacional (+1% ganador, -1% perdedor).
    5. Condición Jaque Mate: si el rey del bando perdedor estaba en la batalla,
       su nación es eliminada y sus tierras pasan al vencedor.
    """
    if tropas_atk <= 0:
        raise ValueError(f"Las tropas atacantes deben ser mayores a 0: {tropas_atk}")

    tropas_def_iniciales = provincia.tropas

    # 1. Cálculo de fuerzas efectivas en porcentaje entero
    fc_a = calcular_fuerza_atacante(
        tropas_atk=tropas_atk,
        gobernante_presente=gobernante_atk_presente,
        es_naval=es_naval,
    )
    fc_d = calcular_fuerza_defensora(
        tropas_def=tropas_def_iniciales,
        tiene_muralla=provincia.muralla,
        gobernante_presente=gobernante_def_presente,
    )

    jaque_mate = False
    id_gobernante_eliminado: Optional[int] = None

    # 2. Criterio de Victoria: FC_A > FC_D gana el Atacante; de lo contrario gana el Defensor
    if fc_a > fc_d:
        # --- GANA EL ATACANTE ---
        ganador_id = nacion_atk.id_nacion
        perdedor_id = nacion_def.id_nacion
        cambio_propietario = True

        # Cálculo de sobrevivientes atacantes (aritmética entera)
        if fc_d == 0:
            sobrevivientes = tropas_atk
        else:
            # floor(M_atk * (1 - FC_D / FC_A)) = (M_atk * (FC_A - FC_D)) // FC_A
            sobrevivientes = max(1, (tropas_atk * (fc_a - fc_d)) // fc_a)

        # Actualizar provincia y tropas
        provincia.tropas = sobrevivientes
        if provincia.id_provincia in nacion_def.provincias:
            nacion_def.provincias.remove(provincia.id_provincia)
        nacion_atk.provincias.add(provincia.id_provincia)
        provincia.propietario = nacion_atk.id_nacion

        # Ajuste de felicidad nacional (+1% atk, -1% def)
        nacion_atk.felicidad_promedio = min(100, nacion_atk.felicidad_promedio + 1)
        nacion_def.felicidad_promedio = max(0, nacion_def.felicidad_promedio - 1)

        # Condición Jaque Mate: Rey defensor capturado/muerto
        if gobernante_def_presente:
            jaque_mate = True
            nacion_def.gobernante_vivo = False
            nacion_def.activa = False
            if gobernante_def:
                gobernante_def.vivo = False
                id_gobernante_eliminado = gobernante_def.id_gobernante
            if mapa is not None:
                transferir_todas_las_tierras(nacion_def, nacion_atk, mapa)

    else:
        # --- GANA EL DEFENSOR (empate o superioridad defensora) ---
        ganador_id = nacion_def.id_nacion
        perdedor_id = nacion_atk.id_nacion
        cambio_propietario = False

        # Cálculo de sobrevivientes defensores (aritmética entera)
        if fc_a == 0:
            sobrevivientes = tropas_def_iniciales
        else:
            # floor(P_M_i * (1 - FC_A / FC_D)) = (P_M_i * (FC_D - FC_A)) // FC_D
            sobrevivientes = max(1, (tropas_def_iniciales * (fc_d - fc_a)) // fc_d)

        # Actualizar tropas de la provincia defensora
        provincia.tropas = sobrevivientes

        # Ajuste de felicidad nacional (+1% def, -1% atk)
        nacion_def.felicidad_promedio = min(100, nacion_def.felicidad_promedio + 1)
        nacion_atk.felicidad_promedio = max(0, nacion_atk.felicidad_promedio - 1)

        # Condición Jaque Mate: Rey atacante muere/es capturado liderando la invasión
        if gobernante_atk_presente:
            jaque_mate = True
            nacion_atk.gobernante_vivo = False
            nacion_atk.activa = False
            if gobernante_atk:
                gobernante_atk.vivo = False
                id_gobernante_eliminado = gobernante_atk.id_gobernante
            if mapa is not None:
                transferir_todas_las_tierras(nacion_atk, nacion_def, mapa)

    return ResultadoCombate(
        id_provincia=provincia.id_provincia,
        id_nacion_atk=nacion_atk.id_nacion,
        id_nacion_def=nacion_def.id_nacion,
        ganador=ganador_id,
        perdedor=perdedor_id,
        fc_atacante=fc_a,
        fc_defensor=fc_d,
        tropas_iniciales_atk=tropas_atk,
        tropas_iniciales_def=tropas_def_iniciales,
        tropas_sobrevivientes=sobrevivientes,
        cambio_propietario=cambio_propietario,
        jaque_mate=jaque_mate,
        gobernante_eliminado=id_gobernante_eliminado,
    )
