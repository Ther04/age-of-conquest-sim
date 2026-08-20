# Decisiones de diseño — Submodelo Económico, Poblacional y de Felicidad

- **Autor:** Henyer Molina
- **Rama:** feature/economia-poblacion
- **Fecha:** 2026-08-19
- **Referencia en la Formalización/Modelo Conceptual:** Formalización Cuantitativa §Submodelo Económico y Poblacional, §Submodelo de Atrición, Pillaje y Revueltas, §Inanición Territorial (Sin Provincias), y §Ejemplo 1; Modelo Conceptual §2.7, §4.1, §4.2, §9.5, §9.6, §9.7.

## Objetivo de la feature

Esta feature implementa el núcleo del motor financiero, de crecimiento demográfico y de control de felicidad del simulador. Modela las transferencias financieras, el cobro de impuestos y comercio, el costo de administración no lineal, el mantenimiento militar (upkeep), la atrición en territorio no aliado, las revueltas, y el desbande forzoso de tropas por bancarrota nacional, asegurando la correspondencia exacta con las fórmulas matemáticas del documento de Formalización.

## Lógica seguida

La feature se implementó en el módulo [src/economia.py](file:///home/gozard/Documentos/padre/age-of-conquest-sim/src/economia.py) mediante funciones puras y auxiliares que operan sobre el estado de `Provincia` y `Nacion`:

1. **`crecer_poblacion(mapa)`**: Se tradujo la ecuación de crecimiento:
   $$P\_pop\_i(t+1) = P\_pop\_i(t) + \lfloor r\_grow \cdot P\_pop\_i(t) \cdot (P\_H\_i(t) - 50) / 100 \rfloor$$
   Dado que $r\_grow = 0.02$, en aritmética entera esto equivale a `(2 * pop * (happiness - 50)) // 10000`. Se usa la división entera (`//`) de Python porque realiza la función `floor` exacta hacia $-\infty$ para valores negativos.
2. **`calcular_ingresos(nacion, mapa, turno)`**: Calcula el comercio de cada provincia de la nación que `puede_recaudar()` (felicidad $\ge 50$ y sin pillaje). Asimismo, calcula el impuesto (`poblacion // 100`) para cada provincia que cumple la misma condición. El impuesto anual solo se suma al ingreso bruto si `turno % 12 == 0`.
3. **`calcular_costo_administracion(nacion, mapa, ingreso_bruto)`**: Traduce la fórmula no lineal:
   $$\text{Costo} = \lfloor Cap\_adm \cdot \sqrt{x_n} \cdot Ingreso\_Bruto \rfloor$$
   donde $x_n = 0.5 \cdot (\text{provincias\_nación} / \text{Provincias\_Totales}) + 0.5 \cdot (\text{población\_nación} / \text{Población\_Total})$.
4. **`calcular_mantenimiento_militar(nacion, mapa)`**: Calcula el mantenimiento de las guarniciones sumando `max(COST_UPK_MIN, floor(tropas * COST_UPK_BASE / 100))` para cada provincia con tropas.
5. **`actualizar_tesoreria_y_ap(...)`**: Aplica el flujo neto a la tesorería de la nación `max(0, tesoreria + neto - upkeep)` e incrementa los puntos de acción según:
   $$N\_Ap\_n(t+1) = AP\_BASE + AP\_CARRY\_RATE \cdot \text{ap\_unused} + \lfloor 0.1 \cdot \sqrt{\text{count}(N\_provinces\_n)} \rfloor$$
6. **`actualizar_felicidad(nacion, mapa, relaciones, eventos)`**: Ajusta la felicidad de las provincias. Si la provincia experimentó un evento este turno (victoria: +1, derrota: -1, pillaje: -15, festival: +20), este anula el cambio estándar. De lo contrario, se aplica el efecto impositivo (+2 si LOW, 0 si MEDIUM, -4 si HIGH) más el efecto de guerras activas ($\max(-3, -1 \cdot \text{guerras\_activas})$). Recalcula la felicidad promedio nacional como la media simple de sus provincias.
7. **`aplicar_atricion(mapa, naciones, relaciones)`**: Aplica un desgaste de $-13\%$ (`tropas = floor(tropas * 0.87)`) en provincias ajenas no aliadas ni protectorados.
8. **`evaluar_revueltas(mapa, naciones, gobernantes, relaciones, random)`**: Evalúa las provincias con felicidad $< 50$. Si no hay gobernante ni suficientes tropas (1 por cada 2500 habitantes), la probabilidad de revuelta es $P\_rev = (50 - P\_H) / 50$. Si el número aleatorio es menor a $P\_rev$, la provincia se independiza de la nación: si tiene vecinos de otras naciones activas se anexa a una de ellas (con preferencia a la de mayor felicidad), de lo contrario pasa a ser Neutral (y resta $-1\%$ a la felicidad de la nación original).
9. **`aplicar_desbande_bancarrota(naciones, mapa, net_incomes, military_upkeeps)`**: Si la tesorería queda en 0 y el upkeep militar supera lo disponible, se calcula la cantidad de soldados a desbandar:
   $$\text{Soldados\_Desbandar} = \lceil (\text{upkeep} - \text{net\_income}) \cdot 100 / COST\_UPK\_BASE \rceil$$
   Se ejecuta `desbandar_tropas()` de forma rotativa restando de a 100 soldados, priorizando las provincias con menor felicidad.
10. **`evaluar_eliminacion_inanicion(naciones)`**: Si una nación tiene 0 provincias (exilio), su felicidad se resetea a 50% en el primer turno y disminuye $-2\%$ por turno en los siguientes. Al llegar a 0%, se elimina la nación.

## Decisiones de diseño y por qué

- **Aritmética entera pura con operadores de Python**: Se utilizó `//` para la división de enteros, lo que garantiza el comportamiento matemático de `floor` en números negativos sin floats intermediarios (ej. `(P_H - 50) // 10000` decrece la población de forma simétrica a cómo crece).
- **Control de eventos de felicidad vía diccionario**: Dado que `Provincia` no contiene campos mutables de eventos ocurridos en el turno, la función `actualizar_felicidad` recibe un diccionario opcional `provincias_con_eventos` para procesar los cambios abruptos de felicidad de forma modular sin contaminar el estado permanente de la provincia.
- **Tolerancia determinista en revueltas y desbandes**: Se ordenan los conjuntos de provincias bajo criterios estables (felicidad ascendente y ID de provincia como clave de desempate) para que el orden de evaluación de revueltas y desbandes sea determinista y reproducible bajo las mismas condiciones.
- **Costo de administración con floats limitados a `math.sqrt`**: Dado que la fórmula de administración requiere una raíz cuadrada ($\sqrt{x_n}$), se realiza el cálculo de $x_n$ y su raíz con aritmética de punto flotante de Python, y el resultado final se redondea hacia abajo inmediatamente con `math.floor()`, minimizando cualquier impacto de precisión de punto flotante en el juego.

## Alternativas consideradas

- **Representar tropas como entidades independientes**: Se descartó porque en el diccionario formal de la Formalización Cuantitativa, las tropas son un atributo de la provincia (`P_M_i`), no un componente independiente. Esto simplifica el código al evitar mapear y sincronizar una lista de tropas con los IDs de provincias.
- **Representar la nación Neutral como una entidad Nacion con id=0**: Se descartó para evitar bucles innecesarios. Se representa con `propietario=None` en la provincia, lo que simplifica las comprobaciones de neutralidad (`es_neutral()`).

## Casos borde contemplados

- **Población en 0**: Si la población llega a 0, la provincia no genera crecimiento ni puede recaudar impuestos (el impuesto es `0 // 100 = 0`).
- **Felicidad en límites [0, 100]**: Todos los deltas de felicidad se acotan usando `max(0, min(100, ...))` para evitar que se desborden de los límites de porcentaje.
- **División por cero en el promedio de felicidad**: Si una nación en exilio tiene 0 provincias, la felicidad promedio no se calcula con división entre cero, sino que se devuelve 50% por defecto (reiniciando el exilio).
- **Desbande rotativo con tropas insuficientes**: Si una provincia se queda con menos de 100 soldados en el desbande rotativo, se desbanda el total de tropas que tiene (usando `min(prov.tropas, min(100, total_a_desbandar))`) y se elimina de la lista de provincias con guarnición para evitar bucles infinitos.

## Pendientes / limitaciones conocidas

- **Integración del flujo WEGO**: El decremento del cooldown de pillaje `cooldown_pillaje = max(0, cooldown_pillaje - 1)` se ejecuta al final de los turnos en el motor WEGO. Se asume que el motor de turnos (módulo de Ismael) llamará a la lógica de economía en la fase endógena en el orden secuencial correcto.
- **Detalle de las acciones opcionales**: Las acciones de festivales y distribución de dinero se implementaron a nivel de API para que la interfaz de consola de Theryan las pueda ejecutar gastando oro de la tesorería de la nación y afectando felicidad/población de forma directa.
