# Age of Conquest — Simulador (Ingeniería Inversa)

Simulador de eventos discretos (DES) que replica el motor lógico (back-end) del
wargame de estrategia por turnos **Age of Conquest**, desarrollado como trabajo
final de la asignatura **Simulación de Sistemas** — Universidad Nacional
Experimental del Táchira (UNET), Vicerrectorado Académico.

## Integrantes

- Theryan Colmenares — V-31060894
- Ismael Hidalgo — V-31470047
- Henyer Molina — V-31098304

## Alcance del proyecto

Este simulador implementa el "motor lógico" del juego: economía, población,
felicidad, diplomacia, combate y el ciclo de turnos en modo **WEGO**
(We-Go), tal como se especifica en la formalización cuantitativa y el modelo
conceptual desarrollados en las fases previas del proyecto.

**No** se replica la interfaz gráfica, los mapas ni ningún asset visual del
juego comercial original — la interacción es por consola, y el mapa es una
estructura lógica de provincias con adyacencia (sin representación gráfica),
tal como permite el enunciado de la tarea. No se utiliza ningún material con
derechos de autor del juego original; todo el código y los nombres de
variables provienen de la especificación propia elaborada por el equipo.

## Estructura del proyecto

```
age-of-conquest-sim/
├── src/
│   ├── entidades/         # Provincia, Nacion, Gobernante, RelacionDiplomatica
│   ├── parametros.py      # Constantes de configuración del modelo
│   └── mapa.py            # Estructura lógica del mapa y adyacencia
├── tests/                 # Pruebas y casos de validación numérica
└── docs/
    └── decisiones/        # Registro de decisiones de diseño por feature
```

## Requisitos

- Python 3.10 o superior (se usan `dataclasses`, `set[int]` y `from __future__ import annotations`).

## Cómo ejecutar

> El módulo de interfaz de consola (bucle de turnos) se agregará en una fase
> posterior del desarrollo. Por ahora, el proyecto puede importarse y
> ejercitarse directamente en Python, por ejemplo:

```bash
cd age-of-conquest-sim
python3 -c "
from src.mapa import crear_mapa_anillo
mapa = crear_mapa_anillo()
print(f'Mapa generado con {len(mapa)} provincias')
"
```

## Documentación técnica

- Cada feature del proyecto tiene su propio registro de decisiones de diseño
  en `docs/decisiones/`, explicando la lógica seguida y las decisiones
  tomadas al implementarla.
- Las fórmulas y reglas de negocio implementadas provienen de la
  Formalización Cuantitativa y el Modelo Conceptual entregados en las fases
  previas del proyecto (documentos académicos, no incluidos en este
  repositorio).
