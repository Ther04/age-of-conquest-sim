# Decisiones de diseño — Ajustes Finales, Usabilidad y Validación Interactiva en Consola

- **Autor:** Ismael Hidalgo
- **Rama:** feature/combate-diplomacia-motor
- **Fecha:** 2026-08-19
- **Referencia en la Formalización/Modelo Conceptual:** Formalización Cuantitativa §Submodelo de Resolución de Combate, §Paso 2: Cobro de Ingresos y Tesorería, §Algoritmo del Despachador de la LEF; Modelo Conceptual §6, §7 (FEL), §9.1, §9.3; Game Manual §Diplomacy, §Economy, §How to Play.

## Objetivo de la feature

Esta feature complementa el motor y la interfaz de consola con mecanismos de usabilidad, validación temprana interactiva y feedback financiero, adaptando la experiencia de simulación a un entorno de texto sin interfaz gráfica. Provee visualización de topología de mapa en anillo (ASCII), validación de órdenes en tiempo real para evitar la pérdida involuntaria de turnos por errores tipográficos, gestión asíncrona de tratados diplomáticos (proponer, aceptar, rechazar) y desglose transparente de los cálculos de ingresos y mantenimiento al final de cada turno.

## Lógica seguida

1. **Validación Interactiva Temprana de Órdenes (`src/interfaz_consola.py`)**:
   - Al recibir comandos en la consola (`mover`, `atacar`, `reclutar`, `muralla`, `torre`, `pillar`, `guerra`), el sistema verifica las precondiciones espaciales y económicas antes de encolar el evento en la FEL:
     - **Pertenencia:** Se valida que la provincia pertenezca a la nación emisora (`prov in nacion.provincias`).
     - **Adyacencia de Grafo:** Se comprueba que `destino in mapa[origen].vecinos`.
     - **Disponibilidad de Recursos:** Se valida que existan suficientes tropas (`cant <= mapa[origen].tropas`) o tesorería (`nacion.tesoreria >= costo`).
     - **Estado de Guerra:** Si se intenta atacar una provincia enemiga sin estado de guerra previo, la consola avisa al jugador que debe declarar la guerra primero con `guerra <id>`.
   - Si la validación falla, se imprime un mensaje de error descriptivo con las opciones válidas y **no se consume la acción**, permitiendo al jugador reingresar su orden correctamente.

2. **Bandeja de Entrada Diplomática Bilateral (`src/simulacion.py` y `src/interfaz_consola.py`)**:
   - Se añadió la estructura `Partida.propuestas_pendientes: dict[int, list[tuple[str, int]]]`.
   - Cuando una nación ejecuta `paz <id>` o `alianza <id>`, la propuesta se encola y se almacena en la bandeja del receptor.
   - Al inicio del turno de la nación receptora, la consola muestra una notificación con las solicitudes pendientes.
   - Se añadieron los comandos interactivos:
     - `aceptar <paz|alianza> <id_nacion>`: aplica la transición en `GestorDiplomacia` y remueve la propuesta.
     - `rechazar <paz|alianza> <id_nacion>`: descarta la propuesta sin alterar las relaciones.

3. **Visualización Gráfica y Estructurada del Mapa (`imprimir_mapa_completo`)**:
   - Incorpora un diagrama ASCII con la topología circular del anillo de 9 provincias, visualizando las adyacencias bidireccionales.
   - Genera una tabla con todas las provincias, su propietario (o Neutral), tropas, población, felicidad, murallas, torres y vecinos directos.
   - El comando `estado` resalta claramente el número de provincias controladas (ej. `Provincias (2): [Prov 0, Prov 1]`) y las provincias hacia donde se puede mover.

4. **Desglose Financiero en el Hook de Fin de Turno (`src/simulacion.py`)**:
   - En la fase endógena, se imprime el balance económico detallado para cada nación:
     $$\text{Ingreso Bruto} - \text{Costo Admin} - \text{Mantenimiento} = \text{Flujo Neto}$$
   - Muestra la transición exacta de la tesorería ($\text{Tesorería}_{t} \rightarrow \text{Tesorería}_{t+1}$), haciendo explícito por qué una nación gana o pierde oro y cuándo se suspende la recaudación por felicidad $< 50\%$.

## Decisiones de diseño y por qué

