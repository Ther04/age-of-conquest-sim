"""
Lista de Eventos Futuros (FEL / Future Event List).

Estructura central del modelo de simulación de eventos discretos (DES) para
el wargame Age of Conquest bajo el paradigma WEGO.

Ver:
- Modelo Conceptual de Simulación - Age of Conquest, sección 7:
  "Lista de eventos futuros (FEL)".
- Formalización Cuantitativa y Lógica del Sistema - AgeofConquest,
  sección "Algoritmo del Despachador de la LEF y Reloj de Simulación".
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class FaseOrden(Enum):
    """
    Fases de ejecución de eventos dentro de un turno macro de simulación.
    - ESTATICA: Órdenes no interactivas (reclutar, fortificar, pillaje, diplomacia, etc.).
    - ORDENADA: Órdenes interactivas/espaciales procesadas vía Round-Robin por debilidad.
    - ENDOGENA: Cálculos automáticos de fin de turno del motor (economía, moral, atrición).
    """
    ESTATICA = "estatica"
    ORDENADA = "ordenada"
    ENDOGENA = "endogena"


class TipoEvento(Enum):
    """
    Catálogo de tipos de eventos reconocidos por el motor de simulación.
    Ver Modelo Conceptual §5.1 (Exógenos) y §5.2 (Endógenos).
    """
    # Órdenes Estáticas (No interactivas)
    RECLUTAR = "reclutar"
    FORTIFICAR = "fortificar"
    CONSTRUIR_MURALLA = "construir_muralla"
    CONSTRUIR_TORRE = "construir_torre"
    PILLAJE = "pillaje"
    DIPLOMACIA = "diplomacia"
    DISTRIBUIR_DINERO = "distribuir_dinero"
    FESTIVAL = "festival"

    # Órdenes Ordenadas (Interactivas / Round-Robin)
    MOVIMIENTO = "movimiento"
    ATAQUE = "ataque"
    DECLARAR_GUERRA = "declarar_guerra"
    CANCELAR_RELACION = "cancelar_relacion"
    ABANDONAR_PROVINCIA = "abandonar_provincia"
    DISBAND = "disband"

    # Eventos Endógenos del Motor
    FIN_TURNO_ECONOMIA = "fin_turno_economia"
    VERIFICAR_VICTORIA = "verificar_victoria"


@dataclass(order=True)
class Evento:
    """
    Registro individual dentro de la Lista de Eventos Futuros (FEL).

    El orden natural de procesamiento se define por:
    1. `turno`: Turno de ocurrencia (menor a mayor).
    2. `prioridad_fase`: Prioridad numérica de fase (ESTATICA=1, ORDENADA=2, ENDOGENA=3).
    3. `prioridad_nacion`: Ranking de debilidad de la nación (1 = más débil, actúa primero).
    4. `id_evento`: Identificador secuencial para orden FIFO y estabilidad en desempates.
    """
    turno: int
    prioridad_fase: int = field(init=False)
    prioridad_nacion: int
    id_evento: int = 0

    # Campos de datos del evento (excluidos del cálculo comparativo directo)
    fase: FaseOrden = field(compare=False, default=FaseOrden.ESTATICA)
    id_nacion: int = field(compare=False, default=0)
    tipo_evento: TipoEvento = field(compare=False, default=TipoEvento.MOVIMIENTO)
    origen: int = field(compare=False, default=0)
    destino: Optional[int] = field(compare=False, default=None)
    datos: dict[str, Any] = field(compare=False, default_factory=dict)

    def __post_init__(self) -> None:
        # Asignar prioridad numérica de fase para ordenamiento estricto
        if self.fase == FaseOrden.ESTATICA:
            self.prioridad_fase = 1
        elif self.fase == FaseOrden.ORDENADA:
            self.prioridad_fase = 2
        else:
            self.prioridad_fase = 3


class ListaEventosFuturos:
    """
    Estructura de Lista de Eventos Futuros (FEL).
    Almacena, ordena y despacha las órdenes planificadas por los jugadores e IA.
    """

    def __init__(self) -> None:
        self._eventos: list[Evento] = []
        self._contador_eventos: int = 0

    def encolar(self, evento: Evento) -> None:
        """Encola un evento asignándole un ID secuencial si no lo tiene."""
        self._contador_eventos += 1
        evento.id_evento = self._contador_eventos
        self._eventos.append(evento)
        self._eventos.sort()

    def encolar_orden(
        self,
        turno: int,
        fase: FaseOrden,
        id_nacion: int,
        tipo_evento: TipoEvento,
        origen: int,
        destino: Optional[int] = None,
        prioridad_nacion: int = 1,
        datos: Optional[dict[str, Any]] = None,
    ) -> Evento:
        """Crea y encola una nueva orden en la FEL."""
        evento = Evento(
            turno=turno,
            prioridad_nacion=prioridad_nacion,
            fase=fase,
            id_nacion=id_nacion,
            tipo_evento=tipo_evento,
            origen=origen,
            destino=destino,
            datos=datos or {},
        )
        self.encolar(evento)
        return evento

    def encolar_lote(self, eventos: list[Evento]) -> None:
        """Encola múltiples eventos de forma eficiente."""
        for e in eventos:
            self._contador_eventos += 1
            e.id_evento = self._contador_eventos
            self._eventos.append(e)
        self._eventos.sort()

    def obtener_siguiente(self) -> Optional[Evento]:
        """Extrae y retorna el siguiente evento en la cola."""
        if not self._eventos:
            return None
        return self._eventos.pop(0)

    def inspeccionar_siguiente(self) -> Optional[Evento]:
        """Retorna el siguiente evento sin extraerlo de la cola."""
        if not self._eventos:
            return None
        return self._eventos[0]

    def filtrar_ordenes_estaticas(self, turno: int) -> list[Evento]:
        """
        Retorna y remueve todas las órdenes estáticas correspondientes a un turno.
        No requieren orden particular entre naciones (ver Formalización §Algoritmo Despachador).
        """
        estaticas: list[Evento] = []
        restantes: list[Evento] = []
        for e in self._eventos:
            if e.turno == turno and e.fase == FaseOrden.ESTATICA:
                estaticas.append(e)
            else:
                restantes.append(e)
        self._eventos = restantes
        return estaticas

    def filtrar_ordenes_ordenadas(self, turno: int) -> list[Evento]:
        """
        Retorna y remueve todas las órdenes ordenadas correspondientes a un turno.
        Estas serán procesadas mediante el algoritmo Round-Robin.
        """
        ordenadas: list[Evento] = []
        restantes: list[Evento] = []
        for e in self._eventos:
            if e.turno == turno and e.fase == FaseOrden.ORDENADA:
                ordenadas.append(e)
            else:
                restantes.append(e)
        self._eventos = restantes
        return ordenadas

    def obtener_eventos_nacion(self, turno: int, id_nacion: int) -> list[Evento]:
        """Obtiene todas las órdenes de una nación para un turno sin extraerlas."""
        return [e for e in self._eventos if e.turno == turno and e.id_nacion == id_nacion]

    def total_eventos(self) -> int:
        """Cantidad total de eventos pendientes en la FEL."""
        return len(self._eventos)

    def esta_vacia(self) -> bool:
        """Indica si no hay eventos encolados."""
        return len(self._eventos) == 0

    def limpiar(self) -> None:
        """Vacía todos los eventos de la FEL."""
        self._eventos.clear()
        self._contador_eventos = 0
