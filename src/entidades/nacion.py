"""
Entidad Nación (prefijo N_ en la Formalización Cuantitativa).

Ver: Formalización Cuantitativa y Lógica del Sistema - AgeofConquest,
     sección "Variables de Estado de la Nación (Prefijo N)".
     Modelo Conceptual de Simulación - Age of Conquest, secciones 2.1 y 3.

Esta clase es un contenedor de estado (datos + consultas simples). Los cálculos
de negocio (ingresos, costo administrativo, ranking round-robin, victoria, etc.)
se implementan en los módulos de economía y de motor de turnos, no aquí.
"""

from dataclasses import dataclass, field
from enum import Enum


class TipoNacion(Enum):
    HUMANO = "humano"
    IA = "ia"


class TasaImpuestos(Enum):
    """N_TR_n(t): tasa de impuestos establecida por la nación. {LOW, MEDIUM, HIGH}."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class Nacion:
    id_nacion: int
    nombre: str
    tipo: TipoNacion = TipoNacion.IA

    # N_T_n(t): oro acumulado en las arcas de la nación. Entero, [0, infinito).
    tesoreria: int = 0

    # N_Ap_n(t): puntos de acción de la nación. Real (único atributo no entero
    # según el diccionario de variables), [0, infinito).
    puntos_accion: float = 0.0

    # N_Ap_used_n(t): puntos de acción utilizados en el turno actual. Real.
    puntos_accion_usados: float = 0.0

    # N_Vp_n(t): puntos de victoria acumulados. Entero, [0, 100].
    puntos_victoria: int = 0

    # N_R_n(t): estado de vida del gobernante/rey. Booleano.
    gobernante_vivo: bool = True

    # N_H_prom_n(t): felicidad promedio ponderada nacional. Entero, [0, 100].
    felicidad_promedio: int = 50

    # N_TR_n(t): tasa de impuestos establecida por la nación.
    tasa_impuestos: TasaImpuestos = TasaImpuestos.MEDIUM

    # N_provinces_n(t): conjunto de ids de provincias que pertenecen a la nación.
    provincias: set[int] = field(default_factory=set)

    # N_W_active_n(t): número de guerras activas simultáneas de la nación.
    guerras_activas: int = 0

    # Estado general de la nación en la partida (False = eliminada).
    activa: bool = True

    def __post_init__(self) -> None:
        if not 0 <= self.felicidad_promedio <= 100:
            raise ValueError(f"Felicidad promedio fuera de rango [0,100]: {self.felicidad_promedio}")
        if not 0 <= self.puntos_victoria <= 100:
            raise ValueError(f"Puntos de victoria fuera de rango [0,100]: {self.puntos_victoria}")
        if self.tesoreria < 0:
            raise ValueError(f"Tesorería no puede ser negativa: {self.tesoreria}")
        if self.guerras_activas < 0:
            raise ValueError(f"Guerras activas no pueden ser negativas: {self.guerras_activas}")

    def numero_provincias(self) -> int:
        return len(self.provincias)

    def tiene_provincias(self) -> bool:
        return len(self.provincias) > 0

    def ha_alcanzado_victoria_por_puntos(self) -> bool:
        # Ver Game Manual, sección "Objectives": se gana al llegar a 100 puntos.
        return self.puntos_victoria >= 100

    def esta_eliminada(self) -> bool:
        # Ver Formalización Cuantitativa, "Inanición Territorial": una nación
        # queda eliminada cuando su felicidad llega a 0% tras perder todas
        # sus provincias (la lógica de transición vive en el módulo de economía).
        return not self.activa
