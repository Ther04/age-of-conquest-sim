"""
Interfaz de consola: bucle de turnos jugable por texto con validación temprana interactiva.

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
from .simulacion import Partida, aceptar_tratado, crear_partida_demo, rechazar_tratado

AYUDA = """
Órdenes disponibles (todas relativas a TU nación):
  mapa                                   - Muestra el diagrama del mapa y la tabla de todas las provincias.
  estado                                 - Muestra el estado de tu nación, provincias y vecinos.
  reclutar <provincia> <cantidad>        - Recluta soldados (10 oro / 100 soldados).
  muralla <provincia>                    - Construye una muralla (+100% defensa, 50 oro).
  torre <provincia>                      - Construye una torre de vigía (25 oro).
  pillar <provincia>                     - Pilla la provincia (oro, -15% felicidad, cooldown 12).
  mover <origen> <destino> <cantidad>    - Mueve tropas a una provincia adyacente propia o neutral.
  atacar <origen> <destino> <cantidad>   - Ataca una provincia adyacente enemiga o neutral.
  guerra <id_nacion>                     - Declara la guerra a otra nación.
  paz <id_nacion>                        - Envía una propuesta de tratado de paz.
  alianza <id_nacion>                    - Envía una propuesta de alianza militar.
  aceptar <paz|alianza> <id_nacion>      - Acepta una propuesta diplomática pendiente.
  rechazar <paz|alianza> <id_nacion>     - Rechaza una propuesta diplomática pendiente.
  cancelar <id_nacion>                   - Cancela la relación vigente (activa ceasefire).
  abandonar <provincia>                  - Abandona una provincia propia.
  disband <provincia> <cantidad>         - Disuelve tropas propias en una provincia.
  ayuda                                  - Muestra esta lista de órdenes.
  fin                                    - Termina tu turno de órdenes.
