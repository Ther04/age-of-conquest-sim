"""
Módulo del Submodelo de Combate y Movimiento para Age of Conquest.

Implementa la Ley Lineal de Lanchester discreta en aritmética entera,
movimiento de tropas, bloqueo naval, bonificaciones aditivas,
transferencia territorial y Jaque Mate.
"""

from .lanchester import (
    ResultadoCombate,
    calcular_fuerza_atacante,
    calcular_fuerza_defensora,
    resolver_combate,
    transferir_todas_las_tierras,
)
from .movimiento import ResultadoMovimiento, ejecutar_movimiento_tropas

__all__ = [
    "ResultadoCombate",
    "calcular_fuerza_atacante",
    "calcular_fuerza_defensora",
    "resolver_combate",
    "transferir_todas_las_tierras",
    "ResultadoMovimiento",
    "ejecutar_movimiento_tropas",
]
