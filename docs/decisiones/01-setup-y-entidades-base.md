# Decisiones de diseño — Setup del proyecto y entidades base

- **Autor:** Theryan Colmenares
- **Rama:** feature/setup-proyecto-base
- **Fecha:** 2026-08-19
- **Referencia en la Formalización/Modelo Conceptual:** "Diccionario Formal de Variables y Parámetros" (Provincia, Nación, variables auxiliares) y "Parámetros y Constantes de Configuración" de la Formalización Cuantitativa; secciones 2 y 3 ("Componentes del sistema" y "Atributos de los componentes") del Modelo Conceptual.

## Objetivo de la feature

Levantar la base estructural del repositorio (carpetas, `.gitignore`, README)
y el modelo de entidades del dominio (`Provincia`, `Nacion`, `Gobernante`,
`RelacionDiplomatica`) más el módulo de constantes de configuración y la
estructura lógica del mapa, para que el resto del equipo (Henyer en
economía/población, Ismael en combate/diplomacia/motor de turnos) tenga sobre
qué construir sin bloquearse entre sí.

## Lógica seguida

1. Se creó la estructura de carpetas `src/`, `tests/`, `docs/decisiones/` y un
   `.gitignore` orientado a Python (entornos virtuales, cachés, IDEs, y una
   entrada de resguardo para que `CLAUDE.md`/`REPARTO_TAREAS.md` nunca entren
   al repo aunque se copien por error, ya que en la práctica viven un nivel
   arriba de `age-of-conquest-sim/`).
2. Cada entidad del diccionario de variables se tradujo a una clase Python con
   `@dataclass`, replicando el nombre y tipo de cada atributo tal cual la
   tabla del PDF (comentado en el código junto a cada campo, ej.
   `poblacion: int = 0  # P_pop_i(t)`), para que la trazabilidad entre la
   fórmula matemática y el código sea directa.
3. Se creó el paquete `src/entidades/` con un archivo por clase
   (`provincia.py`, `nacion.py`, `gobernante.py`,
   `relacion_diplomatica.py`) y un `__init__.py` que las re-exporta, en vez de
   un único archivo `entidades.py` monolítico — así cada clase queda aislada
   y es más fácil de extender por separado sin generar conflictos de merge
   entre integrantes.
4. `src/parametros.py` centraliza **todas** las constantes de la tabla
   "Parámetros y Constantes de Configuración" del PDF, en mayúsculas
   (convención de constantes en Python) pero conservando el nombre original
   del documento como referencia en el comentario de cada línea.
5. `src/mapa.py` implementa `crear_mapa_anillo()`: genera `TotalProvinces`
   provincias (constante de `parametros.py`) conectadas en anillo (cada una
   vecina de la anterior y la siguiente), y reparte la población total
   (`TotalPopulation`) equitativamente entre ellas como estado inicial. Se
   probó manualmente instanciando el mapa y consultando adyacencia antes de
   commitear (ver sección "Casos borde contemplados").

## Decisiones de diseño y por qué

- **`dataclass` en vez de clases manuales con `__init__`:** menos código
  repetido, valida por igualdad de campos automáticamente (útil para pruebas),
  y dado que estas clases son principalmente contenedores de estado, encaja
  con el propósito.
- **Las entidades son "tontas" (solo datos + consultas simples), sin lógica de
  negocio:** los métodos que sí se agregaron (`puede_recaudar()`,
  `esta_pillada()`, `ha_alcanzado_victoria_por_puntos()`, etc.) son consultas
  de solo lectura sobre el propio estado, nunca cálculos que modifiquen otras
  entidades (eso pertenece a los módulos de economía/combate que aún no
  existen). Esto evita pisar el trabajo que le corresponde a Henyer e Ismael.
