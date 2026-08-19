"""
Pruebas unitarias para el submodelo de evaluación de condiciones de victoria.
"""

import unittest
from src.entidades.nacion import Nacion
from src.entidades.provincia import Provincia
from src.motor.victoria import (
    EstadoPartida,
    EvaluadorVictoria,
    ResultadoVictoria,
    TipoObjetivo,
    verificar_victoria,
)


class TestVictoria(unittest.TestCase):

    def test_victoria_por_100_puntos_universal(self):
        # Incluso en modo Supremacía, si una nación llega a 100 VP gana de inmediato
        n1 = Nacion(id_nacion=1, nombre="N1", provincias={1}, puntos_victoria=100)
        n2 = Nacion(id_nacion=2, nombre="N2", provincias={2, 3, 4}, puntos_victoria=40)
        naciones = {1: n1, 2: n2}
        mapa = {}

        res = verificar_victoria(naciones, mapa, turno_actual=5, objetivo=TipoObjetivo.SUPREMACIA)
        self.assertEqual(res.estado, EstadoPartida.VICTORIA)
        self.assertEqual(res.ganador, 1)

    def test_victoria_por_supremacia(self):
        # Total 10 provincias. Mayoría > 50% = 6 provincias
        n1 = Nacion(id_nacion=1, nombre="N1", provincias={1, 2, 3, 4, 5, 6})
        n2 = Nacion(id_nacion=2, nombre="N2", provincias={7, 8, 9, 10})
        naciones = {1: n1, 2: n2}
        mapa = {}

        res = verificar_victoria(naciones, mapa, turno_actual=3, objetivo=TipoObjetivo.SUPREMACIA, total_provincias=10)
        self.assertEqual(res.estado, EstadoPartida.VICTORIA)
        self.assertEqual(res.ganador, 1)

    def test_supremacia_no_alcanzada_con_50_porciento_exacto(self):
        # 5 de 10 provincias no es mayoría estricta (>50%)
        n1 = Nacion(id_nacion=1, nombre="N1", provincias={1, 2, 3, 4, 5})
        n2 = Nacion(id_nacion=2, nombre="N2", provincias={6, 7, 8, 9, 10})
        naciones = {1: n1, 2: n2}
        mapa = {}

        res = verificar_victoria(naciones, mapa, turno_actual=3, objetivo=TipoObjetivo.SUPREMACIA, total_provincias=10)
        self.assertEqual(res.estado, EstadoPartida.EN_CURSO)
        self.assertIsNone(res.ganador)

    def test_victoria_por_dominacion_100_porciento(self):
        # Total 4 provincias. Requiere las 4
        n1 = Nacion(id_nacion=1, nombre="N1", provincias={1, 2, 3, 4})
        n2 = Nacion(id_nacion=2, nombre="N2", provincias=set(), activa=True)
        naciones = {1: n1, 2: n2}
        mapa = {}

        res = verificar_victoria(naciones, mapa, turno_actual=10, objetivo=TipoObjetivo.DOMINACION, total_provincias=4)
        self.assertEqual(res.estado, EstadoPartida.VICTORIA)
        self.assertEqual(res.ganador, 1)

    def test_victoria_por_aniquilacion(self):
        # Solo 1 nación activa
        n1 = Nacion(id_nacion=1, nombre="N1", activa=True)
        n2 = Nacion(id_nacion=2, nombre="N2", activa=False)
        n3 = Nacion(id_nacion=3, nombre="N3", activa=False)
        naciones = {1: n1, 2: n2, 3: n3}
        mapa = {}

        res = verificar_victoria(naciones, mapa, turno_actual=8, objetivo=TipoObjetivo.ANIQUILACION)
        self.assertEqual(res.estado, EstadoPartida.VICTORIA)
        self.assertEqual(res.ganador, 1)

    def test_empate_por_limite_de_turnos(self):
        n1 = Nacion(id_nacion=1, nombre="N1", provincias={1}, activa=True)
        n2 = Nacion(id_nacion=2, nombre="N2", provincias={2}, activa=True)
        naciones = {1: n1, 2: n2}
        mapa = {}

        # Turno 20 de 20 sin ganador
        res = verificar_victoria(naciones, mapa, turno_actual=20, objetivo=TipoObjetivo.SUPREMACIA, total_provincias=10, limite_turnos=20)
        self.assertEqual(res.estado, EstadoPartida.EMPATE_DERROTA)
        self.assertIsNone(res.ganador)

    def test_captura_de_bandera_consecutiva(self):
        evaluador = EvaluadorVictoria(
            objetivo=TipoObjetivo.CAPTURA_BANDERA,
            provincia_bandera=5,
            turnos_requeridos_bandera=3,
        )
        prov5 = Provincia(id_provincia=5, propietario=1)
        mapa = {5: prov5}
        naciones = {1: Nacion(id_nacion=1, nombre="N1", activa=True)}

        # Turno 1
        res1 = evaluador.evaluar(naciones, mapa, turno_actual=1)
        self.assertEqual(res1.estado, EstadoPartida.EN_CURSO)

        # Turno 2
        res2 = evaluador.evaluar(naciones, mapa, turno_actual=2)
        self.assertEqual(res2.estado, EstadoPartida.EN_CURSO)

        # Turno 3 (3 turnos consecutivos) -> Victoria
        res3 = evaluador.evaluar(naciones, mapa, turno_actual=3)
        self.assertEqual(res3.estado, EstadoPartida.VICTORIA)
        self.assertEqual(res3.ganador, 1)


if __name__ == "__main__":
    unittest.main()
