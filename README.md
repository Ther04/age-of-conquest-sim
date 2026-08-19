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
│   ├── mapa.py            # Estructura lógica del mapa y adyacencia
│   ├── economia.py        # Submodelo económico, poblacional y de felicidad
│   ├── acciones_estaticas.py  # Reclutamiento, construcción y pillaje
│   ├── combate/           # Resolución de combate (Lanchester) y movimiento
│   ├── diplomacia/        # Relaciones diplomáticas y declaración de guerra
│   ├── motor/              # FEL, ciclo WEGO, ranking, round-robin, victoria
│   ├── simulacion.py       # Integra todos los submódulos en una partida jugable
│   └── interfaz_consola.py # Bucle de turnos interactivo por consola
├── tests/                 # Pruebas y casos de validación numérica
└── docs/
    └── decisiones/        # Registro de decisiones de diseño por feature
```

## Requisitos

- Python 3.10 o superior (se usan `dataclasses`, `set[int]` y `from __future__ import annotations`).

## Cómo ejecutar

Para jugar una partida interactiva por consola (3 naciones, mapa de 9
provincias, 5 turnos por defecto):

```bash
cd age-of-conquest-sim
python3 -m src.interfaz_consola
```

Cada turno, cada nación activa ingresa sus órdenes (reclutar, construir,
pillar, mover/atacar, declarar guerra, proponer paz/alianza, abandonar
provincia, disbandar tropas) hasta escribir `fin`; luego se ejecuta el
ciclo completo de fin de turno (WEGO) y se muestra el resultado. Escribe
`ayuda` en cualquier momento para ver la lista de comandos.

Para correr las pruebas automatizadas del proyecto:

```bash
python3 -m unittest discover -s tests
```

También se puede armar y ejecutar una partida mediante código, sin la
interfaz interactiva, usando `src/simulacion.py` directamente:

```bash
python3 -c "
from src.simulacion import crear_partida_demo, ejecutar_n_turnos
partida = crear_partida_demo(['Rojo', 'Azul', 'Verde'], num_provincias=9)
ejecutar_n_turnos(partida, 5)
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
