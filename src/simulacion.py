"""
Módulo de integración: arma una partida jugable y conecta todos los
submódulos (entidades, mapa, economía, combate, diplomacia, motor WEGO,
acciones estáticas) al `MotorSimulacionWEGO` mediante handlers.

Ver: CLAUDE.md §6 — "Módulo de interfaz de consola (entrada de órdenes,
     visualización de eventos/estado, bucle de ejecución de N turnos)".

Este módulo no contiene reglas de negocio propias: solo cablea las
funciones ya implementadas por Henyer (economía/población), Ismael
(combate/diplomacia/motor) y las órdenes estáticas de reclutamiento y
construcción, para que el bucle de turnos WEGO ejecute un ciclo completo.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional

from . import economia
from .acciones_estaticas import (
    construir_muralla,
    construir_torre_vigia,
    pillar_provincia,
    reclutar_tropas,
    reducir_cooldowns_pillaje,
)
from .combate.movimiento import ejecutar_movimiento_tropas
from .diplomacia.declaracion_guerra import (
    aplicar_penalizacion_recurrente_guerras,
    declarar_guerra,
)
from .diplomacia.gestor_diplomacia import GestorDiplomacia
from .entidades.gobernante import Gobernante
from .entidades.nacion import Nacion, TipoNacion
from .entidades.provincia import Provincia
from .mapa import crear_mapa_anillo
from .motor.ciclo_wego import MotorSimulacionWEGO, ResultadoTurno
from .motor.fel import FaseOrden, TipoEvento
from .motor.victoria import EvaluadorVictoria, TipoObjetivo


@dataclass
class Partida:
    """Agrupa el estado completo de una partida y el motor que la ejecuta."""
    motor: MotorSimulacionWEGO
    gestor_diplomacia: GestorDiplomacia
    evaluador_victoria: EvaluadorVictoria
    random_generator: random.Random = field(default_factory=random.Random)


def crear_partida_demo(nombres_naciones: list[str], num_provincias: int = 9, semilla: Optional[int] = 42) -> Partida:
    """
    Crea una partida lista para jugar: mapa en anillo, una nación por cada
    nombre en `nombres_naciones` (repartidas equidistantes sobre el anillo,
    cada una con su gobernante en su provincia inicial), y todo el cableado
    de handlers necesario para que `MotorSimulacionWEGO.ejecutar_ciclo_turno()`
    procese un turno completo (estático -> ordenado -> endógeno -> victoria).
    """
    mapa = crear_mapa_anillo(num_provincias)
    naciones: dict[int, Nacion] = {}
    gobernantes: dict[int, Gobernante] = {}

    num_naciones = len(nombres_naciones)
    paso = num_provincias // num_naciones
    for idx, nombre in enumerate(nombres_naciones):
        id_nacion = idx + 1
        provincia_inicial = idx * paso

        nacion = Nacion(
            id_nacion=id_nacion,
            nombre=nombre,
            tipo=TipoNacion.HUMANO,
            tesoreria=100,
            puntos_accion=2.2,
        )
        prov = mapa[provincia_inicial]
        prov.propietario = id_nacion
        prov.tropas = 100
        nacion.provincias.add(provincia_inicial)
        naciones[id_nacion] = nacion

        gobernantes[id_nacion] = Gobernante(
            id_gobernante=id_nacion,
            nacion_propietaria=id_nacion,
            provincia_actual=provincia_inicial,
        )

    gestor_diplomacia = GestorDiplomacia()
    evaluador_victoria = EvaluadorVictoria(objetivo=TipoObjetivo.SUPREMACIA, total_provincias=num_provincias)

    motor = MotorSimulacionWEGO(mapa=mapa, naciones=naciones, gobernantes=gobernantes, turno_inicial=1)
    partida = Partida(motor=motor, gestor_diplomacia=gestor_diplomacia, evaluador_victoria=evaluador_victoria)

    _registrar_handlers_estaticos(partida)
    _registrar_handlers_ordenados(partida)
    _registrar_hooks_fin_turno(partida)
    _registrar_verificador_victoria(partida)

    return partida


# --- Fase 1: Órdenes Estáticas ---

def _registrar_handlers_estaticos(partida: Partida) -> None:
    motor = partida.motor

    def handler_reclutar(evento, motor: MotorSimulacionWEGO) -> None:
        nacion = motor.naciones[evento.id_nacion]
        provincia = motor.mapa[evento.origen]
        resultado = reclutar_tropas(nacion, provincia, evento.datos.get("cantidad", 0))
        print(f"[Turno {evento.turno}] Nación {nacion.nombre}: {resultado.mensaje}")

    def handler_muralla(evento, motor: MotorSimulacionWEGO) -> None:
        nacion = motor.naciones[evento.id_nacion]
        provincia = motor.mapa[evento.origen]
        resultado = construir_muralla(nacion, provincia)
        print(f"[Turno {evento.turno}] Nación {nacion.nombre}: {resultado.mensaje}")

    def handler_torre(evento, motor: MotorSimulacionWEGO) -> None:
        nacion = motor.naciones[evento.id_nacion]
        provincia = motor.mapa[evento.origen]
        resultado = construir_torre_vigia(nacion, provincia)
        print(f"[Turno {evento.turno}] Nación {nacion.nombre}: {resultado.mensaje}")

    def handler_pillaje(evento, motor: MotorSimulacionWEGO) -> None:
        nacion = motor.naciones[evento.id_nacion]
        provincia = motor.mapa[evento.origen]
        resultado = pillar_provincia(nacion, provincia)
        print(f"[Turno {evento.turno}] Nación {nacion.nombre}: {resultado.mensaje}")

    def handler_distribuir_dinero(evento, motor: MotorSimulacionWEGO) -> None:
        nacion = motor.naciones[evento.id_nacion]
        monto = evento.datos.get("monto_por_provincia", 0)
        try:
            economia.realizar_distribuir_dinero_nacion(nacion, motor.mapa, monto)
            print(f"[Turno {evento.turno}] Nación {nacion.nombre}: distribuyó {monto} oro/provincia entre su población.")
        except ValueError as exc:
            print(f"[Turno {evento.turno}] Nación {nacion.nombre}: no se pudo distribuir dinero ({exc}).")

    def handler_festival(evento, motor: MotorSimulacionWEGO) -> None:
        nacion = motor.naciones[evento.id_nacion]
        provincia = motor.mapa[evento.origen]
        try:
            economia.realizar_festival_fertilidad_provincia(nacion, provincia)
            print(f"[Turno {evento.turno}] Nación {nacion.nombre}: celebró festival de fertilidad en provincia {provincia.id_provincia}.")
        except ValueError as exc:
            print(f"[Turno {evento.turno}] Nación {nacion.nombre}: no se pudo celebrar festival ({exc}).")

    def handler_diplomacia(evento, motor: MotorSimulacionWEGO) -> None:
        nacion = motor.naciones[evento.id_nacion]
        objetivo_id = evento.datos.get("objetivo")
        tipo_propuesta = evento.datos.get("tipo_propuesta", "paz")
        if objetivo_id is None or objetivo_id not in motor.naciones:
            print(f"[Turno {evento.turno}] Nación {nacion.nombre}: propuesta diplomática inválida (sin objetivo).")
            return
        if tipo_propuesta == "alianza":
            partida.gestor_diplomacia.establecer_alianza(nacion.id_nacion, objetivo_id, evento.turno)
        elif tipo_propuesta == "protectorado":
            partida.gestor_diplomacia.establecer_protectorado(nacion.id_nacion, objetivo_id, evento.turno)
        else:
            partida.gestor_diplomacia.establecer_paz(nacion.id_nacion, objetivo_id, evento.turno)
        print(f"[Turno {evento.turno}] Nación {nacion.nombre}: propuso '{tipo_propuesta}' a la nación {objetivo_id}.")

    motor.registrar_handler_estatico(TipoEvento.RECLUTAR, handler_reclutar)
    motor.registrar_handler_estatico(TipoEvento.CONSTRUIR_MURALLA, handler_muralla)
    motor.registrar_handler_estatico(TipoEvento.FORTIFICAR, handler_muralla)
    motor.registrar_handler_estatico(TipoEvento.CONSTRUIR_TORRE, handler_torre)
    motor.registrar_handler_estatico(TipoEvento.PILLAJE, handler_pillaje)
    motor.registrar_handler_estatico(TipoEvento.DISTRIBUIR_DINERO, handler_distribuir_dinero)
    motor.registrar_handler_estatico(TipoEvento.FESTIVAL, handler_festival)
    motor.registrar_handler_estatico(TipoEvento.DIPLOMACIA, handler_diplomacia)


# --- Fase 2: Órdenes Ordenadas (Round-Robin) ---

def _registrar_handlers_ordenados(partida: Partida) -> None:
    motor = partida.motor

    def handler_movimiento(evento, motor: MotorSimulacionWEGO) -> None:
        datos = evento.datos
        resultado = ejecutar_movimiento_tropas(
            origen_id=evento.origen,
            destino_id=evento.destino,
            id_nacion=evento.id_nacion,
            cantidad_tropas=datos.get("cantidad_tropas", 0),
            mapa=motor.mapa,
            naciones=motor.naciones,
            gobernantes=motor.gobernantes,
            gestor_diplomacia=partida.gestor_diplomacia,
            es_naval=datos.get("es_naval", False),
            acompanar_gobernante=datos.get("acompanar_gobernante", False),
            modo_open_travel=datos.get("modo_open_travel", False),
        )
        print(f"[Turno {evento.turno}] Nación {evento.id_nacion}: {resultado.mensaje}")

    def handler_declarar_guerra(evento, motor: MotorSimulacionWEGO) -> None:
        objetivo_id = evento.datos.get("objetivo")
        nacion_agresora = motor.naciones.get(evento.id_nacion)
        nacion_objetivo = motor.naciones.get(objetivo_id)
        if not nacion_agresora or not nacion_objetivo:
            print(f"[Turno {evento.turno}] Declaración de guerra inválida.")
            return
        relacion = partida.gestor_diplomacia.obtener_relacion(evento.id_nacion, objetivo_id)
        try:
            resultado = declarar_guerra(
                nacion_agresora=nacion_agresora,
                nacion_objetivo=nacion_objetivo,
                relacion=relacion,
                mapa=motor.mapa,
                declaraciones_en_turno=evento.datos.get("declaraciones_en_turno", 1),
                turno_actual=evento.turno,
            )
            print(f"[Turno {evento.turno}] Nación {nacion_agresora.nombre} declaró la guerra a {nacion_objetivo.nombre} (penalización moral: {resultado['penalizacion_aplicada']}%).")
        except ValueError as exc:
            print(f"[Turno {evento.turno}] No se pudo declarar guerra: {exc}")

    def handler_cancelar_relacion(evento, motor: MotorSimulacionWEGO) -> None:
        objetivo_id = evento.datos.get("objetivo")
        try:
            resultado = partida.gestor_diplomacia.cancelar_relacion(evento.id_nacion, objetivo_id, evento.turno)
            print(f"[Turno {evento.turno}] Nación {evento.id_nacion} canceló su relación con {objetivo_id} (ceasefire: {resultado['ceasefire_turnos']} turnos).")
        except ValueError as exc:
            print(f"[Turno {evento.turno}] No se pudo cancelar la relación: {exc}")

    def handler_abandonar_provincia(evento, motor: MotorSimulacionWEGO) -> None:
        nacion = motor.naciones.get(evento.id_nacion)
        provincia = motor.mapa.get(evento.origen)
        if not nacion or not provincia or provincia.propietario != nacion.id_nacion:
            print(f"[Turno {evento.turno}] Abandono inválido de provincia {evento.origen}.")
            return
        nacion.provincias.discard(provincia.id_provincia)
        provincia.propietario = None
        provincia.tropas = 0
        print(f"[Turno {evento.turno}] Nación {nacion.nombre} abandonó la provincia {provincia.id_provincia}.")

    def handler_disband(evento, motor: MotorSimulacionWEGO) -> None:
        provincia = motor.mapa.get(evento.origen)
        cantidad = evento.datos.get("cantidad", 0)
        if not provincia or provincia.propietario != evento.id_nacion:
            print(f"[Turno {evento.turno}] Disband inválido en provincia {evento.origen}.")
            return
        disbandados = min(provincia.tropas, cantidad)
        provincia.tropas -= disbandados
        print(f"[Turno {evento.turno}] Nación {evento.id_nacion} disbandó {disbandados} soldados en provincia {provincia.id_provincia}.")

    motor.registrar_handler_ordenado(TipoEvento.MOVIMIENTO, handler_movimiento)
    motor.registrar_handler_ordenado(TipoEvento.ATAQUE, handler_movimiento)
    motor.registrar_handler_ordenado(TipoEvento.DECLARAR_GUERRA, handler_declarar_guerra)
    motor.registrar_handler_ordenado(TipoEvento.CANCELAR_RELACION, handler_cancelar_relacion)
    motor.registrar_handler_ordenado(TipoEvento.ABANDONAR_PROVINCIA, handler_abandonar_provincia)
    motor.registrar_handler_ordenado(TipoEvento.DISBAND, handler_disband)


# --- Fase 3: Cálculos Endógenos de Fin de Turno ---

def _registrar_hooks_fin_turno(partida: Partida) -> None:
    motor = partida.motor

    def hook_fin_turno(turno: int, motor: MotorSimulacionWEGO) -> None:
        # Paso 1: Crecimiento de población (una sola vez, sobre todo el mapa).
        economia.crecer_poblacion(motor.mapa)

        relaciones = list(partida.gestor_diplomacia.relaciones.values())
        net_incomes: dict[int, int] = {}
        military_upkeeps: dict[int, int] = {}

        # Paso 2: Ingresos y tesorería, por cada nación activa.
        for id_nacion, nacion in motor.naciones.items():
            if not nacion.activa:
                continue
            _, _, ingreso_bruto = economia.calcular_ingresos(nacion, motor.mapa, turno)
            costo_admin = economia.calcular_costo_administracion(nacion, motor.mapa, ingreso_bruto)
            upkeep = economia.calcular_mantenimiento_militar(nacion, motor.mapa)
            net_income = economia.actualizar_tesoreria_y_ap(nacion, motor.mapa, turno, ingreso_bruto, costo_admin, upkeep)
            net_incomes[id_nacion] = net_income
            military_upkeeps[id_nacion] = upkeep

        # Paso 3: Ajuste de felicidad (impuestos + guerras activas) y desgaste recurrente de guerra.
        for nacion in motor.naciones.values():
            if nacion.activa:
                economia.actualizar_felicidad(nacion, motor.mapa, relaciones)
        aplicar_penalizacion_recurrente_guerras(motor.naciones, motor.mapa)

        # Paso 4: Atrición militar en territorio no aliado (Open Travel).
        economia.aplicar_atricion(motor.mapa, motor.naciones, relaciones, open_travel=True)

        # Paso 5: Revueltas estocásticas.
        economia.evaluar_revueltas(motor.mapa, motor.naciones, list(motor.gobernantes.values()), relaciones, partida.random_generator)

        # Paso 6: Desbande forzoso por bancarrota.
        economia.aplicar_desbande_bancarrota(motor.naciones, motor.mapa, net_incomes, military_upkeeps)

        # Paso 7: Evaluación de eliminación por inanición territorial.
        economia.evaluar_eliminacion_inanicion(motor.naciones)

        # Cooldowns de pillaje y expiración de ceasefires diplomáticos.
        reducir_cooldowns_pillaje(motor.mapa)
        partida.gestor_diplomacia.actualizar_ceasefires_fin_turno()

    motor.registrar_hook_fin_turno(hook_fin_turno)


# --- Fase 4: Verificación de Victoria ---

def _registrar_verificador_victoria(partida: Partida) -> None:
    def verificador(motor: MotorSimulacionWEGO) -> Optional[int]:
        resultado = partida.evaluador_victoria.evaluar(motor.naciones, motor.mapa, motor.turno_actual)
        return resultado.ganador if resultado.hay_ganador() else None

    partida.motor.set_verificador_victoria(verificador)


def ejecutar_n_turnos(partida: Partida, num_turnos: int) -> list[ResultadoTurno]:
    """Ejecuta `num_turnos` ciclos completos WEGO y retorna sus resultados, deteniéndose antes si hay ganador."""
    resultados: list[ResultadoTurno] = []
    for _ in range(num_turnos):
        resultado = partida.motor.ejecutar_ciclo_turno()
        resultados.append(resultado)
        if resultado.partida_finalizada:
            break
    return resultados
