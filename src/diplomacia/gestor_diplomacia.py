"""
Gestor de Diplomacia y Transiciones de Relaciones Bilaterales.

Ver:
- Game Manual, sección "Diplomacy":
  "States: Neutral, Alliance, Protector/Protectorate, Peace Treaty, War, Ceasefire.
   Cancelling an existing relationship creates a ceasefire (1 turn for peace treaty,
   longer for others) before being able to declare war again."
- Modelo Conceptual de Simulación - Age of Conquest, secciones 2.5, 4.1 y 9.4.
- Formalización Cuantitativa, variable N_D_n_m(t).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from src.entidades.nacion import Nacion
from src.entidades.relacion_diplomatica import RelacionDiplomatica, TipoRelacion

# Duración estándar del Ceasefire según el tipo de relación cancelada (en turnos)
DURACION_CEASEFIRE_PAZ = 1
DURACION_CEASEFIRE_ALIANZA = 2
DURACION_CEASEFIRE_PROTECTORADO = 2


def clave_relacion(id_a: int, id_b: int) -> tuple[int, int]:
    """Retorna la tupla canónica ordenada para indexar relaciones bilaterales."""
    return (min(id_a, id_b), max(id_a, id_b))


class GestorDiplomacia:
    """
    Administra la matriz de relaciones diplomáticas entre todas las naciones del juego,
    sus transiciones de estado y la expiración de periodos de Ceasefire.
    """

    def __init__(self, relaciones: Optional[dict[tuple[int, int], RelacionDiplomatica]] = None) -> None:
        self.relaciones: dict[tuple[int, int], RelacionDiplomatica] = relaciones or {}

    def obtener_relacion(self, id_a: int, id_b: int, crear_si_no_existe: bool = True) -> Optional[RelacionDiplomatica]:
        """Obtiene la relación bilateral entre dos naciones (crea NEUTRAL por defecto)."""
        if id_a == id_b:
            raise ValueError("Una nación no puede tener relación diplomática consigo misma")

        clave = clave_relacion(id_a, id_b)
        if clave not in self.relaciones:
            if crear_si_no_existe:
                self.relaciones[clave] = RelacionDiplomatica(
                    nacion_a=clave[0],
                    nacion_b=clave[1],
                    tipo=TipoRelacion.NEUTRAL,
                    turno_inicio=1,
                    turnos_ceasefire_restante=0,
                )
            else:
                return None
        return self.relaciones[clave]

    def son_aliados(self, id_a: int, id_b: int) -> bool:
        """Verifica si dos naciones son aliadas o tienen relación de protector/protectorado."""
        if id_a == id_b:
            return True
        rel = self.obtener_relacion(id_a, id_b, crear_si_no_existe=False)
        if not rel:
            return False
        return rel.tipo in (TipoRelacion.ALIANZA, TipoRelacion.PROTECTOR, TipoRelacion.PROTECTORADO)

    def estan_en_guerra(self, id_a: int, id_b: int) -> bool:
        """Verifica si dos naciones están actualmente en estado de guerra."""
        if id_a == id_b:
            return False
        rel = self.obtener_relacion(id_a, id_b, crear_si_no_existe=False)
        if not rel:
            return False
        return rel.tipo == TipoRelacion.GUERRA

    def hay_ceasefire_activo(self, id_a: int, id_b: int) -> bool:
        """Verifica si existe un alto el fuego (ceasefire) activo entre dos naciones."""
        if id_a == id_b:
            return False
        rel = self.obtener_relacion(id_a, id_b, crear_si_no_existe=False)
        if not rel:
            return False
        return rel.turnos_ceasefire_restante > 0 or rel.tipo == TipoRelacion.CEASEFIRE

    def pueden_declararse_guerra(self, id_a: int, id_b: int) -> bool:
        """
        Determina si `id_a` puede declarar la guerra a `id_b`.
        Requiere estar en NEUTRAL y sin Ceasefire activo.
        """
        rel = self.obtener_relacion(id_a, id_b)
        return rel.tipo == TipoRelacion.NEUTRAL and rel.turnos_ceasefire_restante == 0

    # --- Transiciones de Estado ---

    def establecer_alianza(self, id_a: int, id_b: int, turno_actual: int = 1) -> RelacionDiplomatica:
        """Establece una alianza militar mutua entre dos naciones."""
        rel = self.obtener_relacion(id_a, id_b)
        if rel.tipo == TipoRelacion.GUERRA:
            raise ValueError("No se puede formar alianza directamente mientras se está en guerra. Debe pactarse la paz primero.")
        rel.tipo = TipoRelacion.ALIANZA
        rel.turno_inicio = turno_actual
        rel.turnos_ceasefire_restante = 0
        return rel

    def establecer_protectorado(self, id_protector: int, id_protegido: int, turno_actual: int = 1) -> RelacionDiplomatica:
        """Establece una relación de protector / protectorado."""
        rel = self.obtener_relacion(id_protector, id_protegido)
        if rel.tipo == TipoRelacion.GUERRA:
            raise ValueError("No se puede establecer protectorado mientras se está en guerra.")
        # La relación se etiqueta según el orden canónico
        if rel.nacion_a == id_protector:
            rel.tipo = TipoRelacion.PROTECTOR
        else:
            rel.tipo = TipoRelacion.PROTECTORADO
        rel.turno_inicio = turno_actual
        rel.turnos_ceasefire_restante = 0
        return rel

    def establecer_paz(self, id_a: int, id_b: int, turno_actual: int = 1) -> RelacionDiplomatica:
        """Establece un Tratado de Paz entre dos naciones."""
        rel = self.obtener_relacion(id_a, id_b)
        rel.tipo = TipoRelacion.PAZ
        rel.turno_inicio = turno_actual
        rel.turnos_ceasefire_restante = 0
        return rel

    def firmar_paz_desde_guerra(
        self,
        id_a: int,
        id_b: int,
        nacion_a: Nacion,
        nacion_b: Nacion,
        turno_actual: int = 1,
    ) -> RelacionDiplomatica:
        """
        Finaliza una guerra formal firmando un tratado de paz.
        Decrementa los contadores de guerras activas de ambas naciones.
        """
        rel = self.obtener_relacion(id_a, id_b)
        if rel.tipo != TipoRelacion.GUERRA:
            raise ValueError(f"Las naciones {id_a} y {id_b} no están en guerra.")

        rel.tipo = TipoRelacion.PAZ
        rel.turno_inicio = turno_actual
        rel.turnos_ceasefire_restante = 0

        nacion_a.guerras_activas = max(0, nacion_a.guerras_activas - 1)
        nacion_b.guerras_activas = max(0, nacion_b.guerras_activas - 1)
        return rel

    def cancelar_relacion(
        self,
        id_a: int,
        id_b: int,
        turno_actual: int = 1,
    ) -> dict[str, Any]:
        """
        Cancela una relación existente (Alianza, Paz, Protectorado), lo que activa
        obligatoriamente un periodo de Ceasefire antes de poder declarar guerra.

        Duración:
        - Paz: 1 turno de Ceasefire.
        - Alianza / Protectorado: 2 turnos de Ceasefire.
        """
        rel = self.obtener_relacion(id_a, id_b)
        tipo_previo = rel.tipo

        if tipo_previo in (TipoRelacion.NEUTRAL, TipoRelacion.GUERRA, TipoRelacion.CEASEFIRE):
            raise ValueError(f"No se puede cancelar una relación en estado '{tipo_previo.value}'.")

        # Asignar duración del ceasefire según la relación previa
        if tipo_previo == TipoRelacion.PAZ:
            duracion = DURACION_CEASEFIRE_PAZ
        else:
            duracion = DURACION_CEASEFIRE_ALIANZA

        rel.tipo = TipoRelacion.CEASEFIRE
        rel.turno_inicio = turno_actual
        rel.turnos_ceasefire_restante = duracion

        return {
            "nacion_a": id_a,
            "nacion_b": id_b,
            "relacion_previa": tipo_previo.value,
            "ceasefire_turnos": duracion,
            "turno": turno_actual,
        }

    def actualizar_ceasefires_fin_turno(self) -> list[tuple[int, int]]:
        """
        Hook de fin de turno:
        Reduce en 1 los turnos de Ceasefire restantes.
        Si el Ceasefire llega a 0, la relación transiciona automáticamente a NEUTRAL.
        Retorna la lista de pares de naciones cuyo ceasefire expiró en este turno.
        """
        expirados: list[tuple[int, int]] = []
        for clave, rel in self.relaciones.items():
            if rel.turnos_ceasefire_restante > 0:
                rel.turnos_ceasefire_restante -= 1
                if rel.turnos_ceasefire_restante == 0:
                    rel.tipo = TipoRelacion.NEUTRAL
                    expirados.append(clave)
        return expirados
