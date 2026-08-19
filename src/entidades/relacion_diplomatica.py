"""
Entidad Relación Diplomática.

Ver: Formalización Cuantitativa y Lógica del Sistema - AgeofConquest,
     variable N_D_n_m(t): {NEUTRAL, ALLIANCE, PEACE, WAR, CEASEFIRE,
     PROTECTOR, PROTECTORATE}.
     Modelo Conceptual de Simulación - Age of Conquest, secciones 2.5 y 3.
     Game Manual, sección "Diplomacy".

Las transiciones de estado (declarar guerra, cancelar relación → ceasefire,
penalizaciones de felicidad asociadas) se implementan en el módulo de
combate/diplomacia, no aquí.
"""

from dataclasses import dataclass
from enum import Enum


class TipoRelacion(Enum):
    NEUTRAL = "neutral"
    ALIANZA = "alianza"
    PROTECTOR = "protector"
    PROTECTORADO = "protectorado"
    PAZ = "paz"
    GUERRA = "guerra"
    CEASEFIRE = "ceasefire"


@dataclass
class RelacionDiplomatica:
    nacion_a: int
    nacion_b: int
    tipo: TipoRelacion = TipoRelacion.NEUTRAL

    # Turno de simulación en que se estableció la relación actual.
    turno_inicio: int = 0

    # Turnos de ceasefire restantes (aplica tras cancelar alianza/paz/etc.,
    # ver Game Manual sección "Diplomacy": tratados de paz = 1 turno,
    # otras relaciones = ceasefire más largo).
    turnos_ceasefire_restante: int = 0

    def esta_en_guerra(self) -> bool:
        return self.tipo == TipoRelacion.GUERRA

    def puede_declarar_guerra(self) -> bool:
        # No se puede declarar guerra si ya existe una relación establecida
        # (hay que cancelarla primero, lo que genera un ceasefire) ni durante
        # un ceasefire activo. Ver Game Manual, sección "Diplomacy".
        return self.tipo in (TipoRelacion.NEUTRAL,) and self.turnos_ceasefire_restante == 0

    def involucra(self, id_nacion: int) -> bool:
        return id_nacion in (self.nacion_a, self.nacion_b)

    def otra_nacion(self, id_nacion: int) -> int:
        if id_nacion == self.nacion_a:
            return self.nacion_b
        if id_nacion == self.nacion_b:
            return self.nacion_a
        raise ValueError(f"La nación {id_nacion} no participa en esta relación")
