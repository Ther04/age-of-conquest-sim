"""
Pruebas unitarias para el ciclo principal de turnos en modo WEGO.
"""

import unittest
from src.motor.ciclo_wego import MotorSimulacionWEGO
from src.motor.fel import FaseOrden, TipoEvento


class TestCicloWEGO(unittest.TestCase):

    def test_flujo_ciclo_wego_y_avance_reloj(self):
        motor = MotorSimulacionWEGO(turno_inicial=1)

        # Planificar órdenes en la FEL para el turno 1
        motor.planificar_orden(
            fase=FaseOrden.ESTATICA,
            id_nacion=1,
            tipo_evento=TipoEvento.RECLUTAR,
            origen=1,
        )
        motor.planificar_orden(
            fase=FaseOrden.ORDENADA,
            id_nacion=1,
            tipo_evento=TipoEvento.MOVIMIENTO,
            origen=1,
            destino=2,
        )

        # Registrar hooks/handlers para verificar ejecución
        eventos_estaticos_ejecutados = []
        eventos_ordenados_ejecutados = []
        fin_turno_ejecutado = []

        def handler_reclutar(evento, m):
            eventos_estaticos_ejecutados.append(evento)

        def handler_movimiento(evento, m):
            eventos_ordenados_ejecutados.append(evento)

        def hook_fin_turno(turno, m):
            fin_turno_ejecutado.append(turno)

        motor.registrar_handler_estatico(TipoEvento.RECLUTAR, handler_reclutar)
        motor.registrar_handler_ordenado(TipoEvento.MOVIMIENTO, handler_movimiento)
        motor.registrar_hook_fin_turno(hook_fin_turno)

        # Ejecutar el turno 1
        self.assertEqual(motor.turno_actual, 1)
        resultado = motor.ejecutar_ciclo_turno()

        # Validaciones del resultado
        self.assertEqual(resultado.turno, 1)
        self.assertEqual(len(resultado.eventos_estaticos_procesados), 1)
        self.assertEqual(len(resultado.eventos_ordenados_procesados), 1)
        self.assertEqual(len(eventos_estaticos_ejecutados), 1)
        self.assertEqual(len(eventos_ordenados_ejecutados), 1)
        self.assertEqual(fin_turno_ejecutado, [1])

        # El reloj debe haber avanzado al turno 2
        self.assertEqual(motor.turno_actual, 2)
        # La FEL del turno 1 debe estar vacía
        self.assertTrue(motor.fel.esta_vacia())


if __name__ == "__main__":
    unittest.main()
