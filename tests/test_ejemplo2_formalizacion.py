"""
Prueba de Validación y Calibración Numérica — Ejemplo 2 de la Formalización Cuantitativa.

Ver:
- Formalización Cuantitativa y Lógica del Sistema - AgeofConquest,
  sección "Ejemplo 2: Simulación de Combate en Aritmética Entera", páginas 12-13.
- CLAUDE.md, sección 4: "Ejemplos numéricos ya resueltos en el PDF".

Condiciones iniciales exactas del documento:
- Atacante: 17 soldados con el rey (Bon_ruler_atk = 1.00) en ataque naval (Pen_naval_atk = 0.30, IsNaval = 1).
- Defensor: 17 soldados tras murallas (Bon_wall_def = 1.00) y con rey defensor (Bon_ruler_def = 0.30).

Resultados esperados según la Formalización:
- FC_A = 2,890
- FC_D = 3,910
- Ganador: Defensor (FC_A <= FC_D)
- Tropas atacantes finales = 0
- Tropas defensoras sobrevivientes = 4 soldados (floor(17 * (1 - 2890/3910)) = floor(4.435) = 4)
- Jaque Mate: El rey atacante muere al liderar la invasión fallida, la nación atacante es eliminada
  y transfiere todo su territorio restante a la defensora.
"""

import unittest
from src.combate.lanchester import (
    calcular_fuerza_atacante,
    calcular_fuerza_defensora,
    resolver_combate,
)
from src.entidades.gobernante import Gobernante
from src.entidades.nacion import Nacion
from src.entidades.provincia import Provincia


class TestEjemplo2Formalizacion(unittest.TestCase):

    def test_ejemplo_2_combate_naval_con_reyes_y_muralla(self):
        # 1. Verificar cálculos aislados de Fuerzas de Combate Efectivas
        fc_a = calcular_fuerza_atacante(
            tropas_atk=17,
            gobernante_presente=True,
            es_naval=True,
        )
        # FC_A = 17 * (100 + 100 - 30) = 17 * 170 = 2,890
        self.assertEqual(fc_a, 2890, f"FC_A esperado: 2890, obtenido: {fc_a}")

        fc_d = calcular_fuerza_defensora(
            tropas_def=17,
            tiene_muralla=True,
            gobernante_presente=True,
        )
        # FC_D = 17 * (100 + 100 + 30) = 17 * 230 = 3,910
        self.assertEqual(fc_d, 3910, f"FC_D esperado: 3910, obtenido: {fc_d}")

        # 2. Configurar el escenario completo de la simulación
        # Provincia donde ocurre la batalla (fortificada y con guarnición de 17)
        prov_batalla = Provincia(
            id_provincia=1,
            propietario=2,
            tropas=17,
            muralla=True,
            felicidad=50,
        )
        # Provincia patria del atacante (para verificar transferencia por Jaque Mate)
        prov_atacante = Provincia(
            id_provincia=2,
            propietario=1,
            tropas=50,
            muralla=False,
            felicidad=50,
        )
        mapa = {1: prov_batalla, 2: prov_atacante}

        nacion_atacante = Nacion(
            id_nacion=1,
            nombre="Nación Atacante",
            provincias={2},
            felicidad_promedio=50,
            gobernante_vivo=True,
            activa=True,
        )
        nacion_defensora = Nacion(
            id_nacion=2,
            nombre="Nación Defensora",
            provincias={1},
            felicidad_promedio=50,
            gobernante_vivo=True,
            activa=True,
        )

        rey_atacante = Gobernante(
            id_gobernante=1,
            nacion_propietaria=1,
            provincia_actual=2,
            vivo=True,
        )
        rey_defensor = Gobernante(
            id_gobernante=2,
            nacion_propietaria=2,
            provincia_actual=1,
            vivo=True,
        )

        # 3. Ejecutar la resolución de combate
        resultado = resolver_combate(
            provincia=prov_batalla,
            nacion_atk=nacion_atacante,
            nacion_def=nacion_defensora,
            tropas_atk=17,
            es_naval=True,
            gobernante_atk_presente=True,
            gobernante_def_presente=True,
            gobernante_atk=rey_atacante,
            gobernante_def=rey_defensor,
            mapa=mapa,
        )

        # 4. Verificaciones exactas contra la Formalización Cuantitativa
        # Criterio de victoria: FC_A (2890) <= FC_D (3910) -> Gana el Defensor
        self.assertEqual(resultado.ganador, 2, "El defensor (Nación 2) debe ser el ganador.")
        self.assertEqual(resultado.perdedor, 1, "El atacante (Nación 1) debe ser el perdedor.")
        self.assertEqual(resultado.fc_atacante, 2890)
        self.assertEqual(resultado.fc_defensor, 3910)

        # Sobrevivientes: max(1, floor(17 * (1 - 2890 / 3910))) = 4
        self.assertEqual(
            resultado.tropas_sobrevivientes,
            4,
            f"Bajas esperadas: sobrevivientes = 4, obtenido: {resultado.tropas_sobrevivientes}",
        )
        self.assertEqual(prov_batalla.tropas, 4)
        self.assertEqual(prov_batalla.propietario, 2)
        self.assertFalse(resultado.cambio_propietario)

        # Efecto en felicidad (+1% defensor, -1% atacante)
        self.assertEqual(nacion_defensora.felicidad_promedio, 51)
        self.assertEqual(nacion_atacante.felicidad_promedio, 49)

        # Condición Jaque Mate: El rey atacante murió liderando la invasión
        self.assertTrue(resultado.jaque_mate)
        self.assertFalse(rey_atacante.vivo)
        self.assertFalse(nacion_atacante.gobernante_vivo)
        self.assertFalse(nacion_atacante.activa)

        # Transferencia total de tierras: las provincias de la nación 1 pasan a la nación 2
        self.assertEqual(nacion_atacante.provincias, set())
        self.assertEqual(nacion_defensora.provincias, {1, 2})
        self.assertEqual(prov_atacante.propietario, 2)


if __name__ == "__main__":
    unittest.main()
