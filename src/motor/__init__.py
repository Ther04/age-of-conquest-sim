"""
Módulo del motor de simulación de eventos discretos (DES) para Age of Conquest.

Incluye la Lista de Eventos Futuros (FEL), despachadores de órdenes estáticas/ordenadas,
algoritmo de Round-Robin, bucle de turnos WEGO y evaluadores de victoria.
"""

from .fel import Evento, FaseOrden, TipoEvento, ListaEventosFuturos

__all__ = [
    "Evento",
    "FaseOrden",
    "TipoEvento",
    "ListaEventosFuturos",
]
