"""
Prueba de integración de partida completa (5 turnos):
Replica exactamente la partida interactiva jugada en consola con 3 naciones
y 9 provincias, verificando:
- Turno 1: Despliegues pacíficos, declaración de guerra Azul->Rojo, propuestas diplomáticas de Verde.
- Turno 2: Construcción de muralla en Prov 1, ataque fallido de Azul a Prov 1 (defensa con muralla), rechazo de paz.
- Turno 3: Aceptación de alianza Rojo-Verde, reclutamiento, expansión de Rojo a Prov 8 y Verde a Prov 5.
- Turno 4: Ataque victorioso de Rojo a Prov 2 (conquista), declaración de guerra Azul->Verde.
- Turno 5: Ataque de Rojo a la capital de Azul (Prov 3 con gobernante), Jaque Mate, eliminación de Azul y victoria por Supremacía.
"""

import unittest

from src.entidades.relacion_diplomatica import TipoRelacion
from src.motor.fel import FaseOrden, TipoEvento
from src.simulacion import (
    aceptar_tratado,
    crear_partida_demo,
    proponer_tratado,
    rechazar_tratado,
)


class TestPartidaCompleta5Turnos(unittest.TestCase):

    def test_partida_completa_5_turnos_con_jaque_mate_y_supremacia(self):
        # 1. Configuración inicial
        partida = crear_partida_demo(["Rojo", "Azul", "Verde"], num_provincias=9)
        motor = partida.motor
        gestor_dip = partida.gestor_diplomacia

        # Verificación estado inicial
        self.assertEqual(motor.mapa[0].propietario, 1)
        self.assertEqual(motor.mapa[3].propietario, 2)
        self.assertEqual(motor.mapa[6].propietario, 3)

        # =========================================================================
        # TURNO 1
        # =========================================================================
        # Rojo: mover 0 -> 1 (50 tropas)
        motor.planificar_orden(FaseOrden.ORDENADA, 1, TipoEvento.MOVIMIENTO, origen=0, destino=1, datos={"cantidad_tropas": 50})

        # Azul: guerra a 1, mover 3 -> 2 (80 tropas)
        motor.planificar_orden(FaseOrden.ORDENADA, 2, TipoEvento.DECLARAR_GUERRA, origen=0, datos={"objetivo": 1})
        motor.planificar_orden(FaseOrden.ORDENADA, 2, TipoEvento.MOVIMIENTO, origen=3, destino=2, datos={"cantidad_tropas": 80})

        # Verde: paz a 2, alianza a 1
        motor.planificar_orden(FaseOrden.ESTATICA, 3, TipoEvento.DIPLOMACIA, origen=0, datos={"objetivo": 2, "tipo_propuesta": "paz"})
        motor.planificar_orden(FaseOrden.ESTATICA, 3, TipoEvento.DIPLOMACIA, origen=0, datos={"objetivo": 1, "tipo_propuesta": "alianza"})

        res_t1 = motor.ejecutar_ciclo_turno()
        self.assertFalse(res_t1.partida_finalizada)

        # Verificaciones Turno 1
        self.assertIn(1, motor.naciones[1].provincias)
        self.assertIn(2, motor.naciones[2].provincias)
        self.assertTrue(gestor_dip.estan_en_guerra(1, 2))
        self.assertIn(("paz", 3), partida.propuestas_pendientes.get(2, []))
        self.assertIn(("alianza", 3), partida.propuestas_pendientes.get(1, []))
        self.assertEqual(motor.naciones[1].tesoreria, 111)
        self.assertEqual(motor.naciones[2].tesoreria, 103)
        self.assertEqual(motor.naciones[3].tesoreria, 104)

        # =========================================================================
        # TURNO 2
        # =========================================================================
        # Rojo: muralla en Prov 1
        motor.planificar_orden(FaseOrden.ESTATICA, 1, TipoEvento.CONSTRUIR_MURALLA, origen=1)

        # Azul: atacar 2 -> 1 (50 tropas), rechazar paz 3
        rechazar_tratado(partida, id_receptor=2, id_origen=3, tipo="paz")
        motor.planificar_orden(FaseOrden.ORDENADA, 2, TipoEvento.ATAQUE, origen=2, destino=1, datos={"cantidad_tropas": 50})

        res_t2 = motor.ejecutar_ciclo_turno()
        self.assertFalse(res_t2.partida_finalizada)

        # Verificaciones Turno 2
        self.assertTrue(motor.mapa[1].muralla)
        # Rojo defendió con éxito con muralla (50 vs 50 + muralla -> 25 sobrevivientes)
        self.assertEqual(motor.mapa[1].propietario, 1)
        self.assertEqual(motor.mapa[1].tropas, 25)
        self.assertEqual(len(partida.propuestas_pendientes.get(2, [])), 0)
        self.assertEqual(motor.naciones[1].tesoreria, 58)
        self.assertEqual(motor.naciones[2].tesoreria, 101)
        self.assertEqual(motor.naciones[3].tesoreria, 108)

        # =========================================================================
        # TURNO 3
        # =========================================================================
        # Rojo: aceptar alianza 3, reclutar 50 en Prov 1, mover 0->1 (30), mover 0->8 (20)
        aceptar_tratado(partida, id_receptor=1, id_origen=3, tipo="alianza", turno=3)
        motor.planificar_orden(FaseOrden.ESTATICA, 1, TipoEvento.RECLUTAR, origen=1, datos={"cantidad": 50})
        motor.planificar_orden(FaseOrden.ORDENADA, 1, TipoEvento.MOVIMIENTO, origen=0, destino=1, datos={"cantidad_tropas": 30})
        motor.planificar_orden(FaseOrden.ORDENADA, 1, TipoEvento.MOVIMIENTO, origen=0, destino=8, datos={"cantidad_tropas": 20})

        # Azul: mover 3 -> 2 (20 tropas)
        motor.planificar_orden(FaseOrden.ORDENADA, 2, TipoEvento.MOVIMIENTO, origen=3, destino=2, datos={"cantidad_tropas": 20})

        # Verde: mover 6 -> 5 (80 tropas)
        motor.planificar_orden(FaseOrden.ORDENADA, 3, TipoEvento.MOVIMIENTO, origen=6, destino=5, datos={"cantidad_tropas": 80})

        res_t3 = motor.ejecutar_ciclo_turno()
        self.assertFalse(res_t3.partida_finalizada)

        # Verificaciones Turno 3
        self.assertEqual(gestor_dip.obtener_relacion(1, 3).tipo, TipoRelacion.ALIANZA)
        self.assertIn(8, motor.naciones[1].provincias)
        self.assertIn(5, motor.naciones[3].provincias)
        self.assertEqual(motor.mapa[1].tropas, 105)  # 25 + 50 reclutados + 30 movidos
        self.assertEqual(motor.mapa[2].tropas, 50)   # 30 restantes + 20 movidos
        self.assertEqual(motor.naciones[1].tesoreria, 54)
        self.assertEqual(motor.naciones[2].tesoreria, 99)
        self.assertEqual(motor.naciones[3].tesoreria, 118)

        # =========================================================================
        # TURNO 4
        # =========================================================================
        # Rojo: atacar 1 -> 2 (105 tropas)
        motor.planificar_orden(FaseOrden.ORDENADA, 1, TipoEvento.ATAQUE, origen=1, destino=2, datos={"cantidad_tropas": 105})

        # Azul: reclutar 10 en Prov 3, guerra a Verde (3)
        motor.planificar_orden(FaseOrden.ESTATICA, 2, TipoEvento.RECLUTAR, origen=3, datos={"cantidad": 10})
        motor.planificar_orden(FaseOrden.ORDENADA, 2, TipoEvento.DECLARAR_GUERRA, origen=0, datos={"objetivo": 3})

        res_t4 = motor.ejecutar_ciclo_turno()
        self.assertFalse(res_t4.partida_finalizada)

        # Verificaciones Turno 4
        # Rojo conquista Prov 2 (105 vs 50 -> 55 sobrevivientes)
        self.assertEqual(motor.mapa[2].propietario, 1)
        self.assertEqual(motor.mapa[2].tropas, 55)
        self.assertIn(2, motor.naciones[1].provincias)
        self.assertNotIn(2, motor.naciones[2].provincias)
        self.assertTrue(gestor_dip.estan_en_guerra(2, 3))
        self.assertEqual(motor.naciones[1].tesoreria, 51)
        self.assertEqual(motor.naciones[2].tesoreria, 97)
        self.assertEqual(motor.naciones[3].tesoreria, 128)

        # =========================================================================
        # TURNO 5
        # =========================================================================
        # Rojo: atacar 2 -> 3 (55 tropas)
        motor.planificar_orden(FaseOrden.ORDENADA, 1, TipoEvento.ATAQUE, origen=2, destino=3, datos={"cantidad_tropas": 55})

        # Azul: muralla en Prov 3 (50 oro)
        motor.planificar_orden(FaseOrden.ESTATICA, 2, TipoEvento.CONSTRUIR_MURALLA, origen=3)

        res_t5 = motor.ejecutar_ciclo_turno()

        # Verificaciones Turno 5: Fin de Partida
        self.assertTrue(res_t5.partida_finalizada)
        self.assertEqual(res_t5.ganador, 1)
        self.assertEqual(motor.mapa[3].propietario, 1)

        # Muerte del gobernante de Azul en Prov 3 -> Jaque Mate
        self.assertFalse(motor.naciones[2].activa)
        self.assertFalse(motor.gobernantes[2].vivo)

        # Victoria por Supremacía: Rojo controla Provs 0, 1, 2, 3, 8 (5 de 9 provincias > 50%)
        self.assertEqual(len(motor.naciones[1].provincias), 5)


if __name__ == "__main__":
    unittest.main()
