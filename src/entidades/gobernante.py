"""
Entidad Gobernante/Ruler.

Ver: Formalización Cuantitativa y Lógica del Sistema - AgeofConquest,
     variables N_R_n(t) (estado de vida) y N_RL_n(t) (ubicación).
     Modelo Conceptual de Simulación - Age of Conquest, sección 2.4.

Su pérdida implica la eliminación inmediata de la nación ("jaque mate"),
según el submodelo de resolución de combate. Esa lógica de eliminación se
implementa en el módulo de combate, no aquí.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Gobernante:
    id_gobernante: int
    nacion_propietaria: int

    # N_RL_n(t): id de la provincia donde se encuentra el gobernante.
    provincia_actual: Optional[int] = None

    # N_R_n(t): estado de vida del gobernante.
    vivo: bool = True

    def esta_en(self, id_provincia: int) -> bool:
        return self.vivo and self.provincia_actual == id_provincia
