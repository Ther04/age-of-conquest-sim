"""
Submodelo de Evaluación de Condiciones de Victoria y Fin de Partida.

Ver:
- Game Manual, sección "Objectives":
  - Supremacy: Control a majority of the map (>50% of provinces).
  - Domination: Control the whole map (100% of provinces).
  - Annihilation: Eliminate all enemy troops/nations (last active nation).
  - Capture the Flag: Control a target location for N consecutive turns.
  - Defense: Defense vs Offense with limited turns.
  - 100 Victory Points: Reaching 100 VP.
  - Tie/Loss: Turn limit reached without victory.
- Modelo Conceptual de Simulación - Age of Conquest, secciones 2.8, 4.5, 8 y 9.8.
- Formalización Cuantitativa, sección "Condiciones de Frontera y Puntos Críticos".
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from src.entidades.nacion import Nacion
from src.entidades.provincia import Provincia
from src.parametros import TOTAL_PROVINCES, VICTORY_POINTS_TO_WIN


class TipoObjetivo(Enum):
    SUPREMACIA = "supremacia"
    DOMINACION = "dominacion"
    ANIQUILACION = "aniquilacion"
    PUNTOS_VICTORIA = "puntos_victoria"
    CAPTURA_BANDERA = "captura_bandera"
    DEFENSA = "defensa"


class EstadoPartida(Enum):
    EN_CURSO = "en_curso"
    VICTORIA = "victoria"
    EMPATE_DERROTA = "empate_derrota"


@dataclass
class ResultadoVictoria:
    """Resultado de la evaluación de condiciones de victoria."""
    estado: EstadoPartida = EstadoPartida.EN_CURSO
    ganador: Optional[int] = None
    motivo: str = ""
    detalles: dict[str, Any] = field(default_factory=dict)

    def hay_ganador(self) -> bool:
        return self.estado == EstadoPartida.VICTORIA and self.ganador is not None

    def ha_terminado(self) -> bool:
        return self.estado in (EstadoPartida.VICTORIA, EstadoPartida.EMPATE_DERROTA)


class EvaluadorVictoria:
    """
    Evalúa si se ha cumplido alguna condición de victoria global o específica del modo de juego.
    """

    def __init__(
        self,
        objetivo: TipoObjetivo = TipoObjetivo.SUPREMACIA,
        total_provincias: int = TOTAL_PROVINCES,
        limite_turnos: Optional[int] = None,
        provincia_bandera: Optional[int] = None,
        turnos_requeridos_bandera: int = 5,
        id_defensor_modo_defensa: Optional[int] = None,
    ) -> None:
        self.objetivo: TipoObjetivo = objetivo
        self.total_provincias: int = total_provincias
        self.limite_turnos: Optional[int] = limite_turnos
        self.provincia_bandera: Optional[int] = provincia_bandera
        self.turnos_requeridos_bandera: int = turnos_requeridos_bandera
        self.id_defensor_modo_defensa: Optional[int] = id_defensor_modo_defensa

        # Contadores de estado para modos especiales
        self._turnos_control_bandera: dict[int, int] = {}

    def evaluar(
        self,
        naciones: dict[int, Nacion],
        mapa: dict[int, Provincia],
        turno_actual: int,
    ) -> ResultadoVictoria:
        """
        Evalúa el estado actual de la partida.

        Prioridad de evaluación:
        1. Victoria universal por 100 Puntos de Victoria (Game Manual §Objectives).
        2. Objetivo específico de la partida (Supremacía, Dominación, Aniquilación, etc.).
        3. Límite de turnos alcanzado (Empate / Derrota).
        4. Continuar (En Curso).
        """
        naciones_activas = [n for n in naciones.values() if n.activa]

        # 1. Chequeo universal: 100 Puntos de Victoria
        for nacion in naciones_activas:
            if nacion.puntos_victoria >= VICTORY_POINTS_TO_WIN:
                return ResultadoVictoria(
                    estado=EstadoPartida.VICTORIA,
                    ganador=nacion.id_nacion,
                    motivo=f"Alcanzó {nacion.puntos_victoria} puntos de victoria (mínimo {VICTORY_POINTS_TO_WIN}).",
                )

        # 2. Chequeo por objetivo de la partida
        if self.objetivo == TipoObjetivo.ANIQUILACION:
            if len(naciones_activas) == 1:
                ganador = naciones_activas[0]
                return ResultadoVictoria(
                    estado=EstadoPartida.VICTORIA,
                    ganador=ganador.id_nacion,
                    motivo="Aniquilación: Es la última nación en pie sobre el mapa.",
                )
            elif len(naciones_activas) == 0:
                return ResultadoVictoria(
                    estado=EstadoPartida.EMPATE_DERROTA,
                    ganador=None,
                    motivo="Aniquilación: Todas las naciones fueron eliminadas.",
                )

        elif self.objetivo == TipoObjetivo.DOMINACION:
            for nacion in naciones_activas:
                if len(nacion.provincias) >= self.total_provincias:
                    return ResultadoVictoria(
                        estado=EstadoPartida.VICTORIA,
                        ganador=nacion.id_nacion,
                        motivo=f"Dominación: Controla el 100% del mapa ({len(nacion.provincias)}/{self.total_provincias} provincias).",
                    )

        elif self.objetivo == TipoObjetivo.SUPREMACIA:
            for nacion in naciones_activas:
                # Mayoría estricta: > 50% de las provincias totales
                if len(nacion.provincias) * 2 > self.total_provincias:
                    return ResultadoVictoria(
                        estado=EstadoPartida.VICTORIA,
                        ganador=nacion.id_nacion,
                        motivo=f"Supremacía: Controla la mayoría del mapa ({len(nacion.provincias)}/{self.total_provincias} provincias, >50%).",
                    )

        elif self.objetivo == TipoObjetivo.CAPTURA_BANDERA:
            if self.provincia_bandera is not None:
                prov_bandera = mapa.get(self.provincia_bandera)
                if prov_bandera and prov_bandera.propietario is not None:
                    dueno = prov_bandera.propietario
                    self._turnos_control_bandera[dueno] = self._turnos_control_bandera.get(dueno, 0) + 1
                    # Resetear a las demás naciones
                    for n_id in list(self._turnos_control_bandera.keys()):
                        if n_id != dueno:
                            self._turnos_control_bandera[n_id] = 0

                    if self._turnos_control_bandera[dueno] >= self.turnos_requeridos_bandera:
                        return ResultadoVictoria(
                            estado=EstadoPartida.VICTORIA,
                            ganador=dueno,
                            motivo=f"Captura de Bandera: Mantuvo el control de la provincia {self.provincia_bandera} por {self.turnos_requeridos_bandera} turnos consecutivos.",
                        )

        elif self.objetivo == TipoObjetivo.DEFENSA:
            if self.limite_turnos is not None and turno_actual >= self.limite_turnos:
                if self.id_defensor_modo_defensa is not None:
                    defensor = naciones.get(self.id_defensor_modo_defensa)
                    if defensor and defensor.activa:
                        return ResultadoVictoria(
                            estado=EstadoPartida.VICTORIA,
                            ganador=self.id_defensor_modo_defensa,
                            motivo=f"Defensa: Sobrevivió el límite de {self.limite_turnos} turnos.",
                        )

        # 3. Chequeo por límite de turnos alcanzado
        if self.limite_turnos is not None and turno_actual >= self.limite_turnos:
            return ResultadoVictoria(
                estado=EstadoPartida.EMPATE_DERROTA,
                ganador=None,
                motivo=f"Se alcanzó el límite de turnos ({self.limite_turnos}) sin que ninguna nación cumpliera el objetivo.",
            )

        # 4. La partida continúa
        return ResultadoVictoria(estado=EstadoPartida.EN_CURSO)


# Función utilitaria de evaluación directa
def verificar_victoria(
    naciones: dict[int, Nacion],
    mapa: dict[int, Provincia],
    turno_actual: int,
    objetivo: TipoObjetivo = TipoObjetivo.SUPREMACIA,
    total_provincias: int = TOTAL_PROVINCES,
    limite_turnos: Optional[int] = None,
) -> ResultadoVictoria:
    """Función de conveniencia para evaluar condiciones de victoria en un paso."""
    evaluador = EvaluadorVictoria(
        objetivo=objetivo,
        total_provincias=total_provincias,
        limite_turnos=limite_turnos,
    )
    return evaluador.evaluar(naciones, mapa, turno_actual)
