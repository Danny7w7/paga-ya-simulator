"""
Motor financiero Paga-Ya Simulador Educativo.

Escalable: toda conversión pasa por E.A. como pivote canónico.
Soporta absolutamente todas las tasas del mercado colombiano:
EM, EA, Nominal Anual MV/MA/TV/TA/SV/SA/AV/AA, Periódica MV/MA,
Efectiva Diaria/Semanal (para comparar el gota).

Sin dependencias externas. Puro + testeable.
"""

# m = periodos por año para cada nominal
M_POR_NOMINAL = {
    'NAMV': 12, 'NAMA': 12,
    'NATV': 4, 'NATA': 4,
    'NASV': 2, 'NASA': 2,
    'NAAV': 1, 'NAAA': 1,
}

TIPOS_TASA = [
    ('EM', 'Efectivo Mensual'),
    ('EA', 'Efectivo Anual'),
    ('NAMV', 'Nominal Anual Mes Vencido'),
    ('NAMA', 'Nominal Anual Mes Anticipado'),
    ('NATV', 'Nominal Anual Trimestre Vencido'),
    ('NATA', 'Nominal Anual Trimestre Anticipado'),
    ('NASV', 'Nominal Anual Semestre Vencido'),
    ('NASA', 'Nominal Anual Semestre Anticipado'),
    ('NAAV', 'Nominal Anual Año Vencido (=EA nominal)'),
    ('NAAA', 'Nominal Anual Año Anticipado'),
    ('PMV', 'Periódica Mensual Vencida (=EM)'),
    ('PMA', 'Periódica Mensual Anticipada'),
    ('ED', 'Efectiva Diaria'),
    ('ES', 'Efectiva Semanal'),
]

TIPOS_VALIDOS = {c for c, _ in TIPOS_TASA}


def _pct_a_tanto(valor_pct: float) -> float:
    return float(valor_pct) / 100.0


def _tanto_a_pct(tanto: float) -> float:
    return float(tanto) * 100.0


def nominal_a_periodica(j_nominal_pct: float, m: int, anticipada: bool = False) -> float:
    """Nominal anual (en %) -> tasa periódica (tanto). Si anticipada, es ia."""
    if m <= 0:
        raise ValueError("m debe ser >= 1")
    j = _pct_a_tanto(j_nominal_pct)
    return j / m


def periodica_vencida_a_ea(i_per: float, m: int) -> float:
    return (1 + i_per) ** m - 1


def periodica_anticipada_a_ea(ia: float, m: int) -> float:
    if ia >= 1:
        raise ValueError("Tasa anticipada inválida (>=100%)")
    iv = ia / (1 - ia)  # vencida equivalente del periodo
    return (1 + iv) ** m - 1


def ea_a_periodica_vencida(ea_tanto: float, m: int) -> float:
    return (1 + ea_tanto) ** (1 / m) - 1


def ea_a_periodica_anticipada(ea_tanto: float, m: int) -> float:
    iv = ea_a_periodica_vencida(ea_tanto, m)
    return iv / (1 + iv)


def convertir_a_ea(valor_pct: float, tipo: str) -> float:
    """Cualquier tasa (en %) -> E.A. (en %, redondeada a 4 decimales)."""
    t = (tipo or '').upper().strip()
    if t not in TIPOS_VALIDOS:
        raise ValueError(f"Tipo de tasa inválido: {tipo}. Válidos: {sorted(TIPOS_VALIDOS)}")
    if valor_pct < 0 or valor_pct > 1000:
        raise ValueError("Tasa fuera de rango razonable (0-1000%)")

    v = float(valor_pct)
    if t == 'EA' or t == 'NAAV':
        return round(v, 4)
    if t == 'EM' or t == 'PMV':
        ea = periodica_vencida_a_ea(_pct_a_tanto(v), 12)
        return round(_tanto_a_pct(ea), 4)
    if t == 'PMA':
        ea = periodica_anticipada_a_ea(_pct_a_tanto(v), 12)
        return round(_tanto_a_pct(ea), 4)
    if t == 'ED':
        ea = periodica_vencida_a_ea(_pct_a_tanto(v), 365)
        return round(_tanto_a_pct(ea), 4)
    if t == 'ES':
        ea = periodica_vencida_a_ea(_pct_a_tanto(v), 52)
        return round(_tanto_a_pct(ea), 4)
    if t in M_POR_NOMINAL:
        m = M_POR_NOMINAL[t]
        anticipada = t.endswith('A') and t != 'NAAV'
        # NAAA es caso especial: nominal anticipado anual
        if t == 'NAAA':
            ea = periodica_anticipada_a_ea(_pct_a_tanto(v), 1)
            return round(_tanto_a_pct(ea), 4)
        i_per = nominal_a_periodica(v, m, anticipada=False)
        if anticipada:
            ea = periodica_anticipada_a_ea(i_per, m)
        else:
            ea = periodica_vencida_a_ea(i_per, m)
        return round(_tanto_a_pct(ea), 4)
    raise ValueError(f"Conversión no implementada para {t}")


