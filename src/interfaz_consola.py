"""
Interfaz de consola: bucle de turnos jugable por texto.

Ver: CLAUDE.md §6 — "Módulo de interfaz de consola (entrada de órdenes,
     visualización de eventos/estado, bucle de ejecución de N turnos)"
     y tarea.md — "permitir interacción básica (consola...) para ejecutar
     al menos 5 fases (turnos) consecutivas".

Cada turno, cada nación activa ingresa sus órdenes por consola (reclutar,
construir, pillar, mover/atacar, declarar guerra, proponer paz/alianza,
abandonar provincia, disbandar tropas) hasta escribir "fin". Luego se
ejecuta el ciclo WEGO completo (`MotorSimulacionWEGO.ejecutar_ciclo_turno`)
y se muestra el resultado antes de pasar al siguiente turno.
"""

from __future__ import annotations

from .entidades.nacion import Nacion
from .motor.fel import FaseOrden, TipoEvento
from .simulacion import Partida, crear_partida_demo

AYUDA = """
Órdenes disponibles (todas relativas a TU nación):
  reclutar <provincia> <cantidad>        - Recluta soldados (10 oro / 100 soldados).
  muralla <provincia>                    - Construye una muralla (+100% defensa).
  torre <provincia>                      - Construye una torre de vigía.
  pillar <provincia>                     - Pilla la provincia (oro, -15% felicidad, cooldown 12).
  mover <origen> <destino> <cantidad>    - Mueve tropas a una provincia adyacente.
  atacar <origen> <destino> <cantidad>   - Ataca una provincia adyacente enemiga/neutral.
  guerra <id_nacion>                     - Declara la guerra a otra nación.
  paz <id_nacion>                        - Propone un tratado de paz.
  alianza <id_nacion>                    - Propone una alianza.
  cancelar <id_nacion>                   - Cancela la relación vigente (activa ceasefire).
  abandonar <provincia>                  - Abandona una provincia propia.
  disband <provincia> <cantidad>         - Disuelve tropas propias en una provincia.
  estado                                 - Muestra el estado de tu nación.
  ayuda                                  - Muestra esta lista de órdenes.
  fin                                    - Termina tu turno de órdenes.
"""


def imprimir_estado_global(partida: Partida) -> None:
    motor = partida.motor
    print(f"\n===== Turno {motor.turno_actual} =====")
    for nacion in motor.naciones.values():
        estado = "ACTIVA" if nacion.activa else "ELIMINADA"
        print(
            f"  Nación {nacion.id_nacion} [{nacion.nombre}] ({estado}) — "
            f"provincias: {sorted(nacion.provincias)} | oro: {nacion.tesoreria} | "
            f"felicidad prom.: {nacion.felicidad_promedio}% | AP: {nacion.puntos_accion:.2f} | "
            f"puntos victoria: {nacion.puntos_victoria} | guerras activas: {nacion.guerras_activas}"
        )


def imprimir_estado_nacion(partida: Partida, nacion: Nacion) -> None:
    mapa = partida.motor.mapa
    print(f"\n-- Estado de {nacion.nombre} (nación {nacion.id_nacion}) --")
    print(f"Oro: {nacion.tesoreria} | AP: {nacion.puntos_accion:.2f} | Felicidad prom.: {nacion.felicidad_promedio}%")
    for pid in sorted(nacion.provincias):
        p = mapa[pid]
        print(
            f"  Provincia {pid}: pob={p.poblacion} felicidad={p.felicidad}% tropas={p.tropas} "
            f"muralla={p.muralla} torre={p.torre_vigia} cooldown_pillaje={p.cooldown_pillaje} "
            f"vecinos={p.vecinos}"
        )


