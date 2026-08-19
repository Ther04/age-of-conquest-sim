"""
Submodelo Económico, Poblacional y de Felicidad.

Ver: Formalización Cuantitativa y Lógica del Sistema - AgeofConquest,
     secciones "Submodelo Económico y Poblacional", "Submodelo de Atrición, Pillaje y Revueltas"
     y "Inanición Territorial (Sin Provincias)".

Este módulo contiene la lógica de negocio para actualizar el estado financiero,
poblacional y moral de las provincias y de las naciones al final de cada turno.
Toda la aritmética se maneja de manera entera (salvo AP_CARRY_RATE y AP_BASE)
para cumplir con el principio de reproducibilidad del wargame original.
"""

import math
from typing import Optional, Tuple, Dict, List
from .entidades.provincia import Provincia
from .entidades.nacion import Nacion, TasaImpuestos
from .entidades.relacion_diplomatica import RelacionDiplomatica, TipoRelacion
from .parametros import (
    R_GROW,
    CAP_ADM,
    TOTAL_PROVINCES,
    TOTAL_POPULATION,
    COST_UPK_MIN,
    COST_UPK_BASE,
    AP_BASE,
    AP_CARRY_RATE,
    REVOLT_PREV_RATIO,
    HAPPINESS_THRESHOLD,
    PILLAGE_COOLDOWN_TURNS,
    PILLAGE_HAPPINESS_PENALTY,
    FISCAL_YEAR_TURNS,
)


def ceil_div(a: int, b: int) -> int:
    """Realiza la división entera redondeando hacia arriba (ceiling division)."""
    return (a + b - 1) // b


# --- Paso 1: Crecimiento de Población ---

def crecer_poblacion(mapa: Dict[int, Provincia]) -> None:
    """
    Paso 1: Crecimiento de Población.
    Actualiza la población de cada provincia según su felicidad y la tasa de crecimiento natural.
    Ver Formalización Cuantitativa §Paso 1: Crecimiento de Población.
    
    Ecuaciones:
    P_pop_i(t+1) = P_pop_i(t) + P_F_dPop_i(t)
    P_F_dPop_i(t) = floor( r_grow * P_pop_i(t) * (P_H_i(t) - 50) / 100 )
    """
    for provincia in mapa.values():
        if provincia.poblacion > 0:
            # Dado que R_GROW = 0.02 (2 / 100), la multiplicación por r_grow se traduce en
            # multiplicar por 2 y dividir entre 100.
            # R_GROW * P_pop * (P_H - 50) / 100 => 2 * P_pop * (P_H - 50) / 10000.
            # En Python, el operador // realiza la división entera 'floor' (hacia menos infinito),
            # lo que modela exactamente la función 'floor' matemática para valores positivos y negativos.
            delta_pop = (2 * provincia.poblacion * (provincia.felicidad - 50)) // 10000
            
            # Asegura la no negatividad de la población
            provincia.poblacion = max(0, provincia.poblacion + delta_pop)


# --- Paso 2: Cobro de Ingresos y Tesorería ---

def calcular_ingresos(nacion: Nacion, mapa: Dict[int, Provincia], turno: int) -> Tuple[int, int, int]:
    """
    Calcula los ingresos de comercio e impuestos de la nación en el turno actual.
    Ver Formalización Cuantitativa §Paso 2: Cobro de Ingresos y Tesorería.
    
    Ecuaciones:
    N_I_com_n(t) = sum_{i in N_provinces_n(t)} ( P_com_base_i * I(P_H_i(t) >= 50) * I(P_cd_i(t) == 0) )
    N_I_tax_n(t) = sum_{i in N_provinces_n(t)} ( floor(P_pop_i(t) / 100) * I(P_H_i(t) >= 50) * I(P_cd_i(t) == 0) )
    N_F_brt_n(t) = N_I_com_n(t) + N_I_tax_n(t) * delta(t mod 12)
    
    Retorna:
        Tuple[comercio_total, impuesto_total, ingreso_bruto]
    """
    comercio_total = 0
    impuesto_total = 0
    
    for pid in nacion.provincias:
        provincia = mapa[pid]
        # provincia.puede_recaudar() encapsula la condición: felicidad >= 50 y cooldown_pillaje == 0
        if provincia.puede_recaudar():
            comercio_total += provincia.comercio_base
            impuesto_total += provincia.poblacion // 100
            
    # El impuesto anual se cobra cada 12 turnos (fin de año fiscal).
    # t mod 12 == 0. Por ejemplo, en el turno 12, 24, 36, etc.
    if turno > 0 and turno % FISCAL_YEAR_TURNS == 0:
        ingreso_bruto = comercio_total + impuesto_total
    else:
        ingreso_bruto = comercio_total
        
    return comercio_total, impuesto_total, ingreso_bruto