- **Validación de rangos en `__post_init__`:** `Provincia` y `Nacion` validan
  que `felicidad` esté en `[0,100]`, que `puntos_victoria` esté en `[0,100]`,
  que `poblacion`/`tropas`/`tesoreria` no sean negativos, etc., lanzando
  `ValueError` si se viola el dominio declarado en el diccionario de
  variables del PDF. Se hizo así para detectar temprano (en desarrollo) datos
  inconsistentes en vez de dejar que se propaguen silenciosamente por el
  motor de simulación.
- **`puntos_accion` como `float`, todo lo demás como `int`:** el diccionario
  de variables marca `N_Ap_n(t)` explícitamente como tipo `Real`; es el único
  atributo de estado que no es entero. Se documentó en el comentario del
  campo para que quede claro que no es un descuido, sino fidelidad al
  documento (el Game Manual exige aritmética entera en todos los cálculos de
  combate/economía, pero los puntos de acción sí se manejan como valor real
  antes de usarse).
- **Propietario de provincia como `Optional[int]` (id de nación o `None`):**
  se decidió no crear una "nación neutral" ficticia con id propio para
  representar provincias sin dueño, porque el modelo conceptual trata
  "Neutral" como ausencia de propietario, no como una nación más (evita tener
  que excluir esa pseudo-nación en cada iteración sobre `naciones activas`).
- **Mapa en topología de anillo, generado por función y no hardcodeado:** la
  tarea no exige mapas ni geografía real (`tarea.md`: "No se requiere
  replicar la interfaz gráfica o los mapas"), así que se optó por la
  estructura lógica más simple que aún permite probar adyacencia, ataques y
  revueltas de forma realista. Se dejó como función parametrizable
  (`crear_mapa_anillo(num_provincias=...)`) para poder generar mapas más
  chicos en pruebas unitarias sin tocar el código de producción.

## Alternativas consideradas

- Se consideró un único archivo `entidades.py` con las 4 clases juntas; se
  descartó por legibilidad y porque el equipo va a tocar estas clases en
  paralelo durante la integración (menos probabilidad de conflictos de merge
  con archivos separados).
- Se consideró generar el mapa como una grilla 2D en vez de un anillo, para
  parecerse más a un mapa real; se descartó por ahora porque agrega
  complejidad (coordenadas, cálculo de vecinos por distancia) sin aportar
  nada a la validación de las fórmulas económicas/de combate, que es el foco
  real de la evaluación. Puede revisitarse si sobra tiempo.

## Casos borde contemplados

- `Provincia`/`Nacion` lanzan `ValueError` si se instancian con felicidad o
  puntos de victoria fuera de `[0,100]`, o con población/tropas/tesorería
  negativas — para que un error de cálculo en otro módulo se detecte de
  inmediato en vez de generar un estado inválido silencioso.
- `crear_mapa_anillo(num_provincias=1)` se contempló explícitamente (evita
  que una provincia quede señalada como vecina de sí misma) aunque no es un
  caso que vaya a usarse en la partida real (`TotalProvinces = 20`).
- Se verificó manualmente (antes de commitear) que `crear_mapa_anillo(20)`
  genera 20 provincias, que la provincia `0` es vecina de `1` y `19`, y que
  `son_adyacentes(mapa, 0, 5)` da `False` — confirma que la topología de
  anillo quedó bien construida.

## Pendientes / limitaciones conocidas

- Falta el módulo de interfaz de consola (bucle de turnos) — depende de que
  Henyer e Ismael tengan sus módulos de economía y combate/motor listos para
  integrarlos.
- `RelacionDiplomatica` todavía no maneja el registro central de relaciones
  entre todas las naciones (¿dict indexado por par de ids? ¿lista?); esa
  decisión se deja para cuando Ismael empiece el motor de turnos y diplomacia,
  ya que es quien mejor conoce cómo se van a consultar esas relaciones desde
  el algoritmo round-robin.
- No se agregó todavía ninguna prueba automatizada (`pytest`) — por ahora la
  validación fue manual vía consola. Se recomienda que cada quien agregue
  pruebas en `tests/` a medida que avance su propia feature.
