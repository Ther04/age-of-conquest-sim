import unittest
from src.entidades.provincia import Provincia
from src.entidades.nacion import Nacion, TipoNacion, TasaImpuestos
from src.entidades.relacion_diplomatica import RelacionDiplomatica, TipoRelacion
from src.economia import (
    crecer_poblacion,
    calcular_ingresos,
    calcular_costo_administracion,
    calcular_mantenimiento_militar,
    actualizar_tesoreria_y_ap,
    actualizar_felicidad,
    desbandar_tropas,
    aplicar_desbande_bancarrota,
    evaluar_eliminacion_inanicion,
)

class TestEconomia(unittest.TestCase):
    def test_ejemplo_1_formalizacion(self):
        """
        Valida el submodelo económico contra el Ejemplo 1 del PDF de Formalización:
        - Turno: 12 (fin de año fiscal, cobro de impuestos).
        - Provincias dominadas: 5 de un total de 20 (proporción = 0.25).
        - Población nacional: 50,000 (distribuida como 10,000 en c/u de las 5 provincias).
        - Comercio base total: 120 (repartido como 24 en c/u de las 5 provincias).
        - Felicidad de todas las provincias: 80% (sin pillaje, de modo que pueden recaudar).
        - Tropas: 3 provincias con 400 soldados c/u, y 2 con 0 soldados.
        - Tesorería inicial: 100 oro.
        
        Resultados esperados:
        - Ingreso Bruto: 620 oro (120 comercio + 500 impuestos).
        - Costo de Administración: 213 oro.
        - Ingreso Neto: 407 oro.
        - Mantenimiento Militar: 60 oro.
        - Tesorería final: 447 oro.
        """
        # 1. Configurar nación
        nacion = Nacion(
            id_nacion=1,
            nombre="Imperio de Prueba",
            tipo=TipoNacion.HUMANO,
            tesoreria=100,
            tasa_impuestos=TasaImpuestos.MEDIUM
        )
        
        # 2. Configurar provincias
        provincias = {}
        for pid in range(5):
            prov = Provincia(
                id_provincia=pid,
                poblacion=10000,
                felicidad=80,
                comercio_base=24,
                propietario=1,
                cooldown_pillaje=0
            )
            # 3 provincias tienen 400 tropas, 2 tienen 0
            if pid < 3:
                prov.tropas = 400
            else:
                prov.tropas = 0
                
            provincias[pid] = prov
            nacion.provincias.add(pid)
            
        # El mapa completo tiene 20 provincias, así que agregamos 15 neutrales vacías
        for pid in range(5, 20):
            provincias[pid] = Provincia(
                id_provincia=pid,
                poblacion=10000,
                felicidad=50,
                comercio_base=10,
                propietario=None
            )

        # 3. Ejecutar los pasos del cálculo para el Turno 12 (Año Fiscal)
        turno = 12
        
        # A. Verificar los cálculos económicos con la población inicial de 50,000 (10,000 por provincia)
        # Esto replica el Ejemplo 1 del PDF exactamente:
        # Comercio base total = 5 * 24 = 120.
        # Impuesto total = 5 * (10000 // 100) = 500.
        # Ingreso bruto = 120 + 500 = 620.
        comercio, impuesto, ingreso_bruto = calcular_ingresos(nacion, provincias, turno)
        self.assertEqual(comercio, 120)
        self.assertEqual(impuesto, 500)
        self.assertEqual(ingreso_bruto, 620)
        
        # B. Costo de Administración con x_n = 0.25
        admin_cost = calcular_costo_administracion(nacion, provincias, ingreso_bruto)
        self.assertEqual(admin_cost, 213)
        
        # C. Mantenimiento Militar
        military_upkeep = calcular_mantenimiento_militar(nacion, provincias)
        self.assertEqual(military_upkeep, 60)
        
        # D. Actualización de Tesorería (Tesorería final = 100 + 407 - 60 = 447)
        net_income = actualizar_tesoreria_y_ap(nacion, provincias, turno, ingreso_bruto, admin_cost, military_upkeep)
        self.assertEqual(net_income, 407)
        self.assertEqual(nacion.tesoreria, 447)

        # E. Probar Crecimiento de población por separado (Paso 1)
        # La población original es 10,000 en cada provincia de la nación.
        # Felicidad = 80%.
        # delta = floor(0.02 * 10000 * (80 - 50) / 100) = floor(0.02 * 10000 * 30 / 100) = 60.
        # Población nueva esperada en cada provincia = 10,060.
        crecer_poblacion(provincias)
        for pid in range(5):
            self.assertEqual(provincias[pid].poblacion, 10060)

    def test_desbande_por_bancarrota(self):
        """
        Verifica la lógica de desbande forzoso cuando la tesorería cae a 0.
        """
        # Nación en bancarrota
        nacion = Nacion(
            id_nacion=1,
            nombre="Bancarrota",
            tesoreria=0,
            tasa_impuestos=TasaImpuestos.MEDIUM
        )
        
        # 3 provincias con felicidad y tropas variadas
        prov0 = Provincia(id_provincia=0, poblacion=5000, felicidad=30, tropas=500, propietario=1)
        prov1 = Provincia(id_provincia=1, poblacion=5000, felicidad=40, tropas=150, propietario=1)
        prov2 = Provincia(id_provincia=2, poblacion=5000, felicidad=50, tropas=200, propietario=1)
        
        mapa = {0: prov0, 1: prov1, 2: prov2}
        nacion.provincias = {0, 1, 2}
        
        # Costo de mantenimiento:
        # prov0: floor(500 * 5 / 100) = 25
        # prov1: floor(150 * 5 / 100) = 7
        # prov2: floor(200 * 5 / 100) = 10
        # total upkeep = 42
        upkeep = calcular_mantenimiento_militar(nacion, mapa)
        self.assertEqual(upkeep, 42)
        
        # Supongamos ingresos netos de 10 oro (insuficientes)
        net_income = 10
        
        # Aplicamos la bancarrota
        # Exceso = 42 - (0 + 10) = 32
        # Soldados a desbandar = ceil(32 * 100 / 5) = 640 soldados
        net_incomes = {1: net_income}
        military_upkeeps = {1: upkeep}
        
        desbandados = aplicar_desbande_bancarrota({1: nacion}, mapa, net_incomes, military_upkeeps)
        
        # Se debieron desbandar 640 soldados
        self.assertEqual(desbandados.get(1), 640)
        
        # Verificamos la rotación priorizando menor felicidad:
        # Provincias ordenadas por felicidad: prov0 (30), prov1 (40), prov2 (50)
        # Total a desbandar: 640.
        # Ronda 1:
        # - prov0 (tropas: 500 -> 400), desbanda 100, restante 540
        # - prov1 (tropas: 150 -> 50), desbanda 100, restante 440
        # - prov2 (tropas: 200 -> 100), desbanda 100, restante 340
        # Ronda 2:
        # - prov0 (tropas: 400 -> 300), desbanda 100, restante 240
        # - prov1 (tropas: 50 -> 0), desbanda 50, restante 190 (prov1 se queda sin tropas y sale de la lista)
        # - prov2 (tropas: 100 -> 0), desbanda 100, restante 90 (prov2 se queda sin tropas y sale de la lista)
        # Ronda 3 (solo queda prov0):
        # - prov0 (tropas: 300 -> 210), desbanda 90, restante 0.
        #
        # Valores finales esperados:
        # prov0: 210 tropas
        # prov1: 0 tropas
        # prov2: 0 tropas
        self.assertEqual(prov0.tropas, 210)
        self.assertEqual(prov1.tropas, 0)
        self.assertEqual(prov2.tropas, 0)

    def test_inanicion_territorial(self):
        """
        Valida que una nación en exilio (sin provincias) pierda felicidad
        gradualmente y sea eliminada al llegar a 0%.
        """
        nacion = Nacion(
            id_nacion=2,
            nombre="Exiliado",
            tesoreria=0,
            felicidad_promedio=80,
            activa=True
        )
        naciones = {2: nacion}
        
        # Turno 1 en exilio: se resetea a 50%
        eliminadas = evaluar_eliminacion_inanicion(naciones)
        self.assertEqual(len(eliminadas), 0)
        self.assertTrue(nacion.en_exilio)
        self.assertEqual(nacion.felicidad_promedio, 50)
        
        # Turno 2 en exilio: decae a 48%
        evaluar_eliminacion_inanicion(naciones)
        self.assertEqual(nacion.felicidad_promedio, 48)
        
        # Llevamos la felicidad a 2% para ver si se elimina al siguiente turno
        nacion.felicidad_promedio = 2
        eliminadas = evaluar_eliminacion_inanicion(naciones)
        self.assertEqual(nacion.felicidad_promedio, 0)
        self.assertEqual(eliminadas, [2])
        self.assertFalse(nacion.activa)

if __name__ == '__main__':
    unittest.main()
