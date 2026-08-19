"""
Módulo del Submodelo de Diplomacia y Declaración de Guerra para Age of Conquest.

Incluye la gestión de relaciones bilaterales, transiciones de estado,
declaración de guerra, manejo de ceasefire y cálculo de penalizaciones de felicidad.
"""

from .declaracion_guerra import (
    aplicar_penalizacion_recurrente_guerras,
    calcular_penalizacion_declaracion_guerra,
    calcular_penalizacion_recurrente_guerra,
    declarar_guerra,
)

__all__ = [
    "calcular_penalizacion_declaracion_guerra",
    "calcular_penalizacion_recurrente_guerra",
    "declarar_guerra",
    "aplicar_penalizacion_recurrente_guerras",
]
