"""
Pruebas unitarias para el gestor de diplomacia y transiciones de relaciones bilaterales.
"""

import unittest
from src.diplomacia.gestor_diplomacia import (
    DURACION_CEASEFIRE_ALIANZA,
    DURACION_CEASEFIRE_PAZ,
    GestorDiplomacia,
)
from src.entidades.nacion import Nacion
from src.entidades.relacion_diplomatica import TipoRelacion


class TestDiplomacia(unittest.TestCase):

    def setUp(self):
        self.gestor = GestorDiplomacia()
        self.n1 = Nacion(id_nacion=1, nombre="Nacion 1")
        self.n2 = Nacion(id_nacion=2, nombre="Nacion 2")

    def test_relacion_inicial_es_neutral(self):
        rel = self.gestor.obtener_relacion(1, 2)
        self.assertEqual(rel.tipo, TipoRelacion.NEUTRAL)
        self.assertEqual(rel.turnos_ceasefire_restante, 0)
        self.assertTrue(self.gestor.pueden_declararse_guerra(1, 2))

    def test_establecer_alianza_y_protectorado(self):
        # Alianza
        rel_alianza = self.gestor.establecer_alianza(1, 2, turno_actual=2)
        self.assertEqual(rel_alianza.tipo, TipoRelacion.ALIANZA)
        self.assertTrue(self.gestor.son_aliados(1, 2))
        self.assertFalse(self.gestor.pueden_declararse_guerra(1, 2))

        # Protectorado
        rel_prot = self.gestor.establecer_protectorado(1, 2, turno_actual=3)
        self.assertIn(rel_prot.tipo, (TipoRelacion.PROTECTOR, TipoRelacion.PROTECTORADO))
        self.assertTrue(self.gestor.son_aliados(1, 2))

    def test_cancelar_alianza_activa_ceasefire_2_turnos(self):
        self.gestor.establecer_alianza(1, 2, turno_actual=1)
        resultado = self.gestor.cancelar_relacion(1, 2, turno_actual=2)

        self.assertEqual(resultado["ceasefire_turnos"], DURACION_CEASEFIRE_ALIANZA)
        rel = self.gestor.obtener_relacion(1, 2)
        self.assertEqual(rel.tipo, TipoRelacion.CEASEFIRE)
        self.assertEqual(rel.turnos_ceasefire_restante, 2)
        self.assertFalse(self.gestor.pueden_declararse_guerra(1, 2))

        # Fin de turno 2: Ceasefire pasa de 2 a 1
        expirados = self.gestor.actualizar_ceasefires_fin_turno()
        self.assertEqual(len(expirados), 0)
        self.assertEqual(rel.turnos_ceasefire_restante, 1)
        self.assertEqual(rel.tipo, TipoRelacion.CEASEFIRE)
        self.assertFalse(self.gestor.pueden_declararse_guerra(1, 2))

        # Fin de turno 3: Ceasefire pasa de 1 a 0 y transiciona a NEUTRAL
        expirados = self.gestor.actualizar_ceasefires_fin_turno()
        self.assertEqual(len(expirados), 1)
        self.assertEqual(rel.turnos_ceasefire_restante, 0)
        self.assertEqual(rel.tipo, TipoRelacion.NEUTRAL)
        self.assertTrue(self.gestor.pueden_declararse_guerra(1, 2))

    def test_cancelar_paz_activa_ceasefire_1_turno(self):
        self.gestor.establecer_paz(1, 2, turno_actual=1)
        resultado = self.gestor.cancelar_relacion(1, 2, turno_actual=2)

        self.assertEqual(resultado["ceasefire_turnos"], DURACION_CEASEFIRE_PAZ)
        rel = self.gestor.obtener_relacion(1, 2)
        self.assertEqual(rel.turnos_ceasefire_restante, 1)

        # 1 turno después ya expira y pasa a NEUTRAL
        expirados = self.gestor.actualizar_ceasefires_fin_turno()
        self.assertEqual(len(expirados), 1)
        self.assertEqual(rel.tipo, TipoRelacion.NEUTRAL)
        self.assertTrue(self.gestor.pueden_declararse_guerra(1, 2))

    def test_firmar_paz_desde_guerra(self):
        rel = self.gestor.obtener_relacion(1, 2)
        rel.tipo = TipoRelacion.GUERRA
        self.n1.guerras_activas = 1
        self.n2.guerras_activas = 1

        self.gestor.firmar_paz_desde_guerra(1, 2, self.n1, self.n2, turno_actual=5)
        self.assertEqual(rel.tipo, TipoRelacion.PAZ)
        self.assertEqual(self.n1.guerras_activas, 0)
        self.assertEqual(self.n2.guerras_activas, 0)


if __name__ == "__main__":
    unittest.main()
