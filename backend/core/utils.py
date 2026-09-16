"""Lógica de cálculo SIN interés compuesto + reparto de pagos FIFO."""
import secrets
from datetime import timedelta
from .models import DIAS_POR_FRECUENCIA, hoy


def preview_plan(monto_prestado: int, monto_total: int, num_cuotas: int, frecuencia: str):
    """Devuelve valor_cuota y plazo estimado. Todo lineal, sin capitalización."""
    if monto_total < monto_prestado:
        raise ValueError("El monto total no puede ser menor al prestado.")
    if num_cuotas < 1:
        raise ValueError("num_cuotas debe ser >= 1.")
    if frecuencia not in DIAS_POR_FRECUENCIA:
        raise ValueError("Frecuencia inválida.")
    valor_cuota = round(monto_total / num_cuotas)
    plazo_dias = num_cuotas * DIAS_POR_FRECUENCIA[frecuencia]
    ganancia = monto_total - monto_prestado
    return {
        "monto_prestado": monto_prestado,
        "monto_total": monto_total,
        "ganancia_fija": ganancia,
        "num_cuotas": num_cuotas,
        "valor_cuota": valor_cuota,
        "frecuencia": frecuencia,
        "plazo_dias_aprox": plazo_dias,
        "interes_compuesto": False,
    }


def generar_vencimientos(fecha_inicio, num_cuotas: int, frecuencia: str):
    paso = DIAS_POR_FRECUENCIA[frecuencia]
    return [fecha_inicio + timedelta(days=paso * i) for i in range(1, num_cuotas + 1)]


def aplicar_pago_fifo(prestamo, valor: int, metodo="SIMULADO"):
    """Reparte un pago a las cuotas más antiguas pendientes. Retorna lista de (cuota, aplicado)."""
    from .models import Pago, Cuota
    if valor <= 0:
        raise ValueError("El valor debe ser mayor a 0.")
    restante = valor
    aplicadas = []
    cuotas = prestamo.cuotas.filter(estado__in=['PENDIENTE', 'PARCIAL', 'VENCIDA']).order_by('numero')
    for c in cuotas:
        if restante <= 0:
            break
        falta = c.valor - c.valor_pagado
        if falta <= 0:
            continue
        aplica = min(falta, restante)
        c.valor_pagado += aplica
        restante -= aplica
        if c.valor_pagado >= c.valor:
            c.estado = 'PAGADA'
            c.fecha_pago = hoy()
        else:
            c.estado = c.estado if c.estado == 'VENCIDA' else 'PARCIAL'
        c.save()
        Pago.objects.create(
            prestamo=prestamo, cuota=c, cliente=prestamo.cliente,
            valor=aplica, metodo=metodo,
            referencia='SIM-' + secrets.token_hex(4).upper(),
        )
        aplicadas.append((c.numero, aplica))
    prestamo.actualizar_estado()
    return aplicadas, restante
