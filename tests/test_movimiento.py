"""
Pruebas unitarias para el submodelo de movimiento de tropas y bloqueo naval.
"""

import unittest
from src.combate.movimiento import ejecutar_movimiento_tropas
from src.diplomacia.gestor_diplomacia import GestorDiplomacia
from src.entidades.gobernante import Gobernante
from src.entidades.nacion import Nacion
from src.entidades.provincia import Provincia
from src.entidades.relacion_diplomatica import TipoRelacion


class TestMovimientoYBloqueoNaval(unittest.TestCase):

    def setUp(self):
        # Crear mapa de 3 provincias en línea: 1 <-> 2 <-> 3
        self.prov1 = Provincia(id_provincia=1, propietario=1, tropas=100, vecinos=[2])
        self.prov2 = Provincia(id_provincia=2, propietario=1, tropas=50, vecinos=[1, 3])
        self.prov3 = Provincia(id_provincia=3, propietario=2, tropas=40, vecinos=[2])
        self.mapa = {1: self.prov1, 2: self.prov2, 3: self.prov3}

        self.n1 = Nacion(id_nacion=1, nombre="Nacion 1", provincias={1, 2})
        self.n2 = Nacion(id_nacion=2, nombre="Nacion 2", provincias={3})
        self.naciones = {1: self.n1, 2: self.n2}

        self.gestor = GestorDiplomacia()

    def test_movimiento_pacifico_territorio_propio(self):
        # Mover 40 tropas de prov 1 a prov 2
        res = ejecutar_movimiento_tropas(
            origen_id=1,
            destino_id=2,
            id_nacion=1,
            cantidad_tropas=40,
            mapa=self.mapa,
            naciones=self.naciones,
            gestor_diplomacia=self.gestor,
        )

        self.assertTrue(res.exito)
        self.assertFalse(res.hubo_combate)
        self.assertEqual(self.prov1.tropas, 60)
        self.assertEqual(self.prov2.tropas, 90)

    def test_bloqueo_movimiento_a_otra_nacion_sin_guerra_modo_estandar(self):
        # Intentar entrar a prov 3 (de n2) estando en NEUTRAL
        res = ejecutar_movimiento_tropas(
            origen_id=2,
            destino_id=3,
            id_nacion=1,
            cantidad_tropas=30,
            mapa=self.mapa,
            naciones=self.naciones,
            gestor_diplomacia=self.gestor,
            modo_open_travel=False,
        )

        self.assertFalse(res.exito)
        # Las tropas de origen no se pierden
        self.assertEqual(self.prov2.tropas, 50)

    def test_ataque_a_enemigo_en_guerra(self):
        # Establecer guerra entre n1 y n2
        rel = self.gestor.obtener_relacion(1, 2)
        rel.tipo = TipoRelacion.GUERRA

        # Atacar prov 3 con 50 tropas de prov 2 (defensa tiene 40 tropas)
        res = ejecutar_movimiento_tropas(
            origen_id=2,
            destino_id=3,
            id_nacion=1,
            cantidad_tropas=50,
            mapa=self.mapa,
            naciones=self.naciones,
            gestor_diplomacia=self.gestor,
        )

        self.assertTrue(res.exito)
        self.assertTrue(res.hubo_combate)
        self.assertIsNotNone(res.resultado_combate)
        self.assertEqual(res.resultado_combate.ganador, 1)
        self.assertEqual(self.prov3.propietario, 1)
        self.assertIn(3, self.n1.provincias)
        self.assertNotIn(3, self.n2.provincias)

    def test_bloqueo_naval_detiene_movimiento_tras_combate(self):
        rel = self.gestor.obtener_relacion(1, 2)
        rel.tipo = TipoRelacion.GUERRA
        self.prov2.tropas = 100

        # Atacante: 70 tropas con -30% naval -> FC_A = 70 * 70 = 4900
        # Defensor: 40 tropas sin muralla -> FC_D = 40 * 100 = 4000
        # Gana atacante y el barco detiene su avance en la provincia de batalla
        res = ejecutar_movimiento_tropas(
            origen_id=2,
            destino_id=3,
            id_nacion=1,
            cantidad_tropas=70,
            mapa=self.mapa,
            naciones=self.naciones,
            gestor_diplomacia=self.gestor,
            es_naval=True,
        )

        self.assertTrue(res.exito)
        self.assertTrue(res.hubo_combate)
        self.assertEqual(res.resultado_combate.ganador, 1)
        # En combate naval victorioso, el movimiento se detiene en la provincia de batalla
        self.assertTrue(res.movimiento_detenido)

    def test_gobernante_se_desplaza_con_el_ejercito(self):
        rey1 = Gobernante(id_gobernante=1, nacion_propietaria=1, provincia_actual=1, vivo=True)
        gobernantes = {1: rey1}

        res = ejecutar_movimiento_tropas(
            origen_id=1,
            destino_id=2,
            id_nacion=1,
            cantidad_tropas=20,
            mapa=self.mapa,
            naciones=self.naciones,
            gobernantes=gobernantes,
            gestor_diplomacia=self.gestor,
            acompanar_gobernante=True,
        )

        self.assertTrue(res.exito)
        self.assertEqual(rey1.provincia_actual, 2)


if __name__ == "__main__":
    unittest.main()