def convertir_desde_ea(ea_pct: float, tipo_destino: str) -> float:
    """E.A. (en %) -> cualquier tasa (en %)."""
    t = (tipo_destino or '').upper().strip()
    if t not in TIPOS_VALIDOS:
        raise ValueError(f"Tipo destino inválido: {tipo_destino}")
    ea = _pct_a_tanto(float(ea_pct))
    if ea < 0:
        raise ValueError("EA no puede ser negativa")
    if t == 'EA' or t == 'NAAV':
        return round(float(ea_pct), 4)
    if t == 'EM' or t == 'PMV':
        return round(_tanto_a_pct(ea_a_periodica_vencida(ea, 12)), 4)
    if t == 'PMA':
        return round(_tanto_a_pct(ea_a_periodica_anticipada(ea, 12)), 4)
    if t == 'ED':
        return round(_tanto_a_pct(ea_a_periodica_vencida(ea, 365)), 4)
    if t == 'ES':
        return round(_tanto_a_pct(ea_a_periodica_vencida(ea, 52)), 4)
    if t in M_POR_NOMINAL:
        m = M_POR_NOMINAL[t]
        if t == 'NAAA':
            ia = ea_a_periodica_anticipada(ea, 1)
            return round(_tanto_a_pct(ia * 1), 4)
        anticipada = t.endswith('A') and t != 'NAAV'
        if anticipada:
            ia = ea_a_periodica_anticipada(ea, m)
            return round(_tanto_a_pct(ia * m), 4)
        iv = ea_a_periodica_vencida(ea, m)
        return round(_tanto_a_pct(iv * m), 4)
    raise ValueError(f"Conversión no implementada para {t}")


def tabla_tasas_desde_ea(ea_pct: float) -> dict:
    """Devuelve todas las equivalencias desde una EA. Clave para 'absolutamente todas'."""
    return {codigo: convertir_desde_ea(ea_pct, codigo) for codigo, _ in TIPOS_TASA}


def em_desde_ea(ea_pct: float) -> float:
    return convertir_desde_ea(ea_pct, 'EM')


def ea_desde_em(em_pct: float) -> float:
    return convertir_a_ea(em_pct, 'EM')


def cuota_fija(monto: int, em_pct: float, n: int) -> int:
    """Cuota fija Price con tasa EM. Retorna COP redondeado."""
    if monto <= 0 or n < 1:
        raise ValueError("Monto y n inválidos")
    i = _pct_a_tanto(float(em_pct))
    if i < 0:
        raise ValueError("Tasa negativa")
    if i == 0:
        return round(monto / n)
    r = monto * i / (1 - (1 + i) ** (-n))
    return round(r)


def generar_tabla_amortizacion(monto: int, em_pct: float, n: int) -> dict:
    """Tabla cuota fija. Retorna cuotas + totales. Todo en COP."""
    i = _pct_a_tanto(float(em_pct))
    cuota = cuota_fija(monto, em_pct, n)
    saldo = float(monto)
    filas = []
    total_intereses = 0
    for k in range(1, n + 1):
        interes = round(saldo * i) if i > 0 else 0
        if k == n:
            # última cuota ajusta redondeo
            abono = round(saldo)
            cuota_k = abono + interes
            saldo = 0
        else:
            abono = cuota - interes
            cuota_k = cuota
            saldo = round(saldo - abono)
        total_intereses += interes
        filas.append({
            'numero': k,
            'cuota': cuota_k,
            'interes': interes,
            'abono_capital': abono,
            'saldo': max(0, saldo),
        })
    return {
        'cuota_fija': cuota,
        'total_pagar': sum(f['cuota'] for f in filas),
        'total_intereses': total_intereses,
        'filas': filas,
    }


def tasa_gota_implicita(monto_prestado: int, monto_total_gota: int, dias_plazo: int) -> dict:
    """Convierte un 'gota' (100mil->120mil/7d) a tasas formales para comparar contra usura."""
    if monto_prestado <= 0 or monto_total_gota < monto_prestado or dias_plazo < 1:
        raise ValueError("Parámetros gota inválidos")
    i_periodo = (monto_total_gota / monto_prestado) - 1  # tanto en el plazo
    # llevar a EA: (1+i)^(365/dias)
    ea_tanto = (1 + i_periodo) ** (365 / dias_plazo) - 1
    ea_pct = _tanto_a_pct(ea_tanto)
    em_pct = convertir_desde_ea(min(ea_pct, 1e9), 'EM') if ea_pct < 1e9 else float('inf')
    ed_pct = _tanto_a_pct((1 + i_periodo) ** (1 / dias_plazo) - 1)
    return {
        'i_plazo_pct': round(i_periodo * 100, 2),
        'ed_pct': round(ed_pct, 4),
        'em_pct': round(em_pct, 4) if em_pct != float('inf') else None,
        'ea_pct': round(ea_pct, 2),
    }
