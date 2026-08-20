# Decisiones de diseño — Submodelo de Combate, Diplomacia y Motor de Turnos (WEGO)

- **Autor:** Ismael Hidalgo
- **Rama:** feature/combate-diplomacia-motor
- **Fecha:** 2026-08-19
- **Referencia en la Formalización/Modelo Conceptual:** Formalización Cuantitativa §Fundamentos de Simulación en Modo WEGO, §Submodelo de Resolución de Combate, §Algoritmo del Despachador de la LEF y Reloj de Simulación, §Algoritmo de Resolución de Combate Lanchester, §Función de Penalización por Declaración de Guerra, §Jaque Mate por Pérdida de Gobernante, y §Ejemplo 2; Modelo Conceptual §2.5, §2.6, §2.8, §4.1, §4.3, §4.4, §4.5, §7 (FEL), §9.1, §9.2, §9.3, §9.4, §9.8, §8/§9.9 (Elecciones); Game Manual §Objectives, §How to Play, §Actions & Events, §Troops, §Combat, §Diplomacy.

## Objetivo de la feature

Esta feature implementa el núcleo lógico de ejecución y resolución de eventos del simulador bajo el paradigma WEGO. Abarca la Lista de Eventos Futuros (FEL), el ciclo principal de turnos con avance de reloj discreto, el cálculo del ranking de debilidad de naciones, el algoritmo Round-Robin con cesión de turno por movimiento/ataque, la resolución determinista de combates según la Ley Lineal de Lanchester en aritmética entera, el sistema de diplomacia bilateral con transiciones y periodos de Ceasefire, las penalizaciones morales por declaración de guerra, el movimiento de tropas con bloqueo naval y la evaluación de condiciones de victoria y fin de partida.

## Lógica seguida

La implementación se dividió en módulos especializados dentro de `src/motor/`, `src/combate/` y `src/diplomacia/`:

1. **Lista de Eventos Futuros (FEL) (`src/motor/fel.py`)**:
   Se modeló la clase `Evento` con ordenamiento determinista multidimensional:
   $$(\text{turno}, \text{prioridad\_fase}, \text{prioridad\_nacion}, \text{id\_evento})$$
   donde `prioridad_fase` garantiza que las órdenes estáticas (prioridad 1) se procesen antes que las órdenes ordenadas (prioridad 2). `ListaEventosFuturos` provee métodos para encolar, encolar por lote, y filtrar órdenes estáticas y ordenadas por turno.

2. **Ciclo Principal WEGO (`src/motor/ciclo_wego.py`)**:
   La clase `MotorSimulacionWEGO` implementa la secuencia estricta del turno macro:
   - **Fase 1 (Estática):** Despacho síncrono no interactivo de reclutamiento, fortificación, pillaje, etc.
   - **Fase 2 (Ordenada):** Despacho iterativo interactivo regulado por Round-Robin.
   - **Fase 3 (Endógena):** Ejecución de hooks de fin de turno (economía, crecimiento, felicidad, atrición, revueltas).
   - **Fase 4 (Victoria y Reloj):** Verificación de fin de partida y avance del reloj de simulación ($t = t + 1$).

3. **Cálculo de Ranking de Debilidad (`src/motor/ranking.py`)**:
   Traduce la regla del Game Manual donde la nación más débil actúa primero en el Round-Robin. Se evalúa el vector de fuerza:
   $$(\text{count}(N\_provinces_n), \text{tropas\_totales}_n, N\_T_n, id\_nacion)$$
   donde valores menores indican mayor debilidad.

4. **Algoritmo Round-Robin (`src/motor/round_robin.py`)**:
   Agrupa las órdenes ordenadas por nación en colas FIFO independientes. En cada ronda, itera sobre las naciones en el orden del ranking de debilidad. Cada nación ejecuta órdenes consecutivas hasta topar con un evento de `MOVIMIENTO` o `ATAQUE` (`es_evento_de_cesion`), momento en el cual cede inmediatamente el turno a la siguiente nación del ranking. Órdenes como `DECLARAR_GUERRA`, `CANCELAR_RELACION` o `DISBAND` se ejecutan en ráfaga sin ceder el turno.