"""


def imprimir_mapa_completo(partida: Partida) -> None:
    motor = partida.motor
    mapa = motor.mapa
    num_provs = len(mapa)
    print("\n" + "=" * 85)
    print(f"{'MAPA DE PROVINCIAS — TOPOLOGÍA CIRCULAR (ANILLO)':^85}")
    print("=" * 85)
    if num_provs == 9:
        print("  Esquema de Conexiones:")
        print("    [P0] <-------> [P1] <-------> [P2] <-------> [P3]")
        print("      ^                                            ^")
        print("      |                                            |")
        print("      v                                            v")
        print("    [P8]                                         [P4]")
        print("      ^                                            ^")
        print("      |                                            |")
        print("      v                                            v")
        print("    [P7] <---------------> [P6] <---------------> [P5]")
    elif num_provs > 1:
        ring_str = " <-> ".join(f"[P{pid}]" for pid in sorted(mapa.keys()))
        print(f"  Anillo: {ring_str} <-> (vuelve a [P0])")
    print("-" * 85)
    print(f"{'ID':^4} | {'Propietario':<20} | {'Tropas':^8} | {'Población':^10} | {'Felicidad':^9} | {'Muralla':^7} | {'Torre':^5} | {'Vecinos'}")
    print("-" * 85)
    for pid in sorted(mapa.keys()):
        p = mapa[pid]
        if p.propietario is not None and p.propietario in motor.naciones:
            dueno_str = f"{motor.naciones[p.propietario].nombre} (Nación {p.propietario})"
        else:
            dueno_str = "Neutral"

        muralla_str = "Sí (+100%)" if p.muralla else "No"
        torre_str = "Sí" if p.torre_vigia else "No"
        cooldown_str = f" [Pillaje:{p.cooldown_pillaje}t]" if p.cooldown_pillaje > 0 else ""

        print(
            f"{p.id_provincia:^4} | {dueno_str:<20} | {p.tropas:^8} | {p.poblacion:^10} | "
            f"{p.felicidad:^8}% | {muralla_str:^7} | {torre_str:^5} | {p.vecinos}{cooldown_str}"
        )
    print("=" * 85)


def imprimir_estado_global(partida: Partida) -> None:
    motor = partida.motor
    print(f"\n===== Turno {motor.turno_actual} =====")
    for nacion in motor.naciones.values():
        estado = "ACTIVA" if nacion.activa else "ELIMINADA"
        provs_str = ", ".join(f"Prov {pid}" for pid in sorted(nacion.provincias)) if nacion.provincias else "Ninguna (Exilio)"
        print(
            f"  Nación {nacion.id_nacion} [{nacion.nombre}] ({estado}) — "
            f"Provincias ({len(nacion.provincias)}): [{provs_str}] | Oro: {nacion.tesoreria} | "
            f"Felicidad prom.: {nacion.felicidad_promedio}% | AP: {nacion.puntos_accion:.2f} | "
            f"Puntos victoria: {nacion.puntos_victoria} | Guerras activas: {nacion.guerras_activas}"
        )
    imprimir_mapa_completo(partida)


def imprimir_estado_nacion(partida: Partida, nacion: Nacion) -> None:
    mapa = partida.motor.mapa
    print(f"\n-- Estado de {nacion.nombre} (Nación {nacion.id_nacion}) --")
    print(f"Oro: {nacion.tesoreria} | AP: {nacion.puntos_accion:.2f} | Felicidad prom.: {nacion.felicidad_promedio}% | Provincias totales: {len(nacion.provincias)}")
    if not nacion.provincias:
        print("  (Sin provincias bajo control - Nación en el exilio)")
    for pid in sorted(nacion.provincias):
        p = mapa[pid]
        muralla_str = "Muralla: Sí" if p.muralla else "Muralla: No"
        torre_str = "Torre: Sí" if p.torre_vigia else "Torre: No"
        print(
            f"  * Provincia {pid} -> Tropas: {p.tropas} | Pob: {p.poblacion} | Felicidad: {p.felicidad}% | "
            f"{muralla_str} | {torre_str} | Puede mover hacia: {p.vecinos}"
        )


def _leer_orden_nacion(partida: Partida, nacion: Nacion) -> None:
    motor = partida.motor
    mapa = motor.mapa
    gestor_dip = partida.gestor_diplomacia

    # Notificación de solicitudes diplomáticas pendientes
    pendientes = partida.propuestas_pendientes.get(nacion.id_nacion, [])
    if pendientes:
        print(f"\n>> ✉️  SOLICITUDES DIPLOMÁTICAS PENDIENTES para {nacion.nombre}:")
        for tipo, id_orig in pendientes:
            orig_nombre = motor.naciones[id_orig].nombre if id_orig in motor.naciones else f"Nación {id_orig}"
            print(f"   - {orig_nombre} (Nación {id_orig}) te ofreció un tratado de '{tipo.upper()}'. (Usa 'aceptar {tipo} {id_orig}' o 'rechazar {tipo} {id_orig}')")

    provs_list = sorted(nacion.provincias)
    provs_summary = f"Provincias ({len(provs_list)}): {provs_list}" if provs_list else "Sin provincias"
    print(f"\n>> Órdenes de {nacion.nombre} (Nación {nacion.id_nacion}) [{provs_summary} | Oro: {nacion.tesoreria}]. Escribe 'ayuda' o 'mapa'.")

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
        if comando == "mapa":
            imprimir_mapa_completo(partida)
            continue
        if comando == "estado":
            imprimir_estado_nacion(partida, nacion)
            continue

        try:
            if comando == "reclutar":
                if len(partes) != 3:
                    print("Uso: reclutar <provincia> <cantidad>")
                    continue
                prov_id, cant = int(partes[1]), int(partes[2])
                if prov_id not in nacion.provincias:
                    print(f"❌ Error: La provincia {prov_id} no te pertenece. Tus provincias son: {sorted(nacion.provincias)}")
                    continue
                if cant <= 0:
                    print("❌ Error: La cantidad a reclutar debe ser mayor a 0.")
                    continue
                costo = max(1, (cant * 10) // 100)
                if nacion.tesoreria < costo:
                    print(f"❌ Error: Oro insuficiente. Reclutar {cant} soldados cuesta {costo} oro (tienes {nacion.tesoreria} oro).")
                    continue
                motor.planificar_orden(FaseOrden.ESTATICA, nacion.id_nacion, TipoEvento.RECLUTAR, origen=prov_id, datos={"cantidad": cant})
                print(f"✓ Orden encolada: Reclutar {cant} soldados en Prov {prov_id} por {costo} oro.")

            elif comando == "muralla":
                if len(partes) != 2:
                    print("Uso: muralla <provincia>")
                    continue
                prov_id = int(partes[1])
                if prov_id not in nacion.provincias:
                    print(f"❌ Error: La provincia {prov_id} no te pertenece. Tus provincias son: {sorted(nacion.provincias)}")
                    continue
                if mapa[prov_id].muralla:
                    print(f"❌ Error: La provincia {prov_id} ya tiene una muralla construida.")
                    continue
                if nacion.tesoreria < 50:
                    print(f"❌ Error: Oro insuficiente. Construir muralla cuesta 50 oro (tienes {nacion.tesoreria} oro).")
                    continue
                motor.planificar_orden(FaseOrden.ESTATICA, nacion.id_nacion, TipoEvento.CONSTRUIR_MURALLA, origen=prov_id)
                print(f"✓ Orden encolada: Construir muralla en Prov {prov_id} (50 oro).")

            elif comando == "torre":
                if len(partes) != 2:
                    print("Uso: torre <provincia>")
                    continue
                prov_id = int(partes[1])
                if prov_id not in nacion.provincias:
                    print(f"❌ Error: La provincia {prov_id} no te pertenece. Tus provincias son: {sorted(nacion.provincias)}")
                    continue
                if mapa[prov_id].torre_vigia:
                    print(f"❌ Error: La provincia {prov_id} ya tiene una torre de vigía construida.")
                    continue
                if nacion.tesoreria < 25:
                    print(f"❌ Error: Oro insuficiente. Construir torre de vigía cuesta 25 oro (tienes {nacion.tesoreria} oro).")
                    continue
                motor.planificar_orden(FaseOrden.ESTATICA, nacion.id_nacion, TipoEvento.CONSTRUIR_TORRE, origen=prov_id)
                print(f"✓ Orden encolada: Construir torre de vigía en Prov {prov_id} (25 oro).")

            elif comando == "pillar":
                if len(partes) != 2:
                    print("Uso: pillar <provincia>")
                    continue
                prov_id = int(partes[1])
                if prov_id not in nacion.provincias:
                    print(f"❌ Error: La provincia {prov_id} no te pertenece.")
                    continue
                if mapa[prov_id].cooldown_pillaje > 0:
                    print(f"❌ Error: La provincia {prov_id} fue pillada recientemente (cooldown: {mapa[prov_id].cooldown_pillaje} turnos).")
                    continue
                motor.planificar_orden(FaseOrden.ESTATICA, nacion.id_nacion, TipoEvento.PILLAJE, origen=prov_id)
                print(f"✓ Orden encolada: Pillar provincia {prov_id}.")

            elif comando in ("mover", "atacar"):
                if len(partes) != 4:
                    print(f"Uso: {comando} <origen> <destino> <cantidad>")
                    continue
                orig_id, dest_id, cant = int(partes[1]), int(partes[2]), int(partes[3])
                if orig_id not in nacion.provincias:
                    print(f"❌ Error: La provincia origen {orig_id} no te pertenece. Tus provincias son: {sorted(nacion.provincias)}")
                    continue
                if dest_id not in mapa[orig_id].vecinos:
                    print(f"❌ Error: Las provincias {orig_id} y {dest_id} no son adyacentes. Vecinos válidos de Prov {orig_id}: {mapa[orig_id].vecinos}")
                    continue
                if cant <= 0:
                    print("❌ Error: La cantidad de tropas debe ser mayor a 0.")
                    continue
                if cant > mapa[orig_id].tropas:
                    print(f"❌ Error: Tropas insuficientes en Prov {orig_id} (tienes {mapa[orig_id].tropas} tropas, pediste {cant}).")
                    continue

                dest_prov = mapa[dest_id]
                # Si es atacar y el destino es de otra nación, verificar si están en guerra
                if dest_prov.propietario is not None and dest_prov.propietario != nacion.id_nacion:
                    if not gestor_dip.estan_en_guerra(nacion.id_nacion, dest_prov.propietario):
                        print(f"⚠️ Aviso: Prov {dest_id} pertenece a Nación {dest_prov.propietario}. Debes declararle la guerra primero con 'guerra {dest_prov.propietario}'.")
                        continue

                tipo_ev = TipoEvento.ATAQUE if comando == "atacar" else TipoEvento.MOVIMIENTO
                motor.planificar_orden(FaseOrden.ORDENADA, nacion.id_nacion, tipo_ev, origen=orig_id, destino=dest_id, datos={"cantidad_tropas": cant})
                print(f"✓ Orden encolada: {comando.capitalize()} {cant} tropas de Prov {orig_id} a Prov {dest_id}.")

            elif comando == "guerra":
                if len(partes) != 2:
                    print("Uso: guerra <id_nacion>")
                    continue
                obj_id = int(partes[1])
                if obj_id == nacion.id_nacion:
                    print("❌ Error: No puedes declararte la guerra a ti mismo.")
                    continue
                if obj_id not in motor.naciones:
                    print(f"❌ Error: La nación {obj_id} no existe.")
                    continue
                if not motor.naciones[obj_id].activa:
                    print(f"❌ Error: La nación {obj_id} ya ha sido eliminada.")
                    continue
                if gestor_dip.estan_en_guerra(nacion.id_nacion, obj_id):
                    print(f"❌ Error: Ya estás en guerra con la nación {obj_id}.")
                    continue
                if gestor_dip.hay_ceasefire_activo(nacion.id_nacion, obj_id):
                    print(f"❌ Error: Hay un alto el fuego (ceasefire) activo con la nación {obj_id}.")
                    continue
                motor.planificar_orden(FaseOrden.ORDENADA, nacion.id_nacion, TipoEvento.DECLARAR_GUERRA, origen=0, datos={"objetivo": obj_id})
                print(f"✓ Orden encolada: Declarar la guerra a la Nación {obj_id} ({motor.naciones[obj_id].nombre}).")

            elif comando in ("paz", "alianza"):
                if len(partes) != 2:
                    print(f"Uso: {comando} <id_nacion>")
                    continue
                obj_id = int(partes[1])
                if obj_id == nacion.id_nacion:
                    print("❌ Error: No puedes proponerte tratados a ti mismo.")
                    continue
                if obj_id not in motor.naciones:
                    print(f"❌ Error: La nación {obj_id} no existe.")
                    continue
                motor.planificar_orden(FaseOrden.ESTATICA, nacion.id_nacion, TipoEvento.DIPLOMACIA, origen=0, datos={"objetivo": obj_id, "tipo_propuesta": comando})
                print(f"✓ Propuesta encolada: Ofrecer '{comando}' a la Nación {obj_id} ({motor.naciones[obj_id].nombre}).")

            elif comando == "aceptar":
                if len(partes) != 3:
                    print("Uso: aceptar <paz|alianza> <id_nacion>")
                    continue
                tipo_prop, obj_id = partes[1].lower(), int(partes[2])
                if aceptar_tratado(partida, nacion.id_nacion, obj_id, tipo_prop, motor.turno_actual):
                    print(f"✓ Tratado de '{tipo_prop.upper()}' aceptado y formalizado con la Nación {obj_id}.")
                else:
                    print(f"❌ Error: No tienes una propuesta pendiente de '{tipo_prop}' de la nación {obj_id}.")

            elif comando == "rechazar":
                if len(partes) != 3:
                    print("Uso: rechazar <paz|alianza> <id_nacion>")
                    continue
                tipo_prop, obj_id = partes[1].lower(), int(partes[2])
                if rechazar_tratado(partida, nacion.id_nacion, obj_id, tipo_prop):
                    print(f"✓ Propuesta de '{tipo_prop.upper()}' de la Nación {obj_id} rechazada.")
                else:
                    print(f"❌ Error: No tienes una propuesta pendiente de '{tipo_prop}' de la nación {obj_id}.")

            elif comando == "cancelar":
                if len(partes) != 2:
                    print("Uso: cancelar <id_nacion>")
                    continue
                obj_id = int(partes[1])
                if obj_id not in motor.naciones:
                    print(f"❌ Error: La nación {obj_id} no existe.")
                    continue
                motor.planificar_orden(FaseOrden.ORDENADA, nacion.id_nacion, TipoEvento.CANCELAR_RELACION, origen=0, datos={"objetivo": obj_id})
                print(f"✓ Orden encolada: Cancelar relación vigente con Nación {obj_id}.")

            elif comando == "abandonar":
                if len(partes) != 2:
                    print("Uso: abandonar <provincia>")
                    continue
                prov_id = int(partes[1])
                if prov_id not in nacion.provincias:
                    print(f"❌ Error: La provincia {prov_id} no te pertenece.")
                    continue
                motor.planificar_orden(FaseOrden.ORDENADA, nacion.id_nacion, TipoEvento.ABANDONAR_PROVINCIA, origen=prov_id)
                print(f"✓ Orden encolada: Abandonar Prov {prov_id}.")

            elif comando == "disband":
                if len(partes) != 3:
                    print("Uso: disband <provincia> <cantidad>")
                    continue
                prov_id, cant = int(partes[1]), int(partes[2])
                if prov_id not in nacion.provincias:
                    print(f"❌ Error: La provincia {prov_id} no te pertenece.")
                    continue
                if cant <= 0:
                    print("❌ Error: La cantidad a disolver debe ser mayor a 0.")
                    continue
                if cant > mapa[prov_id].tropas:
                    print(f"❌ Error: Tropas insuficientes en Prov {prov_id} ({mapa[prov_id].tropas} disponibles).")
                    continue
                motor.planificar_orden(FaseOrden.ORDENADA, nacion.id_nacion, TipoEvento.DISBAND, origen=prov_id, datos={"cantidad": cant})
                print(f"✓ Orden encolada: Disolver {cant} soldados en Prov {prov_id}.")

            else:
                print(f"❌ Comando desconocido: '{comando}'. Escribe 'ayuda' para ver la lista.")
        except ValueError:
            print("❌ Formato de orden inválido (los IDs y cantidades deben ser números enteros). Escribe 'ayuda'.")


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
