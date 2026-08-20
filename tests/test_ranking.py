"""
Pruebas unitarias para el cálculo del ranking de debilidad de naciones.
"""

import unittest
from src.entidades.nacion import Nacion
from src.entidades.provincia import Provincia
from src.motor.ranking import (
    asignar_prioridades_ranking,
    calcular_ranking_debilidad,
    calcular_tropas_totales_nacion,
)


class TestRankingDebilidad(unittest.TestCase):

    def setUp(self):
        # Crear 6 provincias
        self.mapa = {
            1: Provincia(id_provincia=1, propietario=1, tropas=100),
            2: Provincia(id_provincia=2, propietario=1, tropas=200),
            3: Provincia(id_provincia=3, propietario=2, tropas=50),
            4: Provincia(id_provincia=4, propietario=3, tropas=500),
            5: Provincia(id_provincia=5, propietario=3, tropas=500),
            6: Provincia(id_provincia=6, propietario=3, tropas=500),
        }

        # Nación 1: 2 provincias, 300 tropas, 100 oro
        self.nacion_1 = Nacion(id_nacion=1, nombre="Nación A", provincias={1, 2}, tesoreria=100)
        # Nación 2: 1 provincia, 50 tropas, 50 oro (la más débil)
        self.nacion_2 = Nacion(id_nacion=2, nombre="Nación B", provincias={3}, tesoreria=50)
        # Nación 3: 3 provincias, 1500 tropas, 500 oro (la más fuerte)
        self.nacion_3 = Nacion(id_nacion=3, nombre="Nación C", provincias={4, 5, 6}, tesoreria=500)

        self.naciones = {
            1: self.nacion_1,
            2: self.nacion_2,
            3: self.nacion_3,
        }

    def test_ranking_orden_debilidad(self):
        # El ranking debe ordenar: Nación 2 (más débil) -> Nación 1 -> Nación 3 (más fuerte)
        ranking = calcular_ranking_debilidad(self.naciones, self.mapa)
        self.assertEqual(ranking, [2, 1, 3])

    def test_desempate_por_tropas_y_tesoreria(self):
        # Mismo número de provincias (1 cada una), pero diferente tropa/tesorería
        mapa = {
            1: Provincia(id_provincia=1, propietario=1, tropas=200),
            2: Provincia(id_provincia=2, propietario=2, tropas=100),
            3: Provincia(id_provincia=3, propietario=3, tropas=100),
        }
        n1 = Nacion(id_nacion=1, nombre="N1", provincias={1}, tesoreria=50)
        n2 = Nacion(id_nacion=2, nombre="N2", provincias={2}, tesoreria=100)
        n3 = Nacion(id_nacion=3, nombre="N3", provincias={3}, tesoreria=20)  # Menos oro que N2

        naciones = {1: n1, 2: n2, 3: n3}
        # N3 y N2 tienen 100 tropas, pero N3 tiene menos oro (20 vs 100) -> N3 es más débil que N2
        # N1 tiene más tropas (200) -> N1 es la más fuerte
        ranking = calcular_ranking_debilidad(naciones, mapa)
        self.assertEqual(ranking, [3, 2, 1])

    def test_excluir_naciones_eliminadas(self):
        self.nacion_2.activa = False  # Nación 2 eliminada
        ranking = calcular_ranking_debilidad(self.naciones, self.mapa, solo_activas=True)
        self.assertEqual(ranking, [1, 3])

    def test_asignar_prioridades_ranking(self):
        prioridades = asignar_prioridades_ranking(self.naciones, self.mapa)
        # Nación 2 es la más débil -> prioridad 1
        self.assertEqual(prioridades[2], 1)
        # Nación 1 es intermedia -> prioridad 2
        self.assertEqual(prioridades[1], 2)
        # Nación 3 es la más fuerte -> prioridad 3
        self.assertEqual(prioridades[3], 3)


if __name__ == "__main__":
    unittest.main()