def _leer_orden_nacion(partida: Partida, nacion: Nacion) -> None:
    motor = partida.motor
    print(f"\n>> Órdenes de {nacion.nombre} (nación {nacion.id_nacion}). Escribe 'ayuda' para ver comandos.")
    while True:
        try:
            entrada = input(f"[{nacion.nombre}] > ").strip()
        except EOFError:
            return
        if not entrada:
            continue

        partes = entrada.split()
        comando = partes[0].lower()

        if comando == "fin":
            return
        if comando == "ayuda":
            print(AYUDA)
            continue
        if comando == "estado":
            imprimir_estado_nacion(partida, nacion)
            continue

        try:
            if comando == "reclutar":
                _, prov, cant = partes
                motor.planificar_orden(FaseOrden.ESTATICA, nacion.id_nacion, TipoEvento.RECLUTAR, origen=int(prov), datos={"cantidad": int(cant)})
            elif comando == "muralla":
                _, prov = partes
                motor.planificar_orden(FaseOrden.ESTATICA, nacion.id_nacion, TipoEvento.CONSTRUIR_MURALLA, origen=int(prov))
            elif comando == "torre":
                _, prov = partes
                motor.planificar_orden(FaseOrden.ESTATICA, nacion.id_nacion, TipoEvento.CONSTRUIR_TORRE, origen=int(prov))
            elif comando == "pillar":
                _, prov = partes
                motor.planificar_orden(FaseOrden.ESTATICA, nacion.id_nacion, TipoEvento.PILLAJE, origen=int(prov))
            elif comando == "mover":
                _, origen, destino, cant = partes
                motor.planificar_orden(FaseOrden.ORDENADA, nacion.id_nacion, TipoEvento.MOVIMIENTO, origen=int(origen), destino=int(destino), datos={"cantidad_tropas": int(cant)})
            elif comando == "atacar":
                _, origen, destino, cant = partes
                motor.planificar_orden(FaseOrden.ORDENADA, nacion.id_nacion, TipoEvento.ATAQUE, origen=int(origen), destino=int(destino), datos={"cantidad_tropas": int(cant)})
            elif comando == "guerra":
                _, objetivo = partes
                motor.planificar_orden(FaseOrden.ORDENADA, nacion.id_nacion, TipoEvento.DECLARAR_GUERRA, origen=0, datos={"objetivo": int(objetivo)})
            elif comando in ("paz", "alianza"):
                _, objetivo = partes
                motor.planificar_orden(FaseOrden.ESTATICA, nacion.id_nacion, TipoEvento.DIPLOMACIA, origen=0, datos={"objetivo": int(objetivo), "tipo_propuesta": comando})
            elif comando == "cancelar":
                _, objetivo = partes
                motor.planificar_orden(FaseOrden.ORDENADA, nacion.id_nacion, TipoEvento.CANCELAR_RELACION, origen=0, datos={"objetivo": int(objetivo)})
            elif comando == "abandonar":
                _, prov = partes
                motor.planificar_orden(FaseOrden.ORDENADA, nacion.id_nacion, TipoEvento.ABANDONAR_PROVINCIA, origen=int(prov))
            elif comando == "disband":
                _, prov, cant = partes
                motor.planificar_orden(FaseOrden.ORDENADA, nacion.id_nacion, TipoEvento.DISBAND, origen=int(prov), datos={"cantidad": int(cant)})
            else:
                print(f"Comando desconocido: '{comando}'. Escribe 'ayuda' para ver la lista.")
                continue
            print("Orden encolada.")
        except ValueError:
            print("Formato de orden inválido. Escribe 'ayuda' para ver la sintaxis correcta.")


def ejecutar_partida_interactiva(nombres_naciones: list[str], num_provincias: int, num_turnos: int) -> None:
    """Bucle principal: recolecta órdenes por consola y ejecuta `num_turnos` ciclos WEGO."""
    partida = crear_partida_demo(nombres_naciones, num_provincias=num_provincias)
    motor = partida.motor

    for _ in range(num_turnos):
        imprimir_estado_global(partida)

        for nacion in list(motor.naciones.values()):
            if nacion.activa:
                _leer_orden_nacion(partida, nacion)

        print(f"\n--- Ejecutando ciclo de fin de turno {motor.turno_actual} ---")
        resultado = motor.ejecutar_ciclo_turno()

        if resultado.partida_finalizada:
            ganador = motor.naciones.get(resultado.ganador)
            nombre_ganador = ganador.nombre if ganador else resultado.ganador
            print(f"\n*** ¡Partida finalizada! Ganadora: {nombre_ganador} (nación {resultado.ganador}) ***")
            return

    print(f"\n--- Fin de la simulación tras {num_turnos} turnos (sin condición de victoria alcanzada) ---")
    imprimir_estado_global(partida)


def main() -> None:
    print("=== Simulador Age of Conquest — Interfaz de Consola ===")
    print(AYUDA)
    ejecutar_partida_interactiva(
        nombres_naciones=["Rojo", "Azul", "Verde"],
        num_provincias=9,
        num_turnos=5,
    )


if __name__ == "__main__":
    main()
