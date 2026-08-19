"""
Parámetros y constantes de configuración del simulador.

Ver: Formalización Cuantitativa y Lógica del Sistema - AgeofConquest,
     sección "Parámetros y Constantes de Configuración".

Estos valores son fijos por diseño del juego original (Game Manual) y no deben
recalcularse ni "ajustarse" dentro del código de simulación: cualquier fórmula
que los use debe referenciarlos desde aquí para mantener un único punto de
verdad y facilitar la validación contra los ejemplos numéricos del documento.

Salvo AP_BASE y AP_CARRY_RATE (que son tasas/proporciones reales usadas para
calcular N_Ap_n(t), el único atributo de tipo Real del diccionario de
variables), el resto de los parámetros se usan siempre dentro de operaciones
de aritmética entera (floor/ceil/max/min), tal como exige el Game Manual
("only integer math is used throughout the game").
"""

# --- Puntos de acción ---
AP_BASE = 2.2  # puntos_accion / turno (base por turno)
AP_CARRY_RATE = 0.25  # proporción de puntos de acción no usados que se acumulan

# --- Costos ---
COST_UPK_BASE = 5  # oro / (100 soldados * turno) — mantenimiento militar
COST_UPK_MIN = 1  # oro / (provincia * turno) — mínimo por provincia con tropas
COST_RECRUIT = 10  # oro por cada 100 soldados reclutados
COST_WALL = 50  # oro — costo de construcción de muralla

# --- Mapa ---
TOTAL_PROVINCES = 20  # cantidad total de provincias en el mapa de juego
TOTAL_POPULATION = 200_000  # habitantes totales en el mapa de juego

# --- Administración ---
CAP_ADM = 0.69  # tope del costo de administración (69% del ingreso bruto)

# --- Combate ---
PEN_ATTRITION = 0.13  # 13% de desgaste por atrición (tropas en territorio no aliado, Open Travel)
BON_WALL_DEF = 1.00  # +100% bonificación defensiva de la muralla
BON_RULER_ATK = 1.00  # +100% bonificación de ataque del gobernante
BON_RULER_DEF = 0.30  # +30% bonificación de defensa del gobernante
PEN_NAVAL_ATK = 0.30  # -30% penalización por ataque naval sobre tierra

# --- Revueltas ---
REVOLT_PREV_RATIO = 2500  # habitantes por soldado necesarios para prevenir revuelta

# --- Diplomacia / Felicidad ---
PEN_WAR_DECL = -4  # penalización base de felicidad por declarar guerra
PEN_WAR_ACTIVE = -8  # penalización adicional por cada guerra activa que ya tenga el rival
PEN_WAR_MULTI = -10  # penalización extra por declarar más de una guerra en el mismo turno
PEN_WAR_RECUR = -1  # penalización recurrente de felicidad por turno de guerra
PEN_WAR_RECUR_CAP = -3  # tope máximo (acumulado) de la penalización recurrente

# --- Crecimiento y pillaje ---
R_GROW = 0.02  # tasa de crecimiento poblacional natural
R_PILLAGE = 0.01  # tasa de ganancia de oro de pillaje por habitante

# --- Otros umbrales de negocio (Game Manual) ---
HAPPINESS_THRESHOLD = 50  # umbral de felicidad para cobrar impuestos/comercio, revueltas, etc.
PILLAGE_COOLDOWN_TURNS = 12  # turnos de cooldown tras pillar una provincia
PILLAGE_HAPPINESS_PENALTY = 15  # penalización de felicidad al pillar (-15%)
FISCAL_YEAR_TURNS = 12  # cada cuántos turnos se cobra el impuesto anual
VICTORY_POINTS_TO_WIN = 100  # puntos de victoria necesarios para ganar la partida
