# Decisiones de diseño — Interfaz de consola e integración final

- **Autor:** Theryan Colmenares
- **Rama:** feature/interfaz-consola
- **Fecha:** 2026-08-19
- **Referencia en la Formalización/Modelo Conceptual:** "Ciclo Principal WEGO" y "Algoritmo del Despachador de la LEF" de la Formalización Cuantitativa; sección 9.1 ("Bucle principal de simulación") del Modelo Conceptual; `tarea.md` ("permitir interacción básica (consola...) para ejecutar al menos 5 fases (turnos) consecutivas"); `Game Manual.txt`, sección "Actions & Events" (catálogo de órdenes estáticas y ordenadas).

## Objetivo de la feature

Integrar los tres submódulos ya mergeados a `develop` (entidades base,
economía/población de Henyer, combate/diplomacia/motor WEGO de Ismael) en
una partida jugable de punta a punta, y exponer un bucle de consola que
permita ingresar órdenes y ejecutar al menos 5 turnos consecutivos, tal
como exige `tarea.md`.

## Lógica seguida

1. Se detectó que ningún submódulo previo implementaba las **órdenes
   estáticas de reclutamiento, construcción (muralla/torre) ni pillaje
   real** (con oro y cooldown) — solo existían declaradas como
   `TipoEvento` en la FEL de Ismael, sin handler. Como la interfaz de
   consola necesita un handler ejecutable por cada tipo de orden estática
   para no dejar la FEL con eventos "huérfanos", se creó
   `src/acciones_estaticas.py` con `reclutar_tropas`, `construir_muralla`,
   `construir_torre_vigia`, `pillar_provincia` y
   `reducir_cooldowns_pillaje`, siguiendo el mismo patrón de "función pura
   que recibe entidades y retorna un resultado" que ya usaba
   `economia.py`.
2. `src/simulacion.py` es el módulo de cableado central: expone
   `crear_partida_demo()` (arma mapa, naciones, gobernantes y el
   `GestorDiplomacia`) y registra en el `MotorSimulacionWEGO` de Ismael
   un handler por cada `TipoEvento` estático/ordenado, más un único hook
   de fin de turno que ejecuta, en el orden estricto de la Formalización
   Cuantitativa (Pasos 1-7): crecimiento de población, ingresos y
   tesorería, ajuste de felicidad, penalización recurrente de guerra,
   atrición militar, revueltas, desbande por bancarrota, evaluación de
   eliminación por inanición territorial, cooldowns de pillaje y
   expiración de ceasefires.
3. `src/interfaz_consola.py` implementa el bucle de turnos: por cada
   turno, cada nación activa ingresa comandos de texto (`reclutar`,
   `muralla`, `torre`, `pillar`, `mover`, `atacar`, `guerra`, `paz`,
   `alianza`, `cancelar`, `abandonar`, `disband`, `estado`, `ayuda`,
   `fin`) que se traducen en llamadas a
   `MotorSimulacionWEGO.planificar_orden()`; al terminar todas las
   naciones, se llama a `ejecutar_ciclo_turno()` (que ya internamente
   corre las 4 fases WEGO) y se imprime el resultado antes de pasar al
   siguiente turno.

## Decisiones de diseño y por qué

- **No se creó un módulo `combate/` ni `diplomacia/` adicional para las
  órdenes estáticas:** se usó un archivo plano `acciones_estaticas.py`
  en la raíz de `src/`, porque conceptualmente estas órdenes no son ni
  economía pura ni combate/diplomacia — corresponden al submodelo de
  "Actions & Events" no interactivas del Game Manual, y no encajaban con
  claridad en ninguno de los paquetes ya creados por Henyer o Ismael.
  Crear un paquete nuevo solo para 4 funciones habría sido sobre-ingeniería.
- **`TipoEvento.FORTIFICAR` se mapea al mismo handler que
  `CONSTRUIR_MURALLA`:** la Formalización Cuantitativa solo define una
  variable booleana de defensa por provincia (`P_W_i`, "muralla"); no
  hay una variable cuantitativa separada para "fortificar" más allá de
  eso, así que se interpretó como sinónimo del Game Manual para la misma
  acción, en vez de inventar un segundo nivel de fortificación sin
  respaldo en el documento formal.
- **Costo de la torre de vigía (mitad del costo de muralla) es un valor
  simbólico, no está en la tabla de parámetros:** la Formalización solo
  declara la existencia de `P_V_i` como booleano, sin costo asociado. Se
  documenta explícitamente en el docstring de `construir_torre_vigia`
  que es una decisión de diseño razonable del equipo, no un valor
  extraído del PDF, para que quede claro en la defensa oral.
