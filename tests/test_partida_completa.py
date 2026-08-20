"""
Prueba de validación del ciclo completo de simulación:
Ejecuta una partida de 5 turnos con 4 naciones, planificando y resolviendo
diversas órdenes estáticas y ordenadas (reclutamiento, fortificación, pillaje,
movimiento, ataque, diplomacia, bancarrota, impuestos altos).
"""

import unittest
from src.simulacion import crear_partida_demo
from src.motor.fel import FaseOrden, TipoEvento
from src.entidades.nacion import TasaImpuestos

class TestPartidaCompleta(unittest.TestCase):
    def test_simulacion_completa_5_turnos(self):
        """Ejecuta una partida de 5 turnos con 4 naciones y verifica la consistencia del estado."""
        naciones = ["Rojo", "Azul", "Verde", "Amarillo"]
        # Mapa de 12 provincias.
        # Las naciones iniciales se colocan en:
        # Rojo: provincia 0 (tropas = 100, rey presente)
        # Azul: provincia 3 (tropas = 100, rey presente)
        # Verde: provincia 6 (tropas = 100, rey presente)
        # Amarillo: provincia 9 (tropas = 100, rey presente)
        partida = crear_partida_demo(naciones, num_provincias=12)
        motor = partida.motor
        
        # Verificar estado inicial
        self.assertEqual(len(motor.naciones), 4)
        self.assertEqual(motor.turno_actual, 1)
        self.assertEqual(motor.mapa[0].propietario, 1)
        self.assertEqual(motor.mapa[3].propietario, 2)
        
        # --- Turno 1 ---
        # Rojo (id 1) recluta 200 en provincia 0. Costo: 20 oro.
        # Azul (id 2) fortifica provincia 3 (muralla). Costo: 50 oro.
        # Rojo declara la guerra a Azul (penalización moral de guerra).
        motor.planificar_orden(FaseOrden.ESTATICA, 1, TipoEvento.RECLUTAR, origen=0, datos={"cantidad": 200})
        motor.planificar_orden(FaseOrden.ESTATICA, 2, TipoEvento.CONSTRUIR_MURALLA, origen=3)
        motor.planificar_orden(FaseOrden.ORDENADA, 1, TipoEvento.DECLARAR_GUERRA, origen=0, datos={"objetivo": 2})
        
        print("\n--- Ejecutando Turno 1 ---")
        res1 = motor.ejecutar_ciclo_turno()
        self.assertFalse(res1.partida_finalizada)
        self.assertEqual(motor.turno_actual, 2)
        
        # Verificar reclutamiento Rojo
        self.assertEqual(motor.mapa[0].tropas, 300)
        self.assertEqual(motor.naciones[1].tesoreria, 65) # 100 - 20 (reclutar) + 0 (ingreso, hap < 50 due to war) - 15 (upkeep)
        
        # Verificar muralla Azul
        self.assertTrue(motor.mapa[3].muralla)
        self.assertEqual(motor.naciones[2].tesoreria, 54) # 100 - 50 (muralla) + 9 (net income) - 5 (upkeep)
        
        # --- Turno 2 ---
        # Rojo (id 1) mueve tropas de 0 a 1 (ocupación neutral).
        # Azul (id 2) recluta en 3.
        # Verde (id 3) propone alianza a Amarillo (id 4).
        motor.planificar_orden(FaseOrden.ORDENADA, 1, TipoEvento.MOVIMIENTO, origen=0, destino=1, datos={"cantidad_tropas": 150})
        motor.planificar_orden(FaseOrden.ESTATICA, 2, TipoEvento.RECLUTAR, origen=3, datos={"cantidad": 100})
        motor.planificar_orden(FaseOrden.ESTATICA, 3, TipoEvento.DIPLOMACIA, origen=0, datos={"objetivo": 4, "tipo_propuesta": "alianza"})
        
        print("\n--- Ejecutando Turno 2 ---")
        res2 = motor.ejecutar_ciclo_turno()
        self.assertFalse(res2.partida_finalizada)
        
        # Verificar que Rojo conquistó provincia 1
        self.assertEqual(motor.mapa[1].propietario, 1)
        self.assertEqual(motor.mapa[1].tropas, 150)
        self.assertEqual(motor.mapa[0].tropas, 150)
        self.assertEqual(motor.naciones[1].tesoreria, 59) # 65 + 8 (net income) - 14 (upkeep)
        self.assertEqual(motor.naciones[2].tesoreria, 34) # 54 - 10 (recruit) + 0 (no taxes, hap < 50) - 10 (upkeep)
        
        # --- Turno 3 ---
        # Amarillo (id 4) pilla su provincia 9. Recibe oro, moral de provincia baja.
        # Verde (id 3) distribuye dinero a nivel nacional (monto 30).
        motor.planificar_orden(FaseOrden.ESTATICA, 4, TipoEvento.PILLAJE, origen=9)
        motor.planificar_orden(FaseOrden.ESTATICA, 3, TipoEvento.DISTRIBUIR_DINERO, origen=0, datos={"monto_por_provincia": 30})
        
        print("\n--- Ejecutando Turno 3 ---")
        res3 = motor.ejecutar_ciclo_turno()
        self.assertFalse(res3.partida_finalizada)
        
        # Verificar pillaje Amarillo: cooldown activo, felicidad baja
        self.assertTrue(motor.mapa[9].esta_pillada())
        self.assertEqual(motor.mapa[9].cooldown_pillaje, 11) # 12 - 1 (fin de turno decrementa)
        self.assertEqual(motor.naciones[4].tesoreria, 269) # 108 + 166 (pillage) - 5 (upkeep)
        
        # --- Turno 4 ---
        # Rojo (id 1) establece impuestos HIGH para ver caída de felicidad
        motor.naciones[1].tasa_impuestos = TasaImpuestos.HIGH
        
        # Amarillo (id 4) gasta todo su oro para forzar bancarrota en mantenimiento
        # Y le damos una fuerza desmedida de tropas en provincia 9 para causar un gran upkeep
        motor.naciones[4].tesoreria = 0
        motor.mapa[9].tropas = 1000
        
        print("\n--- Ejecutando Turno 4 ---")
        res4 = motor.ejecutar_ciclo_turno()
        self.assertFalse(res4.partida_finalizada)
        
        # La felicidad en provincia 0 de Rojo debe disminuir por impuestos HIGH (debería bajar de 50)
        self.assertEqual(motor.mapa[0].felicidad, 34)
        
        # Amarillo debe sufrir desbande por bancarrota en provincia 9
        # Upkeep = max(1, 1000 * 5 // 100) = 50.
        # Ingresos: provincia 9 está pillada y tiene felicidad < 50, por lo que ingresos netos = 0.
        # Exceso = 50 - 0 = 50.
        # Soldados a desbandar = ceil(50 * 100 / 5) = 1000 soldados.
        # Por lo tanto, todas las 1000 tropas de Amarillo se desbandan y quedan en 0.
        self.assertEqual(motor.mapa[9].tropas, 0)
        
        # --- Turno 5 ---
        # Rojo (id 1) ataca a Azul (id 2) en provincia 3
        # Asignamos manualmente provincia 2 a Rojo con tropas suficientes para un ataque
        motor.mapa[2].propietario = 1
        motor.naciones[1].provincias.add(2)
        motor.mapa[2].tropas = 500
        
        # Rojo ataca provincia 3 (Azul) desde provincia 2 con 450 soldados
        # Las tropas defensoras de Azul en la provincia 3 son 200
        # Azul tiene muralla (+100% def) y gobernante (+30% def), total defensivo: 100 + 100 + 30 = 230%
        # Fuerza atacante: 450 * (100) = 45000 (Rojo no tiene gobernante en prov 2)
        # Fuerza defensora: 200 * 230 = 46000
        # Gana el defensor Azul porque FC_A (45000) <= FC_D (46000)
        motor.planificar_orden(FaseOrden.ORDENADA, 1, TipoEvento.ATAQUE, origen=2, destino=3, datos={"cantidad_tropas": 450})
        
        print("\n--- Ejecutando Turno 5 ---")
        res5 = motor.ejecutar_ciclo_turno()
        
        # El defensor Azul debe seguir siendo dueño de provincia 3
        self.assertEqual(motor.mapa[3].propietario, 2)
        # Las tropas de Rojo atacantes murieron (origen quedó con 50)
        self.assertEqual(motor.mapa[2].tropas, 50)
        # Las tropas de Azul sufrieron bajas pero ganaron
        # FC_A/FC_D = 45000/46000 = 0.97826
        # P_M_final = max(1, floor(200 * (1 - 0.97826))) = max(1, floor(4.34)) = 4 soldados defensores
        self.assertEqual(motor.mapa[3].tropas, 4)
        
        print("Test de partida de 5 turnos con 4 naciones completado con éxito.")

if __name__ == "__main__":
    unittest.main()
