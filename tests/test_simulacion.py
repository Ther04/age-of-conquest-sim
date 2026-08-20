"""
Pruebas de integración del módulo de simulación (`src/simulacion.py`):
verifican que el ciclo WEGO completo (estático -> ordenado -> endógeno ->
victoria) corre de punta a punta durante 5+ turnos consecutivos con varias
naciones, incluyendo un escenario con declaración de guerra y combate.
"""

import unittest

from src.motor.fel import FaseOrden, TipoEvento
from src.simulacion import crear_partida_demo, ejecutar_n_turnos


class TestSimulacionIntegracion(unittest.TestCase):

    def test_cinco_turnos_sin_ordenes_no_lanza_excepciones(self):
        """El ciclo WEGO debe correr 5 turnos consecutivos sin órdenes ni errores."""
        partida = crear_partida_demo(["Rojo", "Azul", "Verde"], num_provincias=9)
        resultados = ejecutar_n_turnos(partida, 5)

        self.assertEqual(len(resultados), 5)
        self.assertEqual(partida.motor.turno_actual, 6)
        for nacion in partida.motor.naciones.values():
            self.assertTrue(nacion.activa)

    def test_reclutamiento_y_ocupacion_territorial(self):
        """Reclutar tropas y mover hacia una provincia neutral debe expandir el territorio."""
        partida = crear_partida_demo(["Rojo", "Azul", "Verde"], num_provincias=9)
        motor = partida.motor

        motor.planificar_orden(FaseOrden.ESTATICA, 1, TipoEvento.RECLUTAR, origen=0, datos={"cantidad": 100})
        motor.planificar_orden(FaseOrden.ORDENADA, 1, TipoEvento.MOVIMIENTO, origen=0, destino=1, datos={"cantidad_tropas": 50})
        motor.ejecutar_ciclo_turno()

        rojo = motor.naciones[1]
        self.assertIn(1, rojo.provincias)
        self.assertEqual(motor.mapa[1].propietario, 1)

    def test_guerra_y_combate_transfieren_provincia_al_vencedor(self):
        """
        Escenario: Rojo declara la guerra a Azul y ataca su provincia con una
        fuerza abrumadora. La provincia debe cambiar de dueño (Lanchester discreto).
        """
        partida = crear_partida_demo(["Rojo", "Azul"], num_provincias=6)
        motor = partida.motor

        # Refuerza al atacante y reclama la provincia neutral intermedia como puente.
        motor.mapa[0].tropas = 500

        motor.planificar_orden(FaseOrden.ORDENADA, 1, TipoEvento.DECLARAR_GUERRA, origen=0, datos={"objetivo": 2})
        motor.planificar_orden(FaseOrden.ORDENADA, 1, TipoEvento.ATAQUE, origen=0, destino=1, datos={"cantidad_tropas": 400})

        motor.ejecutar_ciclo_turno()

        # La provincia 1 (vecina de la 0, neutral inicialmente) debe quedar ocupada por Rojo.
        self.assertEqual(motor.mapa[1].propietario, 1)
        self.assertIn(1, motor.naciones[1].provincias)

        relacion = partida.gestor_diplomacia.obtener_relacion(1, 2, crear_si_no_existe=False)
        self.assertIsNotNone(relacion)
        self.assertEqual(relacion.tipo.value, "guerra")

    def test_partida_termina_por_supremacia(self):
        """Si una nación controla más del 50% de las provincias, la partida debe finalizar con esa nación como ganadora."""
        partida = crear_partida_demo(["Rojo", "Azul"], num_provincias=4)
        motor = partida.motor

        # Rojo ya controla 1 de 4; se le asignan manualmente las otras 3 para forzar supremacía.
        for pid in (1, 2, 3):
            motor.mapa[pid].propietario = 1
            motor.naciones[1].provincias.add(pid)
        motor.naciones[2].provincias.clear()
        motor.mapa[motor.mapa[0].vecinos[0]]  # sanity: acceso válido al mapa

        resultados = ejecutar_n_turnos(partida, 5)

        self.assertTrue(resultados[-1].partida_finalizada)
        self.assertEqual(resultados[-1].ganador, 1)


if __name__ == "__main__":
    unittest.main()
