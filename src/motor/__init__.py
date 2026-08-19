"""
Módulo del motor de simulación de eventos discretos (DES) para Age of Conquest.

Incluye la Lista de Eventos Futuros (FEL), bucle principal de turnos WEGO,
cálculo de ranking de debilidad, despachadores y algoritmos de simulación.
"""

from .ciclo_wego import MotorSimulacionWEGO, ResultadoTurno
from .fel import Evento, FaseOrden, ListaEventosFuturos, TipoEvento
from .ranking import (
    asignar_prioridades_ranking,
    calcular_ranking_debilidad,
    calcular_tropas_totales_nacion,
)

__all__ = [
    "Evento",
    "FaseOrden",
    "TipoEvento",
    "ListaEventosFuturos",
    "MotorSimulacionWEGO",
    "ResultadoTurno",
    "calcular_ranking_debilidad",
    "asignar_prioridades_ranking",
    "calcular_tropas_totales_nacion",
]