- **`TipoEvento.DIPLOMACIA` se usa para proponer paz/alianza/protectorado,
  auto-aceptadas sin negociación del otro bando:** dado que el simulador
  no modela IA de negociación ni turnos de aceptación/rechazo (fuera del
  alcance de `tarea.md`), se optó por que la propuesta se aplique de
  inmediato vía `GestorDiplomacia`. Esto es una simplificación deliberada
  frente al Game Manual (que sí prevé negociación), documentada aquí
  para el informe técnico.
- **`ejecutar_movimiento_tropas` se reutiliza como handler tanto de
  `TipoEvento.MOVIMIENTO` como de `TipoEvento.ATAQUE`:** la función de
  Ismael ya decide internamente si el destino es territorio propio,
  neutral o enemigo y resuelve combate solo cuando corresponde, así que
  distinguir "mover" de "atacar" en la consola es solo una ayuda de UX
  para el jugador (deja explícito su intención), no cambia la lógica de
  ejecución.
- **`Partida` (dataclass) agrupa `motor`, `gestor_diplomacia`,
  `evaluador_victoria` y el generador de números aleatorios:** se evitó
  usar variables globales o pasar 4-5 parámetros sueltos entre
  `interfaz_consola.py` y `simulacion.py`; agrupar el estado compartido
  en un solo objeto simplifica las firmas de las funciones del bucle de
  consola.
- **El bucle de consola termina el turno de una nación con el comando
  `fin` en vez de un límite fijo de órdenes:** replica el uso de puntos
  de acción (`N_Ap_n`) del juego real de forma simplificada — no se
  valida aquí que el costo en Puntos de Acción de cada orden no exceda
  `N_Ap_n(t)` disponible (esa validación no estaba en el alcance de
  ningún submódulo previo); se deja como limitación conocida.

## Alternativas consideradas

- Se consideró que la interfaz de consola controlara todas las naciones
  automáticamente (IA simple) para una demo no interactiva; se descartó
  porque `tarea.md` pide explícitamente "interacción básica (consola...)"
  y el equipo prefiere mostrar el ingreso de órdenes en vivo durante la
  defensa oral.
- Se consideró separar el cableado de handlers (`simulacion.py`) en
  varios archivos (uno por fase WEGO); se descartó por ser prematuro
  para el tamaño actual del proyecto — un solo módulo con secciones
  claramente comentadas (`--- Fase 1 ---`, `--- Fase 2 ---`, etc.) es
  suficientemente legible y evita imports cruzados innecesarios.

## Casos borde contemplados

- Se probó el ciclo completo de 5 turnos sin ninguna orden ingresada
  (`test_cinco_turnos_sin_ordenes_no_lanza_excepciones`): el motor no
  debe lanzar excepciones aunque ninguna nación actúe.
- Se probó un escenario de guerra + ataque con fuerza abrumadora
  (`test_guerra_y_combate_transfieren_provincia_al_vencedor`): valida que
  la declaración de guerra, el combate Lanchester y la transferencia de
  provincia queden correctamente encadenados a través del motor.
- Se probó la condición de victoria por Supremacía dentro del bucle de
  `ejecutar_n_turnos` (`test_partida_termina_por_supremacia`): confirma
  que `ResultadoTurno.partida_finalizada` detiene la ejecución de turnos
  restantes tal como espera la interfaz de consola.
- En la interfaz de consola, un comando con argumentos faltantes o no
  numéricos (`ValueError` al hacer `int(...)` o al desempaquetar
  `partes`) se captura y se le informa al usuario sin abortar el bucle
  ni perder las órdenes ya encoladas.
- Se corrió manualmente la interfaz completa vía `stdin` simulado (todas
  las naciones pasando `fin` salvo la primera, que recluta y mueve
  tropas) para confirmar que el bucle real de `input()` also corre 5+
  turnos sin errores, más allá de las pruebas automatizadas.

## Pendientes / limitaciones conocidas

- No se valida el costo en Puntos de Acción (`N_Ap_n`) de cada orden
  contra el saldo disponible de la nación antes de encolarla — cualquier
  nación puede, en la implementación actual, encolar tantas órdenes como
  quiera en un turno. Quedaría como mejora si el equipo dispone de
  tiempo antes de la defensa.
- Las propuestas diplomáticas (`paz`/`alianza`/`protectorado`) se
  auto-aceptan sin intervención de la otra nación; no hay mecanismo de
  rechazo.
- La interfaz de consola es puramente textual/secuencial (sin guardado
  de partida entre ejecuciones); cada corrida empieza desde
  `crear_partida_demo()`.
- No se implementó la mecánica opcional de Elecciones/Reconocimiento/Gran
  Desafío mencionada como opcional en `CLAUDE.md` §5, por no ser
  requisito obligatorio de la tarea.