def calcular_costo_administracion(nacion: Nacion, mapa: Dict[int, Provincia], ingreso_bruto: int) -> int:
    """
    Calcula el costo financiero de administración de la nación.
    Ver Formalización Cuantitativa §Paso 2: Cobro de Ingresos y Tesorería.
    
    Ecuaciones:
    N_C_adm_n(t) = floor( Cap_adm * sqrt(x_n(t)) * N_F_brt_n(t) )
    x_n(t) = 0.5 * (count(N_provinces_n(t)) / TotalProvinces) + 0.5 * (sum_{i in N_provinces_n(t)} P_pop_i(t) / TotalPopulation)
    """
    if not nacion.provincias:
        return 0
        
    prop_territorio = len(nacion.provincias) / TOTAL_PROVINCES
    poblacion_nacional = sum(mapa[pid].poblacion for pid in nacion.provincias)
    prop_poblacion = poblacion_nacional / TOTAL_POPULATION
    
    x_n = 0.5 * prop_territorio + 0.5 * prop_poblacion
    
    # Costo administrativo no lineal. CAP_ADM = 0.69
    costo = math.floor(CAP_ADM * math.sqrt(x_n) * ingreso_bruto)
    return costo


def calcular_mantenimiento_militar(nacion: Nacion, mapa: Dict[int, Provincia]) -> int:
    """
    Calcula el mantenimiento militar (upkeep) de la nación.
    Ver Formalización Cuantitativa §Paso 2: Cobro de Ingresos y Tesorería.
    
    Ecuaciones:
    N_C_upk_n(t) = sum_{i in N_provinces_n(t) donde P_M_i(t) > 0} max(Cost_upk_min, floor(P_M_i(t) * Cost_upk_base / 100))
    """
    upkeep_total = 0
    
    for pid in nacion.provincias:
        provincia = mapa[pid]
        if provincia.tropas > 0:
            # COST_UPK_BASE = 5 oro por cada 100 soldados. COST_UPK_MIN = 1 oro mínimo.
            upkeep_prov = max(COST_UPK_MIN, (provincia.tropas * COST_UPK_BASE) // 100)
            upkeep_total += upkeep_prov
            
    return upkeep_total


def actualizar_tesoreria_y_ap(
    nacion: Nacion,
    mapa: Dict[int, Provincia],
    turno: int,
    gross_income: int,
    admin_cost: int,
    military_upkeep: int
) -> int:
    """
    Actualiza la tesorería de la nación y recarga sus puntos de acción.
    Ver Formalización Cuantitativa §Paso 2: Cobro de Ingresos y Tesorería.
    
    Ecuaciones de Tesorería:
    N_F_net_n(t) = N_F_brt_n(t) - N_C_adm_n(t)
    N_T_n(t+1) = max(0, N_T_n(t) + N_F_net_n(t) - N_C_upk_n(t))
    
    Ecuaciones de Puntos de Acción:
    N_Ap_n(t+1) = Ap_base + Ap_carry_rate * max(0, N_Ap_n(t) - N_Ap_used_n(t)) + floor(0.1 * sqrt(count(N_provinces_n(t))))
    
    Retorna:
        El flujo neto de ingresos (net_income) para usarse en la verificación de bancarrota.
    """
    # Flujo neto de ingresos
    net_income = gross_income - admin_cost
    
    # Actualización de tesorería
    nacion.tesoreria = max(0, nacion.tesoreria + net_income - military_upkeep)
    
    # Actualización de Puntos de Acción. AP_BASE = 2.2, AP_CARRY_RATE = 0.25
    ap_remanente = max(0.0, nacion.puntos_accion - nacion.puntos_accion_usados)
    ap_bono_provincias = math.floor(0.1 * math.sqrt(len(nacion.provincias)))
    
    nacion.puntos_accion = AP_BASE + (AP_CARRY_RATE * ap_remanente) + ap_bono_provincias
    nacion.puntos_accion_usados = 0.0
    
    return net_income


# --- Paso 3: Decaimiento y Ajuste de Moral/Felicidad ---

def actualizar_felicidad(
    nacion: Nacion,
    mapa: Dict[int, Provincia],
    relaciones: List[RelacionDiplomatica],
    provincias_con_eventos: Optional[Dict[int, str]] = None
) -> None:
    """
    Ajusta la felicidad provincial según impuestos, guerras activas y eventos específicos.
    Ver Formalización Cuantitativa §Paso 3: Decaimiento y Ajuste de Moral/Felicidad y §Cambios Abruptos de Estado.
    
    Ecuaciones:
    P_H_i(t+1) = clip(P_H_i(t) + P_F_dHap_i(t), 0, 100)
    P_F_dHap_i(t) = P_F_tax_effect_i(t) + P_F_war_effect_i(t) (si no hay eventos)
    
    Efecto Impositivo:
    P_F_tax_effect_i(t) = +2 si N_TR_n(t) == LOW, 0 si MEDIUM, -4 si HIGH
    
    Efecto de Guerras Activas:
    P_F_war_effect_i(t) = max(Pen_war_recur_cap, Pen_war_recur * N_W_active_n(t)) => max(-3, -1 * N_W_active_n(t))
    
    Eventos Específicos (mutuamente excluyentes del efecto tax+war en el turno que ocurren):
    - 'victoria': +1
    - 'derrota': -1
    - 'pillaje': -15
    - 'festival': +20
    """
    if provincias_con_eventos is None:
        provincias_con_eventos = {}
        
    # Calcular efecto impositivo
    if nacion.tasa_impuestos == TasaImpuestos.LOW:
        tax_effect = 2
    elif nacion.tasa_impuestos == TasaImpuestos.MEDIUM:
        tax_effect = 0
    else:  # HIGH
        tax_effect = -4
        
    # Calcular efecto de guerras activas
    # PEN_WAR_RECUR = -1, PEN_WAR_RECUR_CAP = -3.
    # Así: max(-3, -1 * nacion.guerras_activas)
    war_effect = max(-3, -1 * nacion.guerras_activas)
    
    suma_felicidad = 0
    
    for pid in nacion.provincias:
        provincia = mapa[pid]
        evento = provincias_con_eventos.get(pid)
        
        if evento == 'victoria':
            delta_hap = 1
        elif evento == 'derrota':
            delta_hap = -1
        elif evento == 'pillaje':
            delta_hap = -15
        elif evento == 'festival':
            delta_hap = 20
        else:
            # Caso estándar: efecto de impuestos y guerras activas
            delta_hap = tax_effect + war_effect
            
        provincia.felicidad = max(0, min(100, provincia.felicidad + delta_hap))
        suma_felicidad += provincia.felicidad
        
    # Actualizar la felicidad nacional promedio N_H_prom_n(t+1)
    if nacion.provincias:
        nacion.felicidad_promedio = suma_felicidad // len(nacion.provincias)
    else:
        nacion.felicidad_promedio = 50


# --- Paso 4: Atrición Militar ---

def son_aliados_o_protectorado(nacion_a: int, nacion_b: int, relaciones: List[RelacionDiplomatica]) -> bool:
    """Verifica si dos naciones tienen una relación de alianza o protectorado."""
    if nacion_a == nacion_b:
        return True
    for rel in relaciones:
        if rel.involucra(nacion_a) and rel.involucra(nacion_b):
            if rel.tipo in (TipoRelacion.ALIANZA, TipoRelacion.PROTECTOR, TipoRelacion.PROTECTORADO):
                return True
    return False


def provincia_requiere_atricion(provincia: Provincia, nacion_id: int, relaciones: List[RelacionDiplomatica]) -> bool:
    """
    Retorna True si la provincia no pertenece a la nación de las tropas
    ni a sus aliados o protectorados (requiere desgaste por atrición en Open Travel).
    """
    if provincia.propietario is None:
        return True  # Provincia neutral es territorio no aliado
    if provincia.propietario == nacion_id:
        return False
    return not son_aliados_o_protectorado(provincia.propietario, nacion_id, relaciones)


def aplicar_atricion(
    mapa: Dict[int, Provincia],
    naciones: Dict[int, Nacion],
    relaciones: List[RelacionDiplomatica],
    open_travel: bool = True
) -> None:
    """
    Paso 4: Atrición Militar (Modo Open Travel).
    Aplica desgaste por atrición (-13%) al final del turno a las tropas estacionadas
    en provincias no aliadas ni protectorados.
    Ver Formalización Cuantitativa §Atrición Militar y Paso 4.
    
    Ecuaciones:
    P_F_atr_i(t) = floor(P_M_i(t) * Pen_attrition) = floor(P_M_i(t) * 0.13)
    P_M_i(t+1) = max(0, P_M_i(t) - P_F_atr_i(t))
    """
    if not open_travel:
        return
        
    for nacion_id, nacion in naciones.items():
        if not nacion.activa:
            continue
            
        # El pseudocódigo hace un recorrido sobre N_provinces_n(t).
        # En una partida real, si hay "Open Travel", la nación podría tener tropas en provincias
        # ajenas (o bien, las provincias ajenas contienen tropas extranjeras).
        # Para ser fieles a la representación de Provincia (que tiene tropas y propietario),
        # si una provincia pertenece a la nación y tiene tropas, no sufrirá atrición
        # (ya que provincia.propietario == nacion_id).
        # Sin embargo, si en el futuro se implementa movimiento en tránsito, esta función
        # evaluará correctamente si la provincia requiere atrición para el dueño de las tropas.
        for pid in nacion.provincias:
            provincia = mapa[pid]
            if provincia.tropas > 0:
                if provincia_requiere_atricion(provincia, nacion_id, relaciones):
                    bajas = (provincia.tropas * 13) // 100  # PEN_ATTRITION = 0.13
                    provincia.tropas = max(0, provincia.tropas - bajas)


# --- Paso 5: Evaluación de Revueltas Estocásticas ---

def evaluar_revueltas(
    mapa: Dict[int, Provincia],
    naciones: Dict[int, Nacion],
    gobernantes: List[any],  # Lista de objetos Gobernante
    relaciones: List[RelacionDiplomatica],
    random_generator  # Objeto random con método .random()
) -> List[Tuple[int, int, Optional[int]]]:
    """
    Paso 5: Evaluación de Revueltas Estocásticas.
    Si la felicidad de una provincia es < 50%, y no hay gobernante ni suficientes tropas,
    existe probabilidad de revuelta (50 - P_H)/50.
    Si ocurre la revuelta, la provincia se independiza y se anexa al vecino interesado,
    o en su defecto pasa a ser NEUTRAL (restando -1% a la felicidad nacional).
    Ver Formalización Cuantitativa §Probabilidad de Revuelta Estocástica y Paso 5.
    
    Ecuación de prevención por tropas:
    P_M_i >= ceil(P_pop_i / 2500)
    
    Ecuación de probabilidad:
    P_rev_i = (50 - P_H_i) / 50
    
    Retorna:
        Una lista de tuplas indicando las revueltas ocurridas: (id_provincia, id_nacion_antigua, id_nacion_nueva)
    """
    revueltas_ocurridas = []
    
    for nacion_id, nacion in list(naciones.items()):
        if not nacion.activa or not nacion.provincias:
            continue
            
        for pid in list(nacion.provincias):
            provincia = mapa[pid]
            
            # Condición de activación: felicidad < 50
            if provincia.felicidad >= HAPPINESS_THRESHOLD:
                continue
                
            # Condición de prevención: gobernante presente
            gobernante_presente = False
            for gob in gobernantes:
                # gob.esta_en(pid) devuelve True si está vivo y en pid, y pertenece a la nación de la provincia
                if gob.nacion_propietaria == nacion_id and gob.esta_en(pid):
                    gobernante_presente = True
                    break
            
            if gobernante_presente:
                continue
                
            # Condición de prevención: tropas suficientes (1 soldado por cada 2500 habitantes)
            # P_M_i >= ceil(P_pop_i / Revolt_prev_ratio)
            tropas_requeridas = ceil_div(provincia.poblacion, REVOLT_PREV_RATIO)
            if provincia.tropas >= tropas_requeridas:
                continue
                
            # Calcular probabilidad de revuelta
            p_rev = (50 - provincia.felicidad) / 50.0
            
            if random_generator.random() < p_rev:
                # ¡Ocurre la revuelta! La provincia se independiza
                nacion.provincias.discard(pid)
                
                # Buscar vecino interesado (nación vecina que esté activa y no sea la nación actual)
                vecinos_candidatos = []
                for vecino_id in provincia.vecinos:
                    vecino_prov = mapa[vecino_id]
                    if vecino_prov.propietario is not None and vecino_prov.propietario != nacion_id:
                        vecino_nac = naciones.get(vecino_prov.propietario)
                        if vecino_nac and vecino_nac.activa:
                            vecinos_candidatos.append(vecino_nac)
                            
                nuevo_propietario_id = None
                if vecinos_candidatos:
                    # Se anexa al vecino interesado. Para resolver ambigüedad,
                    # elegimos al vecino con mayor felicidad promedio nacional.
                    vecinos_candidatos.sort(key=lambda n: n.felicidad_promedio, reverse=True)
                    vecino_elegido = vecinos_candidatos[0]
                    nuevo_propietario_id = vecino_elegido.id_nacion
                    
                    provincia.propietario = nuevo_propietario_id
                    vecino_elegido.provincias.add(pid)
                    # En una revuelta exitosa que anexa la provincia a un vecino,
                    # la guarnición antigua se destruye y la nueva entra en 0 o se establece.
                    # Asumimos que las tropas de la nación de origen se destruyen (pasan a 0)
                    provincia.tropas = 0
                else:
                    # De lo contrario pasa a estado NEUTRAL, restando adicionalmente -1% de felicidad nacional
                    provincia.propietario = None
                    provincia.tropas = 0  # Guarnición de origen destruida
                    nacion.felicidad_promedio = max(0, nacion.felicidad_promedio - 1)
                    
                revueltas_ocurridas.append((pid, nacion_id, nuevo_propietario_id))
                
    return revueltas_ocurridas


# --- Paso 6: Desbande Forzoso por Bancarrota ---

def desbandar_tropas(nacion: Nacion, mapa: Dict[int, Provincia], total_a_desbandar: int) -> int:
    """
    Desbanda la cantidad de tropas indicada, restando de a 100 soldados de forma rotativa,
    priorizando las provincias de la nación con menor felicidad.
    Ver Formalización Cuantitativa §Submodelo de Atrición, Pillaje y Revueltas - DesbandarTropas.
    
    Retorna:
        El total de soldados desbandados en la ejecución.
    """
    def obtener_provincias_con_guarnicion() -> List[Provincia]:
        # Filtra las provincias de la nación que tienen tropas y las ordena
        # por felicidad ascendente, usando id_provincia como desempate determinista.
        provincias = []
        for pid in nacion.provincias:
            prov = mapa[pid]
            if prov.tropas > 0:
                provincias.append(prov)
        provincias.sort(key=lambda p: (p.felicidad, p.id_provincia))
        return provincias

    provincias_con_tropas = obtener_provincias_con_guarnicion()
    soldados_desbandados_total = 0
    
    while total_a_desbandar > 0 and len(provincias_con_tropas) > 0:
        for prov in provincias_con_tropas:
            if prov.tropas > 0 and total_a_desbandar > 0:
                # Desbanda múltiplos de 100 o el total a desbandar
                desbandados = min(prov.tropas, min(100, total_a_desbandar))
                prov.tropas -= desbandados
                total_a_desbandar -= desbandados
                soldados_desbandados_total += desbandados
                
        # Re-evaluar guarniciones (elimina provincias que se quedaron sin tropas)
        provincias_con_tropas = obtener_provincias_con_guarnicion()
        
    return soldados_desbandados_total


def aplicar_desbande_bancarrota(
    naciones: Dict[int, Nacion],
    mapa: Dict[int, Provincia],
    net_incomes: Dict[int, int],
    military_upkeeps: Dict[int, int]
) -> Dict[int, int]:
    """
    Paso 6: Desbande Forzoso por Bancarrota.
    Si la tesorería de una nación es 0 y el costo de mantenimiento militar supera sus ingresos netos,
    se calcula la cantidad de soldados a desbandar y se ejecuta el desbande rotativo.
    Ver Formalización Cuantitativa §Desbande Forzoso por Bancarrota y Paso 6.
    
    Ecuación:
    Soldados_Desbandar = ceil( (N_C_upk_n(t) - (N_T_n(t) + N_F_net_n(t))) * 100 / Cost_upk_base )
    
    Retorna:
        Un diccionario que asocia id_nacion con la cantidad de soldados desbandados.
    """
    desbandes = {}
    for nacion_id, nacion in naciones.items():
        if not nacion.activa:
            continue
            
        upkeep = military_upkeeps.get(nacion_id, 0)
        net_income = net_incomes.get(nacion_id, 0)
        
        # Ocurre si la tesorería quedó en 0 y el mantenimiento militar supera lo disponible (oro + neto)
        # Nota: La tesorería ya fue actualizada en el Paso 2 (con max(0, ...)).
        # Si la actualización de tesorería resultó en 0, y el upkeep superó la tesorería anterior + neto:
        if nacion.tesoreria == 0 and upkeep > (nacion.tesoreria + net_income):
            exceso = upkeep - net_income # ya que nacion.tesoreria es 0
            soldados_a_desbandar = ceil_div(exceso * 100, COST_UPK_BASE)
            
            desbandados = desbandar_tropas(nacion, mapa, soldados_a_desbandar)
            desbandes[nacion_id] = desbandados
            
    return desbandes


# --- Paso 7: Evaluación de Eliminación ---

def evaluar_eliminacion_inanicion(naciones: Dict[int, Nacion]) -> List[int]:
    """
    Paso 7: Evaluación de Eliminación por Inanición Territorial.
    Si una nación pierde todas sus provincias pero su gobernante sobrevive:
    - Primer turno en exilio: felicidad promedio se resetea a 50%.
    - Turnos posteriores: disminuye -2% por turno.
    - Si llega a 0%, la nación es eliminada definitivamente (activa = False).
    Ver Formalización Cuantitativa §Inanición Territorial (Sin Provincias) y Paso 7.
    
    Retorna:
        Lista de ids de naciones eliminadas en este paso.
    """
    eliminadas = []
    
    for nacion in naciones.values():
        if not nacion.activa:
            continue
            
        # Si tiene provincias, restablece el flag de exilio
        if len(nacion.provincias) > 0:
            nacion.en_exilio = False
            continue
            
        # Si no tiene provincias y sigue activa (exilio):
        if not nacion.en_exilio:
            # Primer turno de exilio sin tierras
            nacion.en_exilio = True
            nacion.felicidad_promedio = 50
        else:
            # Turnos posteriores en exilio
            nacion.felicidad_promedio = max(0, nacion.felicidad_promedio - 2)
            
        # Si llega a 0%, es eliminada definitivamente
        if nacion.felicidad_promedio <= 0:
            nacion.activa = False
            eliminadas.append(nacion.id_nacion)
            
    return eliminadas


# --- Funciones de Acciones Opcionales (Nivel de Nación y Provincia) ---

def realizar_fiesta_inauguracion(nacion: Nacion, provincia: Provincia) -> None:
    """
    Acción opcional de Asentamiento: Fiesta de Inauguración.
    Se puede realizar la primera vez que se toma posesión de una nueva provincia.
    Cuesta un costo fijo (ej. 20 oro, ver Game Manual) y aumenta significativamente la felicidad (+20%).
    """
    costo_fiesta = 20  # Costo representativo razonable
    if nacion.tesoreria < costo_fiesta:
        raise ValueError(f"Oro insuficiente para fiesta de inauguración. Costo: {costo_fiesta}, Tesorería: {nacion.tesoreria}")
        
    nacion.tesoreria -= costo_fiesta
    provincia.felicidad = min(100, provincia.felicidad + 20)


def realizar_distribuir_dinero_provincia(nacion: Nacion, provincia: Provincia, cantidad_oro: int) -> None:
    """
    Acción opcional de Asentamiento: Distribuir Dinero en provincia.
    Aumenta la felicidad de una provincia a cambio de oro.
    Fórmula de aumento: +1% de felicidad por cada 2 monedas de oro (ejemplo razonable).
    """
    if nacion.tesoreria < cantidad_oro:
        raise ValueError("Oro insuficiente en tesorería.")
    if cantidad_oro <= 0:
        raise ValueError("La cantidad de oro a distribuir debe ser mayor a 0.")
        
    nacion.tesoreria -= cantidad_oro
    aumento_felicidad = cantidad_oro // 2
    provincia.felicidad = min(100, provincia.felicidad + aumento_felicidad)


def realizar_distribuir_dinero_nacion(nacion: Nacion, mapa: Dict[int, Provincia], cantidad_oro_por_provincia: int) -> None:
    """
    Acción opcional de Nación: Distribuir Dinero a nivel nacional.
    Incrementa la felicidad en todas las provincias. Una vez por turno.
    Costo total: cantidad_oro_por_provincia * numero_provincias.
    """
    num_provs = len(nacion.provincias)
    if num_provs == 0:
        return
        
    costo_total = cantidad_oro_por_provincia * num_provs
    if nacion.tesoreria < costo_total:
        raise ValueError(f"Oro insuficiente para distribución nacional. Costo: {costo_total}, Tesorería: {nacion.tesoreria}")
        
    nacion.tesoreria -= costo_total
    aumento_felicidad = cantidad_oro_por_provincia // 2
    
    for pid in nacion.provincias:
        provincia = mapa[pid]
        provincia.felicidad = min(100, provincia.felicidad + aumento_felicidad)


def realizar_festival_fertilidad_provincia(nacion: Nacion, provincia: Provincia) -> None:
    """
    Acción opcional de Asentamiento: Festival de Fertilidad.
    Eleva significativamente la población de la provincia (+5% de la población actual).
    Cuesta un costo proporcional a la población (ej. 1% de la población en oro).
    Cooldown de 6 turnos (meses) en la provincia.
    """
    costo_festival = max(10, provincia.poblacion // 100)
    if nacion.tesoreria < costo_festival:
        raise ValueError(f"Oro insuficiente para festival de fertilidad. Costo: {costo_festival}")
        
    nacion.tesoreria -= costo_festival
    
    # Aumentar la población en 5%
    aumento_pop = (provincia.poblacion * 5) // 100
    provincia.poblacion += aumento_pop
    
    # Aumenta la felicidad (+20% por celebrar festival)
    provincia.felicidad = min(100, provincia.felicidad + 20)