- **Validación en capa de presentación vs. motor:** La validación temprana se ejecuta en `_leer_orden_nacion` antes de llamar a `planificar_orden()`, mientras que el motor (`MotorSimulacionWEGO` y `ejecutar_movimiento_tropas`) mantiene sus propias validaciones internas defensivas. Esto desacopla la experiencia de usuario interactiva de la integridad de la simulación.
- **Tratados diplomáticos de mutuo acuerdo:** En wargames tipo WEGO, los tratados bilaterales requieren el consentimiento de ambas partes. El uso de `propuestas_pendientes` modela fielmente esta asincronía sin bloquear el flujo del turno.
- **Transparencia económica en consola:** Al no existir una interfaz gráfica con paneles flotantes, el registro detallado en el log de fin de turno permite a los evaluadores comprobar la aplicación de las ecuaciones de $N\_I\_com$, $N\_I\_tax$, $N\_C\_adm$ y $N\_C\_upk$.

## Alternativas consideradas

- **Validar únicamente en la ejecución del ciclo WEGO:** Se descartó porque un error tipográfico involuntario de un número de provincia anulaba la orden del jugador durante todo el turno sin posibilidad de enmendarlo, lo cual resultaba frustrante en una interfaz de texto.
- **Aceptación automática de propuestas de paz:** Se descartó porque le quitaba agencia estratégica al jugador receptor de la propuesta.

## Casos borde contemplados

- **Propuestas diplomáticas duplicadas:** Se evita registrar la misma propuesta más de una vez en `propuestas_pendientes`.
- **Aceptar o rechazar propuestas inexistentes:** Si se intenta aceptar una propuesta que no fue enviada, el sistema emite un mensaje de error y no altera el estado de diplomacia.
- **Declaración de guerra con alto el fuego (Ceasefire):** La validación temprana advierte al jugador si existe un ceasefire vigente y bloquea la orden antes de incurrir en infracción.
- **Tesorería en cero durante compras:** Se impide encolar órdenes de reclutamiento o construcción si los fondos disponibles son inferiores al costo requerido.

## Validación Integral de Partida Completa (5 Turnos)

Se formalizó la suite de pruebas en [tests/test_partida_completa_5_turnos.py](file:///c:/Users/ismae/Desktop/Personal%20Documents/uni%20stuff/7%20semestre/simulacion%20de%20sistemas/proyecto/age-of-conquest-sim/tests/test_partida_completa_5_turnos.py), la cual reproduce fielmente la partida de 5 turnos jugada interactivamente:
1. **Turno 1 (Expansión y Diplomacia):** Ocupación pacífica de provincias neutrales 1 (Rojo) y 2 (Azul). Declaración de guerra de Azul a Rojo ($-4\%$ moral). Propuestas asíncronas de Verde (paz a Azul, alianza a Rojo).
2. **Turno 2 (Muralla y Defensa Lanchester):** Construcción de muralla en Prov 1 por Rojo ($50$ oro). Invasión fallida de Azul a Prov 1 ($FC_A = 5000$ vs $FC_D = 10000$), resultando en victoria defensora con 25 supervivientes. Rechazo explícito de paz por Azul.
3. **Turno 3 (Tratado y Reclutamiento):** Aceptación de alianza militar Rojo-Verde. Reclutamiento de 50 soldados en Prov 1 ($5$ oro). Expansión pacífica de Rojo a Prov 8 y Verde a Prov 5.
4. **Turno 4 (Contraataque y Conquista):** Ataque de Rojo a Prov 2 con 105 soldados frente a 50 defensores ($FC_A = 10500$ vs $FC_D = 5000$), logrando la conquista territorial con 55 supervivientes. Declaración de guerra de Azul a Verde.
5. **Turno 5 (Asalto a la Capital y Jaque Mate):** Ataque de Rojo con 55 soldados a la capital de Azul (Prov 3), defendida por 10 soldados, muralla y el Gobernante de Azul ($FC_A = 5500$ vs $FC_D = 2200$). La muerte del gobernante activa la regla de **Jaque Mate**: la Nación Azul es eliminada inmediatamente y transfiere su provincia a Rojo. Con 5 de 9 provincias bajo su control ($>50\%$), Rojo alcanza la victoria por **Supremacía**.

## Pendientes / limitaciones conocidas

- La interfaz de consola opera actualmente en modo Hotseat local por turnos.
