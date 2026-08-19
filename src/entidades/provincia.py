"""
Entidad Provincia (prefijo P_ en la Formalización Cuantitativa).

Ver: Formalización Cuantitativa y Lógica del Sistema - AgeofConquest,
     sección "Variables de Estado de la Provincia (Prefijo P)".
     Modelo Conceptual de Simulación - Age of Conquest, secciones 2.2 y 3.

Esta clase es un contenedor de estado (datos + consultas simples). Los cálculos
de negocio (ingresos, felicidad, atrición, revueltas, combate, etc.) se
implementan en los módulos de economía y combate, no aquí.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Provincia:
    id_provincia: int

    # P_pop_i(t): población habitante de la provincia. Entero, [0, infinito).
    poblacion: int = 0

    # P_H_i(t): felicidad promedio de la provincia. Entero, [0, 100].
    felicidad: int = 50

    # P_M_i(t): tropas/soldados estacionados en la provincia. Entero, [0, infinito).
    tropas: int = 0

    # P_W_i(t): presencia de murallas. Booleano.
    muralla: bool = False

    # P_V_i(t): presencia de torre de vigía. Booleano.
    torre_vigia: bool = False

    # P_cd_i(t): cooldown restante por saqueo/pillaje. Entero, [0, 12].
    cooldown_pillaje: int = 0

    # P_com_base_i: valor de comercio base inherente a la provincia. Entero, [0, infinito).
    comercio_base: int = 0

    # id de la nación propietaria; None = provincia neutral (sin dueño).
    propietario: Optional[int] = None

    # ids de las provincias adyacentes (usado para ataques, revueltas, movimiento).
    vecinos: list[int] = field(default_factory=list)

    # Provincia con acceso a agua (relevante para movimiento naval y bloqueos).
    es_costera: bool = False

    def __post_init__(self) -> None:
        if not 0 <= self.felicidad <= 100:
            raise ValueError(f"Felicidad fuera de rango [0,100]: {self.felicidad}")
        if not 0 <= self.cooldown_pillaje <= 12:
            raise ValueError(f"Cooldown de pillaje fuera de rango [0,12]: {self.cooldown_pillaje}")
        if self.poblacion < 0:
            raise ValueError(f"Población no puede ser negativa: {self.poblacion}")
        if self.tropas < 0:
            raise ValueError(f"Tropas no pueden ser negativas: {self.tropas}")

    def es_neutral(self) -> bool:
        return self.propietario is None

    def tiene_tropas(self) -> bool:
        return self.tropas > 0

    def esta_pillada(self) -> bool:
        # Mientras el cooldown esté activo, la provincia no puede reclutar
        # ni pagar impuestos/comercio (ver Game Manual, sección "Population").
        return self.cooldown_pillaje > 0

    def puede_recaudar(self) -> bool:
        # Ver Formalización Cuantitativa, ecuaciones de N_I_com_n / N_I_tax_n:
        # solo se cobra comercio/impuesto si felicidad >= 50 y no hay pillaje activo.
        return self.felicidad >= 50 and not self.esta_pillada()
