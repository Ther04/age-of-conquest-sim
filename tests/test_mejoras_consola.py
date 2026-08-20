"""
Pruebas de las mejoras de consola y usabilidad:
- Gestión interactiva de tratados diplomáticos (proponer, aceptar, rechazar).
- Desglose financiero y actualización de estado en partida.
"""

import unittest
from io import StringIO
import sys

from src.simulacion import (
    crear_partida_demo,
    proponer_tratado,
    aceptar_tratado,
    rechazar_tratado,
    ejecutar_n_turnos,
)
from src.entidades.relacion_diplomatica import TipoRelacion


class TestMejorasConsola(unittest.TestCase):

    def test_flujo_propuesta_y_aceptacion_alianza(self):
        """Una propuesta de alianza debe guardarse en pendientes y formalizarse al aceptarla."""
        partida = crear_partida_demo(["Rojo", "Azul", "Verde"], num_provincias=9)

        # Rojo (1) propone alianza a Azul (2)
        proponer_tratado(partida, id_origen=1, id_destino=2, tipo="alianza")
        self.assertIn(2, partida.propuestas_pendientes)
        self.assertEqual(partida.propuestas_pendientes[2], [("alianza", 1)])

        # Azul (2) acepta la alianza en turno 1
        exito = aceptar_tratado(partida, id_receptor=2, id_origen=1, tipo="alianza", turno=1)
        self.assertTrue(exito)
        self.assertEqual(len(partida.propuestas_pendientes[2]), 0)

        # Verificar relación diplomática
        rel = partida.gestor_diplomacia.obtener_relacion(1, 2)
        self.assertEqual(rel.tipo, TipoRelacion.ALIANZA)

    def test_flujo_rechazo_propuesta_paz(self):
        """Una propuesta rechazada debe eliminarse de pendientes sin alterar la relación."""
        partida = crear_partida_demo(["Rojo", "Azul", "Verde"], num_provincias=9)

        proponer_tratado(partida, id_origen=1, id_destino=3, tipo="paz")
        self.assertEqual(len(partida.propuestas_pendientes[3]), 1)

        exito = rechazar_tratado(partida, id_receptor=3, id_origen=1, tipo="paz")
        self.assertTrue(exito)
        self.assertEqual(len(partida.propuestas_pendientes[3]), 0)

        # Relación debe permanecer Neutral
        rel = partida.gestor_diplomacia.obtener_relacion(1, 3)
        self.assertEqual(rel.tipo, TipoRelacion.NEUTRAL)

    def test_desglose_financiero_en_fin_de_turno(self):
        """El hook de fin de turno debe imprimir el desglose financiero sin errores."""
        partida = crear_partida_demo(["Rojo", "Azul"], num_provincias=6)

        captured_output = StringIO()
        sys_stdout_backup = sys.stdout
        sys.stdout = captured_output
        try:
            ejecutar_n_turnos(partida, 2)
        finally:
            sys.stdout = sys_stdout_backup

        salida = captured_output.getvalue()
        self.assertIn("[Turno 1 - Finanzas]", salida)
        self.assertIn("Ingreso Bruto:", salida)
        self.assertIn("Mantenimiento:", salida)


if __name__ == "__main__":
    unittest.main()