5. **Resolución de Combate Lanchester Discreto (`src/combate/lanchester.py`)**:
   Traduce las ecuaciones formales en porcentaje entero:
   $$FC_A = M_{\text{atk}} \cdot (100 + 100 \cdot Bon\_ruler\_atk \cdot I(\text{rey}_{\text{atk}}) - 100 \cdot Pen\_naval\_atk \cdot IsNaval)$$
   $$FC_D = P\_M_i \cdot (100 + 100 \cdot Bon\_wall\_def \cdot P\_W_i + 100 \cdot Bon\_ruler\_def \cdot I(\text{rey}_{\text{def}}))$$
   - Si $FC_A > FC_D$: Gana atacante; supervivientes $=\max(1, \lfloor M_{\text{atk}} \cdot (1 - FC_D / FC_A)\rfloor)$; la provincia pasa al atacante; felicidad $+1\%$/$-1\%$. Si el rey defensor estaba presente $\rightarrow$ **Jaque Mate**: la nación defensora es eliminada y transfiere todas sus tierras al atacante.
   - Si $FC_A \le FC_D$: Gana defensor; supervivientes $=\max(1, \lfloor P\_M_i \cdot (1 - FC_A / FC_D)\rfloor)$; atacante pierde todas sus tropas invasoras; felicidad $+1\%$/$-1\%$. Si el rey atacante lideraba la invasión $\rightarrow$ **Jaque Mate**: la nación atacante es eliminada y transfiere sus tierras al defensor.

6. **Declaración de Guerra y Penalizaciones (`src/diplomacia/declaracion_guerra.py`)**:
   Implementa la penalización instantánea a la nación agresora:
   $$N\_F\_war\_pen = Pen\_war\_decl (-4) + (Pen\_war\_active (-8) \cdot N\_W\_active_{\text{rival}}) + Pen\_war\_multi (-10 \text{ si multiguerra})$$
   Se descuenta inmediatamente de la felicidad de sus provincias y de su promedio. Asimismo, provee el cálculo de penalización recurrente $\max(-3, -1 \cdot N\_W\_active)$.

7. **Gestor de Diplomacia y Ceasefire (`src/diplomacia/gestor_diplomacia.py`)**:
   Administra la matriz de relaciones bilaterales indexada por pares ordenados $(min(a, b), max(a, b))$. Al cancelar una relación (`cancelar_relacion`), activa un Ceasefire obligatorio (1 turno para Paz, 2 turnos para Alianza/Protectorado). Durante el Ceasefire no se puede declarar la guerra. Al final de cada turno, el contador de Ceasefire decrece y, al llegar a 0, transiciona automáticamente a `NEUTRAL`.

8. **Movimiento de Tropas y Bloqueo Naval (`src/combate/movimiento.py`)**:
   Valida la adyacencia de grafo con `mapa.py`. En modo Estándar restringe el ingreso a territorio ajeno salvo que exista estado de `GUERRA`. Si una flota naval intercepta una posición enemiga, se resuelve el combate y el avance se detiene en la provincia de la batalla.

9. **Verificación de Condiciones de Victoria (`src/motor/victoria.py`)**:
   Implementa la regla universal de 100 Puntos de Victoria ($N\_Vp \ge 100$), los modos de juego específicos (Supremacía $>50\%$, Dominación $100\%$, Aniquilación, Captura de Bandera, Defensa) y el cierre por límite de turnos (`EMPATE_DERROTA`).

## Decisiones de diseño y por qué

