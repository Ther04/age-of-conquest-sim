"""
Pruebas unitarias para la Lista de Eventos Futuros (FEL).
Usa unittest de la biblioteca estándar de Python (sin dependencias externas).
"""

import unittest
from src.motor.fel import Evento, FaseOrden, TipoEvento, ListaEventosFuturos


class TestListaEventosFuturos(unittest.TestCase):

    def test_ordenamiento_fel_por_fase_y_prioridad(self):
        fel = ListaEventosFuturos()

        # Encolar en desorden
        e_ordenada_b = Evento(
            turno=1,
            prioridad_nacion=2,  # Nación más fuerte (actúa después)
            fase=FaseOrden.ORDENADA,
            id_nacion=2,
            tipo_evento=TipoEvento.MOVIMIENTO,
            origen=5,
            destino=6,
        )
        e_estatica = Evento(
            turno=1,
            prioridad_nacion=3,
            fase=FaseOrden.ESTATICA,
            id_nacion=1,
            tipo_evento=TipoEvento.RECLUTAR,
            origen=1,
        )
        e_ordenada_a = Evento(
            turno=1,
            prioridad_nacion=1,  # Nación más débil (actúa primero)
            fase=FaseOrden.ORDENADA,
            id_nacion=1,
            tipo_evento=TipoEvento.ATAQUE,
            origen=1,
            destino=2,
        )

        fel.encolar(e_ordenada_b)
        fel.encolar(e_estatica)
        fel.encolar(e_ordenada_a)

        # 1. Primero debe salir la orden estática (prioridad_fase = 1)
        primero = fel.obtener_siguiente()
        self.assertIsNotNone(primero)
        self.assertEqual(primero.fase, FaseOrden.ESTATICA)
        self.assertEqual(primero.tipo_evento, TipoEvento.RECLUTAR)

        # 2. Luego la ordenada de la nación 1 (más débil, prioridad 1)
        segundo = fel.obtener_siguiente()
        self.assertIsNotNone(segundo)
        self.assertEqual(segundo.fase, FaseOrden.ORDENADA)
        self.assertEqual(segundo.prioridad_nacion, 1)
        self.assertEqual(segundo.tipo_evento, TipoEvento.ATAQUE)

        # 3. Finalmente la ordenada de la nación 2 (prioridad 2)
        tercero = fel.obtener_siguiente()
        self.assertIsNotNone(tercero)
        self.assertEqual(tercero.fase, FaseOrden.ORDENADA)
        self.assertEqual(tercero.prioridad_nacion, 2)
        self.assertEqual(tercero.tipo_evento, TipoEvento.MOVIMIENTO)

        self.assertTrue(fel.esta_vacia())

    def test_filtrado_por_fase(self):
        fel = ListaEventosFuturos()

        fel.encolar_orden(
            turno=1,
            fase=FaseOrden.ESTATICA,
            id_nacion=1,
            tipo_evento=TipoEvento.RECLUTAR,
            origen=1,
        )
        fel.encolar_orden(
            turno=1,
            fase=FaseOrden.ORDENADA,
            id_nacion=1,
            tipo_evento=TipoEvento.MOVIMIENTO,
            origen=1,
            destino=2,
        )
        fel.encolar_orden(
            turno=2,
            fase=FaseOrden.ESTATICA,
            id_nacion=2,
            tipo_evento=TipoEvento.FORTIFICAR,
            origen=3,
        )

        # Filtrar estáticas del turno 1
        estaticas_t1 = fel.filtrar_ordenes_estaticas(turno=1)
        self.assertEqual(len(estaticas_t1), 1)
        self.assertEqual(estaticas_t1[0].tipo_evento, TipoEvento.RECLUTAR)

        # Quedan 2 eventos en la FEL
        self.assertEqual(fel.total_eventos(), 2)

        # Filtrar ordenadas del turno 1
        ordenadas_t1 = fel.filtrar_ordenes_ordenadas(turno=1)
        self.assertEqual(len(ordenadas_t1), 1)
        self.assertEqual(ordenadas_t1[0].tipo_evento, TipoEvento.MOVIMIENTO)

        # Solo queda el evento del turno 2
        self.assertEqual(fel.total_eventos(), 1)
        siguiente = fel.obtener_siguiente()
        self.assertIsNotNone(siguiente)
        self.assertEqual(siguiente.turno, 2)


if __name__ == "__main__":
    unittest.main()
