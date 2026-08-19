"""
Submodelo de Movimiento de Tropas, Ataques y Bloqueo Naval.

Ver:
- Game Manual, sección "Troops":
  "For standard type games, troops can be moved on your own territory, enemy provinces
   and water only. Ships cannot pass through enemy positions allowing ship blockades.
   If a ship encounters enemy vessels, a decisive battle will take place. Ship movement
   will stop at the location the battle took place (if victorious).
   If 'Open Travel' is selected, troops can be moved onto any territory..."
- Modelo Conceptual de Simulación - Age of Conquest, secciones 4.3, 5.1 y 9.2.
- Formalización Cuantitativa, secciones "Variables Auxiliares (IsNaval)" y
  "Actualización General de Tropas Militares (P_M_i)".
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.combate.lanchester import ResultadoCombate, resolver_combate
from src.diplomacia.gestor_diplomacia import GestorDiplomacia
from src.entidades.gobernante import Gobernante
from src.entidades.nacion import Nacion
from src.entidades.provincia import Provincia
from src.mapa import son_adyacentes


@dataclass
class ResultadoMovimiento:
    """Detalle del resultado de una orden de movimiento o ataque de tropas."""
    origen: int
    destino: int
    id_nacion: int
    cantidad_tropas: int
    es_naval: bool
    exito: bool
    hubo_combate: bool = False
    resultado_combate: Optional[ResultadoCombate] = None
    movimiento_detenido: bool = False
    mensaje: str = ""


def ejecutar_movimiento_tropas(
    origen_id: int,
    destino_id: int,
    id_nacion: int,
    cantidad_tropas: int,
    mapa: dict[int, Provincia],
    naciones: dict[int, Nacion],
    gobernantes: Optional[dict[int, Gobernante]] = None,
    gestor_diplomacia: Optional[GestorDiplomacia] = None,
    es_naval: bool = False,
    acompanar_gobernante: bool = False,
    modo_open_travel: bool = False,
) -> ResultadoMovimiento:
    """
    Ejecuta una orden de movimiento o ataque entre dos provincias adyacentes.

    Valida:
    1. Existencia y adyacencia geográfica de las provincias (`mapa.py`).
    2. Disponibilidad de tropas suficientes en la provincia origen.
    3. Permisos de tránsito según el modo (Estándar vs Open Travel) y diplomacia.

    Efectos:
    - En territorio propio: transferencia pacífica de tropas.
    - En territorio neutral desocupado: ocupación territorial inmediata.
    - En territorio enemigo / ocupado hostil: resolución de combate Lanchester.
    - Bloqueo naval: si una flota intercepta una posición enemiga, se combate y el
      movimiento se detiene en dicha provincia si vence.
    """
    gobernantes = gobernantes or {}
    gestor_diplomacia = gestor_diplomacia or GestorDiplomacia()

    prov_origen = mapa.get(origen_id)
    prov_destino = mapa.get(destino_id)
    nacion_actora = naciones.get(id_nacion)

    if not prov_origen or not prov_destino or not nacion_actora:
        return ResultadoMovimiento(
            origen=origen_id,
            destino=destino_id,
            id_nacion=id_nacion,
            cantidad_tropas=cantidad_tropas,
            es_naval=es_naval,
            exito=False,
            mensaje="Provincia origen, destino o nación no encontrada en el estado de la simulación.",
        )

    # 1. Validar adyacencia
    if not son_adyacentes(mapa, origen_id, destino_id):
        return ResultadoMovimiento(
            origen=origen_id,
            destino=destino_id,
            id_nacion=id_nacion,
            cantidad_tropas=cantidad_tropas,
            es_naval=es_naval,
            exito=False,
            mensaje=f"Las provincias {origen_id} y {destino_id} no son adyacentes.",
        )

    # 2. Validar propiedad y tropas en origen
    if prov_origen.propietario != id_nacion:
        return ResultadoMovimiento(
            origen=origen_id,
            destino=destino_id,
            id_nacion=id_nacion,
            cantidad_tropas=cantidad_tropas,
            es_naval=es_naval,
            exito=False,
            mensaje=f"La nación {id_nacion} no es propietaria de la provincia origen {origen_id}.",
        )

    if cantidad_tropas <= 0 or cantidad_tropas > prov_origen.tropas:
        return ResultadoMovimiento(
            origen=origen_id,
            destino=destino_id,
            id_nacion=id_nacion,
            cantidad_tropas=cantidad_tropas,
            es_naval=es_naval,
            exito=False,
            mensaje=f"Cantidad de tropas inválida ({cantidad_tropas}); disponibles: {prov_origen.tropas}.",
        )

    # Deducir tropas del origen
    prov_origen.tropas -= cantidad_tropas

    # Comprobar presencia del gobernante
    gobernante_actor = gobernantes.get(id_nacion)
    gobernante_presente = (
        acompanar_gobernante
        and gobernante_actor is not None
        and gobernante_actor.esta_en(origen_id)
    )

    # 3. Evaluar destino según propietario
    dueno_destino_id = prov_destino.propietario

    # Caso A: Territorio propio
    if dueno_destino_id == id_nacion:
        prov_destino.tropas += cantidad_tropas
        if gobernante_presente and gobernante_actor:
            gobernante_actor.provincia_actual = destino_id
        return ResultadoMovimiento(
            origen=origen_id,
            destino=destino_id,
            id_nacion=id_nacion,
            cantidad_tropas=cantidad_tropas,
            es_naval=es_naval,
            exito=True,
            mensaje=f"Desplazamiento pacífico de {cantidad_tropas} soldados a territorio propio.",
        )

    # Caso B: Provincia Neutral (sin dueño)
    if dueno_destino_id is None:
        if prov_destino.tropas == 0:
            # Ocupación pacífica de provincia neutral deshabitada militarmente
            prov_destino.propietario = id_nacion
            prov_destino.tropas = cantidad_tropas
            nacion_actora.provincias.add(destino_id)
            if gobernante_presente and gobernante_actor:
                gobernante_actor.provincia_actual = destino_id
            return ResultadoMovimiento(
                origen=origen_id,
                destino=destino_id,
                id_nacion=id_nacion,
                cantidad_tropas=cantidad_tropas,
                es_naval=es_naval,
                exito=True,
                mensaje=f"Ocupación de provincia neutral {destino_id}.",
            )
        else:
            # Provincia neutral con guarnición rebelde / independiente -> combate
            nacion_defensora_dummy = Nacion(id_nacion=0, nombre="Neutral", provincias={destino_id})
            res_combate = resolver_combate(
                provincia=prov_destino,
                nacion_atk=nacion_actora,
                nacion_def=nacion_defensora_dummy,
                tropas_atk=cantidad_tropas,
                es_naval=es_naval,
                gobernante_atk_presente=gobernante_presente,
                gobernante_atk=gobernante_actor,
                mapa=mapa,
            )
            if res_combate.ganador == id_nacion and gobernante_presente and gobernante_actor:
                gobernante_actor.provincia_actual = destino_id
            return ResultadoMovimiento(
                origen=origen_id,
                destino=destino_id,
                id_nacion=id_nacion,
                cantidad_tropas=cantidad_tropas,
                es_naval=es_naval,
                exito=True,
                hubo_combate=True,
                resultado_combate=res_combate,
                movimiento_detenido=es_naval,
                mensaje=f"Combate en provincia neutral {destino_id}: Ganador Nación {res_combate.ganador}.",
            )

    # Caso C: Territorio de otra nación
    nacion_defensora = naciones.get(dueno_destino_id)
    if not nacion_defensora:
        prov_origen.tropas += cantidad_tropas  # Revertir
        return ResultadoMovimiento(
            origen=origen_id,
            destino=destino_id,
            id_nacion=id_nacion,
            cantidad_tropas=cantidad_tropas,
            es_naval=es_naval,
            exito=False,
            mensaje=f"Nación defensora {dueno_destino_id} no encontrada.",
        )

    # Validar modo estándar vs Open Travel
    estan_en_guerra = gestor_diplomacia.estan_en_guerra(id_nacion, dueno_destino_id)
    son_aliados = gestor_diplomacia.son_aliados(id_nacion, dueno_destino_id)

    if not modo_open_travel and not estan_en_guerra:
        # En modo estándar solo se puede entrar a territorio enemigo (en guerra) o propio
        prov_origen.tropas += cantidad_tropas  # Revertir tropas
        return ResultadoMovimiento(
            origen=origen_id,
            destino=destino_id,
            id_nacion=id_nacion,
            cantidad_tropas=cantidad_tropas,
            es_naval=es_naval,
            exito=False,
            mensaje=f"No se puede ingresar a territorio de nación {dueno_destino_id} sin estar en GUERRA (Modo Estándar).",
        )

    if son_aliados and modo_open_travel:
        # Tránsito amistoso en Open Travel
        prov_destino.tropas += cantidad_tropas
        if gobernante_presente and gobernante_actor:
            gobernante_actor.provincia_actual = destino_id
        return ResultadoMovimiento(
            origen=origen_id,
            destino=destino_id,
            id_nacion=id_nacion,
            cantidad_tropas=cantidad_tropas,
            es_naval=es_naval,
            exito=True,
            mensaje=f"Tránsito por territorio aliado en Open Travel (sin atrición).",
        )

    # Caso D: Ataque / Combate hostil
    gobernante_def = gobernantes.get(dueno_destino_id)
    gobernante_def_presente = (
        gobernante_def is not None
        and gobernante_def.esta_en(destino_id)
    )

    res_combate = resolver_combate(
        provincia=prov_destino,
        nacion_atk=nacion_actora,
        nacion_def=nacion_defensora,
        tropas_atk=cantidad_tropas,
        es_naval=es_naval,
        gobernante_atk_presente=gobernante_presente,
        gobernante_def_presente=gobernante_def_presente,
        gobernante_atk=gobernante_actor,
        gobernante_def=gobernante_def,
        mapa=mapa,
    )

    if res_combate.ganador == id_nacion and gobernante_presente and gobernante_actor:
        gobernante_actor.provincia_actual = destino_id

    return ResultadoMovimiento(
        origen=origen_id,
        destino=destino_id,
        id_nacion=id_nacion,
        cantidad_tropas=cantidad_tropas,
        es_naval=es_naval,
        exito=True,
        hubo_combate=True,
        resultado_combate=res_combate,
        movimiento_detenido=es_naval and res_combate.ganador == id_nacion,
        mensaje=f"Combate resuelto en {destino_id}: Victoria de Nación {res_combate.ganador} (Jaque Mate: {res_combate.jaque_mate}).",
    )
