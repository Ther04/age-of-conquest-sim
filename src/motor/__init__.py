"""
Módulo del motor de simulación de eventos discretos (DES) para Age of Conquest.

Incluye la Lista de Eventos Futuros (FEL), bucle principal de turnos WEGO,
despachadores de órdenes estáticas/ordenadas y algoritmos de simulación.
"""

from .ciclo_wego import MotorSimulacionWEGO, ResultadoTurno
from .fel import Evento, FaseOrden, ListaEventosFuturos, TipoEvento

__all__ = [
    "Evento",
    "FaseOrden",
    "TipoEvento",
    "ListaEventosFuturos",
    "MotorSimulacionWEGO",
    "ResultadoTurno",
]
