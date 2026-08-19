"""
Pruebas unitarias para el algoritmo Round-Robin de órdenes ordenadas.
"""

import unittest
from src.motor.fel import Evento, FaseOrden, TipoEvento
from src.motor.round_robin import ejecutar_round_robin, es_evento_de_cesion


class TestRoundRobin(unittest.TestCase):

    def test_es_evento_de_cesion(self):
        self.assertTrue(es_evento_de_cesion(TipoEvento.MOVIMIENTO))
        self.assertTrue(es_evento_de_cesion(TipoEvento.ATAQUE))
        self.assertFalse(es_evento_de_cesion(TipoEvento.DECLARAR_GUERRA))
        self.assertFalse(es_evento_de_cesion(TipoEvento.CANCELAR_RELACION))
        self.assertFalse(es_evento_de_cesion(TipoEvento.DISBAND))

    def test_alternancia_movimientos_round_robin(self):
        # Nación 1 es más débil (ranking [1, 2])
        ranking = [1, 2]

        ordenes = [
            Evento(turno=1, prioridad_nacion=1, fase=FaseOrden.ORDENADA, id_nacion=1, tipo_evento=TipoEvento.MOVIMIENTO, origen=1, destino=2),
            Evento(turno=1, prioridad_nacion=1, fase=FaseOrden.ORDENADA, id_nacion=1, tipo_evento=TipoEvento.MOVIMIENTO, origen=2, destino=3),
            Evento(turno=1, prioridad_nacion=2, fase=FaseOrden.ORDENADA, id_nacion=2, tipo_evento=TipoEvento.MOVIMIENTO, origen=10, destino=11),
            Evento(turno=1, prioridad_nacion=2, fase=FaseOrden.ORDENADA, id_nacion=2, tipo_evento=TipoEvento.MOVIMIENTO, origen=11, destino=12),
        ]

        ejecutados = ejecutar_round_robin(ranking, ordenes)

        # El orden debe alternar: Nación 1 (1er mov) -> Nación 2 (1er mov) -> Nación 1 (2do mov) -> Nación 2 (2do mov)
        self.assertEqual(len(ejecutados), 4)
        self.assertEqual(ejecutados[0].id_nacion, 1)
        self.assertEqual(ejecutados[0].origen, 1)
        self.assertEqual(ejecutados[1].id_nacion, 2)
        self.assertEqual(ejecutados[1].origen, 10)
        self.assertEqual(ejecutados[2].id_nacion, 1)
        self.assertEqual(ejecutados[2].origen, 2)
        self.assertEqual(ejecutados[3].id_nacion, 2)
        self.assertEqual(ejecutados[3].origen, 11)

    def test_ordenes_no_cesion_se_ejecutan_antes_del_movimiento(self):
        # Nación 1 tiene: Declarar Guerra (no cede) + Movimiento (cede) + Ataque (cede)
        # Nación 2 tiene: Movimiento (cede)
        ranking = [1, 2]

        ordenes = [
            Evento(turno=1, prioridad_nacion=1, fase=FaseOrden.ORDENADA, id_nacion=1, tipo_evento=TipoEvento.DECLARAR_GUERRA, origen=1, destino=2),
            Evento(turno=1, prioridad_nacion=1, fase=FaseOrden.ORDENADA, id_nacion=1, tipo_evento=TipoEvento.MOVIMIENTO, origen=1, destino=2),
            Evento(turno=1, prioridad_nacion=1, fase=FaseOrden.ORDENADA, id_nacion=1, tipo_evento=TipoEvento.ATAQUE, origen=2, destino=3),
            Evento(turno=1, prioridad_nacion=2, fase=FaseOrden.ORDENADA, id_nacion=2, tipo_evento=TipoEvento.MOVIMIENTO, origen=10, destino=11),
        ]

        ejecutados = ejecutar_round_robin(ranking, ordenes)

        # Secuencia esperada:
        # 1. N1: DECLARAR_GUERRA (no cede)
        # 2. N1: MOVIMIENTO (cede turno)
        # 3. N2: MOVIMIENTO (cede turno)
        # 4. N1: ATAQUE (cede turno)
        self.assertEqual(len(ejecutados), 4)
        self.assertEqual(ejecutados[0].tipo_evento, TipoEvento.DECLARAR_GUERRA)
        self.assertEqual(ejecutados[0].id_nacion, 1)
        self.assertEqual(ejecutados[1].tipo_evento, TipoEvento.MOVIMIENTO)
        self.assertEqual(ejecutados[1].id_nacion, 1)
        self.assertEqual(ejecutados[2].tipo_evento, TipoEvento.MOVIMIENTO)
        self.assertEqual(ejecutados[2].id_nacion, 2)
        self.assertEqual(ejecutados[3].tipo_evento, TipoEvento.ATAQUE)
        self.assertEqual(ejecutados[3].id_nacion, 1)

    def test_callback_ejecutor_recibe_eventos(self):
        ranking = [1]
        ordenes = [
            Evento(turno=1, prioridad_nacion=1, fase=FaseOrden.ORDENADA, id_nacion=1, tipo_evento=TipoEvento.MOVIMIENTO, origen=1, destino=2),
        ]
        llamadas = []
        ejecutar_round_robin(ranking, ordenes, ejecutor_orden=lambda e: llamadas.append(e.tipo_evento))
        self.assertEqual(llamadas, [TipoEvento.MOVIMIENTO])


if __name__ == "__main__":
    unittest.main()
