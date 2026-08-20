"""
Pruebas unitarias para el submodelo de declaración de guerra y penalizaciones de felicidad.
"""

import unittest
from src.diplomacia.declaracion_guerra import (
    aplicar_penalizacion_recurrente_guerras,
    calcular_penalizacion_declaracion_guerra,
    calcular_penalizacion_recurrente_guerra,
    declarar_guerra,
)
from src.entidades.nacion import Nacion
from src.entidades.provincia import Provincia
from src.entidades.relacion_diplomatica import RelacionDiplomatica, TipoRelacion


class TestDeclaracionGuerra(unittest.TestCase):

    def test_calculo_penalizaciones_declaracion(self):
        # 1. Base: -4%
        self.assertEqual(calcular_penalizacion_declaracion_guerra(guerras_activas_rival=0, es_multiguerra=False), -4)

        # 2. Rival con 1 guerra activa: -4 + (-8 * 1) = -12%
        self.assertEqual(calcular_penalizacion_declaracion_guerra(guerras_activas_rival=1, es_multiguerra=False), -12)

        # 3. Rival con 2 guerras activas y es 2da declaración en el turno: -4 + (-8 * 2) - 10 = -30%
        self.assertEqual(calcular_penalizacion_declaracion_guerra(guerras_activas_rival=2, es_multiguerra=True), -30)

    def test_calculo_penalizacion_recurrente(self):
        self.assertEqual(calcular_penalizacion_recurrente_guerra(0), 0)
        self.assertEqual(calcular_penalizacion_recurrente_guerra(1), -1)
        self.assertEqual(calcular_penalizacion_recurrente_guerra(2), -2)
        self.assertEqual(calcular_penalizacion_recurrente_guerra(3), -3)
        self.assertEqual(calcular_penalizacion_recurrente_guerra(5), -3)  # Tope de -3%

    def test_flujo_declaracion_guerra_exitoso(self):
        prov1 = Provincia(id_provincia=1, propietario=1, felicidad=80)
        prov2 = Provincia(id_provincia=2, propietario=2, felicidad=70)
        mapa = {1: prov1, 2: prov2}

        n1 = Nacion(id_nacion=1, nombre="Atacante", provincias={1}, felicidad_promedio=80)
        n2 = Nacion(id_nacion=2, nombre="Defensor", provincias={2}, felicidad_promedio=70, guerras_activas=1)
        relacion = RelacionDiplomatica(nacion_a=1, nacion_b=2, tipo=TipoRelacion.NEUTRAL)

        # n1 declara guerra a n2 (n2 ya tiene 1 guerra activa) -> penalización = -12%
        res = declarar_guerra(n1, n2, relacion, mapa, declaraciones_en_turno=1, turno_actual=3)

        self.assertEqual(res["penalizacion_aplicada"], -12)
        self.assertEqual(relacion.tipo, TipoRelacion.GUERRA)
        self.assertEqual(n1.guerras_activas, 1)
        self.assertEqual(n2.guerras_activas, 2)
        # Felicidad de n1 baja en 12% (80 -> 68)
        self.assertEqual(prov1.felicidad, 68)
        self.assertEqual(n1.felicidad_promedio, 68)
        # Felicidad de n2 no cambia inmediatamente por ser el objetivo atacado
        self.assertEqual(prov2.felicidad, 70)
        self.assertEqual(n2.felicidad_promedio, 70)

    def test_bloqueo_declaracion_si_no_es_neutral_o_hay_ceasefire(self):
        mapa = {}
        n1 = Nacion(id_nacion=1, nombre="N1", provincias=set())
        n2 = Nacion(id_nacion=2, nombre="N2", provincias=set())

        # Caso 1: En Alianza
        rel_alianza = RelacionDiplomatica(nacion_a=1, nacion_b=2, tipo=TipoRelacion.ALIANZA)
        with self.assertRaises(ValueError):
            declarar_guerra(n1, n2, rel_alianza, mapa)

        # Caso 2: Ceasefire activo
        rel_ceasefire = RelacionDiplomatica(nacion_a=1, nacion_b=2, tipo=TipoRelacion.NEUTRAL, turnos_ceasefire_restante=2)
        with self.assertRaises(ValueError):
            declarar_guerra(n1, n2, rel_ceasefire, mapa)

    def test_penalizacion_recurrente_hook(self):
        prov1 = Provincia(id_provincia=1, propietario=1, felicidad=50)
        mapa = {1: prov1}
        n1 = Nacion(id_nacion=1, nombre="N1", provincias={1}, felicidad_promedio=50, guerras_activas=2)

        # 2 guerras activas -> -2% de felicidad recurrente
        aplicar_penalizacion_recurrente_guerras({1: n1}, mapa)
        self.assertEqual(prov1.felicidad, 48)
        self.assertEqual(n1.felicidad_promedio, 48)


if __name__ == "__main__":
    unittest.main()