- **Aritmética entera exacta mediante operadores de división entera**: En combate, la fracción $\lfloor M \cdot (1 - FC_{\text{menor}} / FC_{\text{mayor}})\rfloor$ se calculó como `(M * (FC_mayor - FC_menor)) // FC_mayor`, evitando completamente el uso de variables de punto flotante y posibles desajustes por precisión en distintas plataformas.
- **Desacoplamiento del Motor WEGO mediante Handlers**: El despachador `MotorSimulacionWEGO` no depende rígidamente de las funciones de combate ni de economía; expone registros de handlers (`registrar_handler_estatico`, `registrar_handler_ordenado`, `registrar_hook_fin_turno`), lo que permite que los módulos de Henyer (economía) e Ismael (combate) se integren limpiamente sin referencias circulares.
- **Tupla canónica para relaciones bilaterales**: Las relaciones diplomáticas se indexan mediante `(min(id_a, id_b), max(id_a, id_b))`, asegurando simetría matemática y garantizando que una consulta entre la nación $A$ y $B$ apunte exactamente al mismo registro que entre $B$ y $A$.
- **Alternancia estricta en Round-Robin**: Se implementó una cola independiente por nación en lugar de una lista global, permitiendo procesar ráfagas de órdenes preliminares (declaraciones de guerra, cancelaciones) y cediendo el turno únicamente tras eventos espaciales de movimiento/ataque.
- **Validación matemática aislada del Ejemplo 2**: Se creó un archivo de prueba específico (`tests/test_ejemplo2_formalizacion.py`) que comprueba los valores numéricos exactos de $FC_A = 2890$, $FC_D = 3910$ y 4 supervivientes, garantizando que el simulador esté 100% calibrado con la teoría.

## Alternativas consideradas

- **Uso de colas de prioridad (`heapq`) para la FEL**: Se evaluó usar `heapq` nativo de Python, pero se descartó en favor de una lista ordenada con `dataclass(order=True)` debido a que el tamaño de eventos por turno es discreto y se requiere realizar filtrados por fase (`filtrar_ordenes_estaticas`, `filtrar_ordenes_ordenadas`) que son más claros y estables con listas.
- **Procesamiento de combate continuo sin detención naval**: Se evaluó permitir que los barcos continúen su movimiento tras ganar una batalla naval, pero se descartó porque el manual establece explícitamente la regla de "bloqueo naval" donde la flota victoriosa debe detenerse en el lugar de la batalla.

## Casos borde contemplados

- **Ataque a provincia indefensa (0 tropas)**: Si una provincia no tiene tropas defensoras ($FC_D = 0$), el atacante ocupa la provincia conservando todas sus tropas ($sobrevivientes = tropas\_atk$).
- **Empate en combate ($FC_A == FC_D$)**: La regla formal establece que el atacante solo vence si supera estrictamente al defensor ($FC_A > FC_D$). En caso de empate, la victoria es otorgada al defensor.
- **Gobernante atacante o defensor derrotado**: Se contempló el Jaque Mate en ambos sentidos; la muerte del rey elimina a la nación y transfiere todo su territorio restante al vencedor de forma automática.
- **Declaraciones múltiples de guerra en un mismo turno**: Se contempló el parámetro `es_multiguerra` para sumar los $-10\%$ adicionales a partir de la segunda declaración en el mismo turno.
- **Expiración de Ceasefire**: Al llegar a 0 turnos de ceasefire, la relación transiciona de forma transparente a `NEUTRAL` permitiendo futuras declaraciones de guerra.
- **Límite de turnos alcanzado sin ganador**: Retorna formalmente el estado `EMPATE_DERROTA` con ganador `None`.

## Pendientes / limitaciones conocidas

- **Integración con la rama `feature/economia-poblacion`**: El motor WEGO ya cuenta con los hooks listos para conectar las funciones de recaudación, mantenimiento, revueltas y bancarrota cuando ambas ramas se integren en `develop`.
- **Integración con la interfaz de consola**: La interfaz de usuario que construirá Theryan en `feature/interfaz-consola` se encargará de solicitar las órdenes interactivas al usuario humano y llamar a `MotorSimulacionWEGO.ejecutar_ciclo_turno()`.
