"""
Módulo del Submodelo de Combate para Age of Conquest.

Implementa la Ley Lineal de Lanchester discreta en aritmética entera,
bonificaciones aditivas, cálculo de bajas, transferencia territorial
y condición de Jaque Mate por muerte de gobernante.
"""

from .lanchester import (
    ResultadoCombate,
    calcular_fuerza_atacante,
    calcular_fuerza_defensora,
    resolver_combate,
)

__all__ = [
    "ResultadoCombate",
    "calcular_fuerza_atacante",
    "calcular_fuerza_defensora",
    "resolver_combate",
]
