"""
Pruebas unitarias para el submodelo de resolución de combate Lanchester discreto.
"""

import unittest
from src.combate.lanchester import (
    calcular_fuerza_atacante,
    calcular_fuerza_defensora,
    resolver_combate,
)
from src.entidades.gobernante import Gobernante
from src.entidades.nacion import Nacion
from src.entidades.provincia import Provincia


class TestCombateLanchester(unittest.TestCase):

    def test_calculo_fuerzas_con_bonos(self):
        # 17 soldados, sin bonos
        self.assertEqual(calcular_fuerza_atacante(17, gobernante_presente=False, es_naval=False), 1700)
        self.assertEqual(calcular_fuerza_defensora(17, tiene_muralla=False, gobernante_presente=False), 1700)

        # Atacante con Rey (+100%): 17 * 200 = 3400
        self.assertEqual(calcular_fuerza_atacante(17, gobernante_presente=True, es_naval=False), 3400)

        # Atacante con Rey (+100%) y Naval (-30%): 17 * (100 + 100 - 30) = 17 * 170 = 2890
        self.assertEqual(calcular_fuerza_atacante(17, gobernante_presente=True, es_naval=True), 2890)

        # Defensor con Muralla (+100%) y Rey (+30%): 17 * (100 + 100 + 30) = 17 * 230 = 3910
        self.assertEqual(calcular_fuerza_defensora(17, tiene_muralla=True, gobernante_presente=True), 3910)

    def test_combate_victoria_atacante_sin_reyes(self):
        # Atacante: 100 tropas (FC_A = 10000)
        # Defensor: 50 tropas (FC_D = 5000)
        # Gana atacante: floor(100 * (1 - 5000/10000)) = 100 * 0.5 = 50 sobrevivientes
        provincia = Provincia(id_provincia=1, propietario=2, tropas=50, muralla=False)
        nacion_atk = Nacion(id_nacion=1, nombre="N1", provincias=set(), felicidad_promedio=50)
        nacion_def = Nacion(id_nacion=2, nombre="N2", provincias={1}, felicidad_promedio=50)

        resultado = resolver_combate(
            provincia=provincia,
            nacion_atk=nacion_atk,
            nacion_def=nacion_def,
            tropas_atk=100,
        )

        self.assertEqual(resultado.ganador, 1)
        self.assertEqual(resultado.perdedor, 2)
        self.assertEqual(resultado.tropas_sobrevivientes, 50)
        self.assertEqual(provincia.tropas, 50)
        self.assertEqual(provincia.propietario, 1)
        self.assertTrue(resultado.cambio_propietario)
        self.assertEqual(nacion_atk.felicidad_promedio, 51)
        self.assertEqual(nacion_def.felicidad_promedio, 49)
        self.assertFalse(resultado.jaque_mate)

    def test_combate_jaque_mate_muerte_rey_defensor(self):
        # Defensor pierde y su rey estaba en la provincia
        provincia = Provincia(id_provincia=1, propietario=2, tropas=10, muralla=False)
        provincia_2 = Provincia(id_provincia=2, propietario=2, tropas=100, muralla=False)
        mapa = {1: provincia, 2: provincia_2}

        nacion_atk = Nacion(id_nacion=1, nombre="N1", provincias=set(), felicidad_promedio=50)
        nacion_def = Nacion(id_nacion=2, nombre="N2", provincias={1, 2}, felicidad_promedio=50)
        rey_def = Gobernante(id_gobernante=2, nacion_propietaria=2, provincia_actual=1, vivo=True)

        resultado = resolver_combate(
            provincia=provincia,
            nacion_atk=nacion_atk,
            nacion_def=nacion_def,
            tropas_atk=50,
            gobernante_def_presente=True,
            gobernante_def=rey_def,
            mapa=mapa,
        )

        self.assertEqual(resultado.ganador, 1)
        self.assertTrue(resultado.jaque_mate)
        self.assertFalse(rey_def.vivo)
        self.assertFalse(nacion_def.activa)
        # Todas las tierras de nacion_def se transfirieron a nacion_atk
        self.assertEqual(nacion_def.provincias, set())
        self.assertEqual(nacion_atk.provincias, {1, 2})
        self.assertEqual(provincia_2.propietario, 1)


if __name__ == "__main__":
    unittest.main()
