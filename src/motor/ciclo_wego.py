"""
Ciclo Principal de Simulación en Modo WEGO y Despachador de la LEF.

Ver:
- Formalización Cuantitativa y Lógica del Sistema - AgeofConquest,
  secciones "Fundamentos de Simulación en Modo WEGO", "Ciclo Principal WEGO"
  y "Algoritmo del Despachador de la LEF y Reloj de Simulación".
- Modelo Conceptual de Simulación - Age of Conquest, sección 9.1:
  "Bucle principal de simulación (motor de turnos)".
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from src.entidades.gobernante import Gobernante
from src.entidades.nacion import Nacion
from src.entidades.provincia import Provincia
from src.entidades.relacion_diplomatica import RelacionDiplomatica
from src.motor.fel import Evento, FaseOrden, ListaEventosFuturos, TipoEvento
from src.motor.ranking import calcular_ranking_debilidad
from src.motor.round_robin import ejecutar_round_robin


@dataclass
class ResultadoTurno:
    """Resumen de los eventos procesados durante la ejecución de un turno macro."""
    turno: int
    eventos_estaticos_procesados: list[Evento] = field(default_factory=list)
    eventos_ordenados_procesados: list[Evento] = field(default_factory=list)
    eventos_endogenos_procesados: list[Evento] = field(default_factory=list)
    partida_finalizada: bool = False
    ganador: Optional[int] = None
    detalles: dict[str, Any] = field(default_factory=dict)


# Firmas para handlers extensibles de eventos
HandlerEvento = Callable[[Evento, "MotorSimulacionWEGO"], Any]
HandlerFinTurno = Callable[[int, "MotorSimulacionWEGO"], Any]
HandlerVerificarVictoria = Callable[["MotorSimulacionWEGO"], Optional[int]]


class MotorSimulacionWEGO:
    """
    Motor central de eventos discretos que orquesta el ciclo WEGO.

    Secuencia estricta por turno:
    1. Fase de Órdenes Estáticas (no interactivas, síncronas).
    2. Fase de Órdenes Ordenadas (interactivas, despacho Round-Robin por ranking).
    3. Fase Endógena de Fin de Turno (crecimiento, finanzas, moral, atrición, revueltas).
    4. Verificación de condiciones de victoria y avance del reloj.
    """

    def __init__(
        self,
        mapa: Optional[dict[int, Provincia]] = None,
        naciones: Optional[dict[int, Nacion]] = None,
        gobernantes: Optional[dict[int, Gobernante]] = None,
        relaciones: Optional[dict[tuple[int, int], RelacionDiplomatica]] = None,
        turno_inicial: int = 1,
    ) -> None:
        self.turno_actual: int = turno_inicial
        self.fel: ListaEventosFuturos = ListaEventosFuturos()

        self.mapa: dict[int, Provincia] = mapa or {}
        self.naciones: dict[int, Nacion] = naciones or {}
        self.gobernantes: dict[int, Gobernante] = gobernantes or {}
        self.relaciones: dict[tuple[int, int], RelacionDiplomatica] = relaciones or {}

        # Handlers de despacho configurables
        self._handlers_estaticos: dict[TipoEvento, HandlerEvento] = {}
        self._handlers_ordenados: dict[TipoEvento, HandlerEvento] = {}
        self._hooks_fin_turno: list[HandlerFinTurno] = []
        self._verificador_victoria: Optional[HandlerVerificarVictoria] = None

    # --- Registro de Handlers y Hooks ---

    def registrar_handler_estatico(self, tipo: TipoEvento, handler: HandlerEvento) -> None:
        """Registra una función para despachar un tipo específico de orden estática."""
        self._handlers_estaticos[tipo] = handler

    def registrar_handler_ordenado(self, tipo: TipoEvento, handler: HandlerEvento) -> None:
        """Registra una función para despachar un tipo específico de orden ordenada."""
        self._handlers_ordenados[tipo] = handler

    def registrar_hook_fin_turno(self, hook: HandlerFinTurno) -> None:
        """Registra un cálculo endógeno de fin de turno (economía, atrición, etc.)."""
        self._hooks_fin_turno.append(hook)

    def set_verificador_victoria(self, verificador: HandlerVerificarVictoria) -> None:
        """Configura la función evaluadora de fin de partida."""
        self._verificador_victoria = verificador

    # --- Planificación de Órdenes en la FEL ---

    def planificar_orden(
        self,
        fase: FaseOrden,
        id_nacion: int,
        tipo_evento: TipoEvento,
        origen: int,
        destino: Optional[int] = None,
        prioridad_nacion: int = 1,
        datos: Optional[dict[str, Any]] = None,
        turno: Optional[int] = None,
    ) -> Evento:
        """Encola una nueva orden para el turno actual (o uno específico)."""
        t = self.turno_actual if turno is None else turno
        return self.fel.encolar_orden(
            turno=t,
            fase=fase,
            id_nacion=id_nacion,
            tipo_evento=tipo_evento,
            origen=origen,
            destino=destino,
            prioridad_nacion=prioridad_nacion,
            datos=datos,
        )

    # --- Ejecución del Ciclo WEGO ---

    def ejecutar_fase_estatica(self, turno: int) -> list[Evento]:
        """
        Fase 1: Procesa órdenes estáticas del turno (reclutamiento, fortificación, etc.).
        No dependen de posiciones geográficas de otros jugadores.
        """
        ordenes = self.fel.filtrar_ordenes_estaticas(turno)
        procesados: list[Evento] = []
        for evento in ordenes:
            handler = self._handlers_estaticos.get(evento.tipo_evento)
            if handler:
                handler(evento, self)
            procesados.append(evento)
        return procesados

    def ejecutar_fase_ordenada(self, turno: int) -> list[Evento]:
        """
        Fase 2: Procesa órdenes ordenadas (movimientos, ataques, etc.)
        utilizando el algoritmo Round-Robin regulado por el Ranking de Debilidad
        (la nación más débil actúa primero y cede el turno tras cada movimiento/ataque).
        """
        ordenes = self.fel.filtrar_ordenes_ordenadas(turno)
        ranking = calcular_ranking_debilidad(self.naciones, self.mapa)

        def despachar(evento: Evento) -> None:
            handler = self._handlers_ordenados.get(evento.tipo_evento)
            if handler:
                handler(evento, self)

        return ejecutar_round_robin(ranking, ordenes, ejecutor_orden=despachar)

    def ejecutar_fase_endogena(self, turno: int) -> list[Evento]:
        """
        Fase 3: Cálculos de fin de turno del motor de simulación.
        Ejecuta los hooks registrados (crecimiento, economía, atrición, revueltas).
        """
        for hook in self._hooks_fin_turno:
            hook(turno, self)

        evento_endogeno = Evento(
            turno=turno,
            prioridad_nacion=0,
            fase=FaseOrden.ENDOGENA,
            id_nacion=0,
            tipo_evento=TipoEvento.FIN_TURNO_ECONOMIA,
            origen=0,
        )
        return [evento_endogeno]

    def avanzar_reloj(self) -> int:
        """Incrementa el reloj discreto de la simulación t = t + 1."""
        self.turno_actual += 1
        return self.turno_actual

    def ejecutar_ciclo_turno(self) -> ResultadoTurno:
        """
        Ejecuta el ciclo completo WEGO para el turno actual:
        1. Fase estática
        2. Fase ordenada
        3. Fase endógena
        4. Verificación de victoria
        5. Avance del reloj
        """
        turno = self.turno_actual
        resultado = ResultadoTurno(turno=turno)

        # 1. Órdenes estáticas
        resultado.eventos_estaticos_procesados = self.ejecutar_fase_estatica(turno)

        # 2. Órdenes ordenadas
        resultado.eventos_ordenados_procesados = self.ejecutar_fase_ordenada(turno)

        # 3. Cálculos endógenos de fin de turno
        resultado.eventos_endogenos_procesados = self.ejecutar_fase_endogena(turno)

        # 4. Verificación de victoria
        if self._verificador_victoria:
            ganador = self._verificador_victoria(self)
            if ganador is not None:
                resultado.partida_finalizada = True
                resultado.ganador = ganador

        # 5. Avance del reloj
        self.avanzar_reloj()

        return resultado
