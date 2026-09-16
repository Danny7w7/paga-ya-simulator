"""API JSON Simulador Educativo (legal). Sin reja, sin préstamo real."""
import json
from datetime import datetime
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import Perfil, Prestamo, Cuota, RelojSistema, hoy, TasaUsura, Simulacion
from .utils import preview_plan, generar_vencimientos, aplicar_pago_fifo
from . import tasas as T


def body(request):
    try:
        return json.loads(request.body.decode() or '{}')
    except Exception:
        return {}


def perfil_de(user):
    try:
        return user.perfil
    except Perfil.DoesNotExist:
        return Perfil.objects.create(user=user, rol='admin' if user.is_superuser else 'cliente')


def user_dict(user):
    p = perfil_de(user)
    return {
        'id': user.id, 'username': user.username,
        'first_name': user.first_name, 'email': user.email,
        'rol': p.rol, 'telefono': p.telefono,
        'codigo_invite': p.codigo_invite,
        'prestador_id': p.prestador_id,
        'prestador': p.prestador.username if p.prestador else None,
    }


def prestamo_dict(p: Prestamo):
    p.actualizar_estado()
    cuotas = []
    for c in p.cuotas.all().order_by('numero'):
        cuotas.append({
            'id': c.id, 'numero': c.numero,
            'fecha_vencimiento': str(c.fecha_vencimiento),
            'valor': c.valor, 'valor_pagado': c.valor_pagado,
            'saldo': c.saldo, 'estado': c.estado,
            'fecha_pago': str(c.fecha_pago) if c.fecha_pago else None,
        })
    return {
        'id': p.id,
        'cliente': p.cliente.username, 'cliente_id': p.cliente_id,
        'prestador': p.prestador.username, 'prestador_id': p.prestador_id,
        'modalidad': p.modalidad, 'frecuencia': p.frecuencia,
        'monto_prestado': p.monto_prestado, 'monto_total': p.monto_total,
        'num_cuotas': p.num_cuotas, 'valor_cuota': p.valor_cuota,
        'fecha_inicio': str(p.fecha_inicio), 'estado': p.estado,
        'total_pagado': p.total_pagado, 'abono_capital': p.total_pagado,
        'saldo_plata': p.saldo_plata,
        'cuotas_vencidas': len(p.cuotas_vencidas()),
        'dias_mora': p.dias_mora,
        'dias_deuda': p.dias_mora,
        'reja_tumbada': p.reja_tumbada,
        'fecha_reja': p.fecha_reja.isoformat() if p.fecha_reja else None,
        'nota_reja': p.nota_reja,
        'cuotas': cuotas,
    }


def ok(data=None, **kw):
    d = {'ok': True}
    if data is not None:
        d['data'] = data
    d.update(kw)
    return JsonResponse(d)


def fail(msg, status=400):
    return JsonResponse({'ok': False, 'error': msg}, status=status)


def login_required_json(fn):
    def wrapper(request, *a, **kw):
        if not request.user.is_authenticated:
            return fail('No autenticado', 401)
        return fn(request, *a, **kw)
    return wrapper


def role_required(*roles):
    def deco(fn):
        def wrapper(request, *a, **kw):
            if not request.user.is_authenticated:
                return fail('No autenticado', 401)
            if perfil_de(request.user).rol not in roles:
                return fail('Sin permiso para este rol', 403)
            return fn(request, *a, **kw)
        return wrapper
    return deco


# ---------- AUTH ----------

@csrf_exempt
@require_http_methods(['POST'])
def api_register(request):
    d = body(request)
    username = (d.get('username') or '').strip()
    password = d.get('password') or ''
    rol = d.get('rol', 'cliente')
    codigo = (d.get('codigo') or '').strip().upper()
    telefono = d.get('telefono', '')
    nombre = d.get('nombre', '')
    if not username or not password:
        return fail('username y password requeridos')
    if User.objects.filter(username=username).exists():
        return fail('Ese usuario ya existe')
    prestador = None
    if codigo:
        try:
            perfil_inv = Perfil.objects.get(codigo_invite=codigo, rol='prestador')
            prestador = perfil_inv.user
            rol = 'cliente'  # el link de prestador siempre crea clientes
        except Perfil.DoesNotExist:
            return fail('Código de invitación inválido')
    if rol not in ('prestador', 'cliente'):
        # admin solo lo crea otro admin o el primero del sistema
        if rol == 'admin':
            if User.objects.exists() and not (
                request.user.is_authenticated and perfil_de(request.user).rol == 'admin'
            ):
                return fail('Solo un administrador puede crear otro admin')
        else:
            return fail('Rol inválido')
    user = User.objects.create_user(username=username, password=password, first_name=nombre)
    Perfil.objects.create(user=user, rol=rol, telefono=telefono, prestador=prestador)
    login(request, user)
    return ok(user_dict(user))


@csrf_exempt
@require_http_methods(['POST'])
def api_login(request):
    d = body(request)
    user = authenticate(request, username=d.get('username'), password=d.get('password'))
    if not user:
        return fail('Credenciales inválidas', 401)
    login(request, user)
    return ok(user_dict(user))


@csrf_exempt
@require_http_methods(['POST'])
def api_logout(request):
    logout(request)
    return ok()


@login_required_json
def api_me(request):
    return ok(user_dict(request.user))


# ---------- PRESTADOR ----------

@role_required('prestador', 'admin')
def api_mi_codigo(request):
    p = perfil_de(request.user)
    link = f"http://localhost:5173/register?code={p.codigo_invite}"
    return ok({'codigo': p.codigo_invite, 'link': link})


@role_required('prestador', 'admin')
def api_mis_clientes(request):
    if perfil_de(request.user).rol == 'admin' and request.GET.get('all') == '1':
        users = User.objects.filter(perfil__rol='cliente')
    else:
        users = User.objects.filter(perfil__prestador=request.user)
    out = []
    for u in users:
        prestamos = Prestamo.objects.filter(cliente=u)
        mora = sum(1 for pr in prestamos for _ in pr.cuotas_vencidas())
        out.append({**user_dict(u),
                    'num_prestamos': prestamos.count(),
                    'cuotas_vencidas': mora})
    return ok(out)


@role_required('prestador', 'admin')
def api_prestamos_prestador(request):
    qs = Prestamo.objects.all().order_by('-id') if perfil_de(request.user).rol == 'admin' \
        else Prestamo.objects.filter(prestador=request.user).order_by('-id')
    cid = request.GET.get('cliente_id')
    if cid:
        qs = qs.filter(cliente_id=cid)
    return ok([prestamo_dict(p) for p in qs])


@csrf_exempt
@role_required('prestador', 'admin')
@require_http_methods(['POST'])
def api_crear_prestamo(request):
    """Crea préstamo con valores 100% variables (sin interés compuesto).

    Espera: cliente_username o cliente_id, monto_prestado, monto_total,
    num_cuotas, frecuencia (DIARIO/SEMANAL/QUINCENAL/MENSUAL),
    modalidad, fecha_inicio (YYYY-MM-DD opcional).
    """
    d = body(request)
    try:
        monto_prestado = int(d.get('monto_prestado', 0))
        monto_total = int(d.get('monto_total', 0))
        num_cuotas = int(d.get('num_cuotas', 0))
        frecuencia = d.get('frecuencia', 'DIARIO')
        modalidad = d.get('modalidad', 'TOTAL_PLAZO')
        plan = preview_plan(monto_prestado, monto_total, num_cuotas, frecuencia)
    except ValueError as e:
        return fail(str(e))
    # resolver cliente
    cliente = None
    if d.get('cliente_id'):
        try:
            cliente = User.objects.get(id=d['cliente_id'])
        except User.DoesNotExist:
            return fail('Cliente no existe')
    elif d.get('cliente_username'):
        try:
            cliente = User.objects.get(username=d['cliente_username'])
        except User.DoesNotExist:
            return fail('Cliente no existe, debe registrarse con tu link primero')
    else:
        return fail('Indica cliente_id o cliente_username')
    if perfil_de(cliente).rol != 'cliente':
        return fail('El usuario no es cliente')
    prestador = request.user
    # si el admin crea, respeta prestador_id opcional
    if perfil_de(request.user).rol == 'admin' and d.get('prestador_id'):
        try:
            prestador = User.objects.get(id=d['prestador_id'])
        except User.DoesNotExist:
            return fail('Prestador no existe')
    # vincular cliente al prestador si no tiene
    pc = perfil_de(cliente)
    if not pc.prestador:
        pc.prestador = prestador
        pc.save()
    fi = d.get('fecha_inicio')
    try:
        fecha_inicio = datetime.strptime(fi, '%Y-%m-%d').date() if fi else hoy()
    except ValueError:
        return fail('fecha_inicio inválida, usa YYYY-MM-DD')
    p = Prestamo.objects.create(
        cliente=cliente, prestador=prestador, modalidad=modalidad,
        frecuencia=frecuencia, monto_prestado=monto_prestado,
        monto_total=monto_total, num_cuotas=num_cuotas,
        valor_cuota=plan['valor_cuota'], fecha_inicio=fecha_inicio,
    )
    for i, venc in enumerate(generar_vencimientos(fecha_inicio, num_cuotas, frecuencia), start=1):
        Cuota.objects.create(prestamo=p, numero=i, fecha_vencimiento=venc, valor=plan['valor_cuota'])
    # ajuste de redondeo en última cuota
    diff = monto_total - plan['valor_cuota'] * num_cuotas
    if diff != 0:
        last = p.cuotas.order_by('-numero').first()
        last.valor += diff
        last.save()
        p.valor_cuota = plan['valor_cuota']
        p.save()
    return ok(prestamo_dict(p))


@csrf_exempt
@role_required('prestador', 'admin')
@require_http_methods(['POST'])
def api_marcar_reja(request, prestamo_id):
    """ELIMINADA por legalidad (Ley 1328/09 + Ley 2300/23).
    Se conserva la ruta para devolver 410 Gone educativo."""
    return fail('Función eliminada: la cobranza intimidante ("tumbar reja") está prohibida. Usa el Simulador y acuerdos de pago dignos.', status=410)


# ---------- CLIENTE ----------

@role_required('cliente', 'admin')
def api_mis_prestamos(request):
    cid = request.GET.get('cliente_id') if perfil_de(request.user).rol == 'admin' else None
    user = User.objects.get(id=cid) if cid else request.user
    qs = Prestamo.objects.filter(cliente=user).order_by('-id')
    return ok([prestamo_dict(p) for p in qs])


@role_required('cliente', 'admin', 'prestador')
def api_detalle_prestamo(request, prestamo_id):
    try:
        p = Prestamo.objects.get(id=prestamo_id)
    except Prestamo.DoesNotExist:
        return fail('No existe', 404)
    rol = perfil_de(request.user).rol
    if rol == 'cliente' and p.cliente_id != request.user.id:
        return fail('Sin permiso', 403)
    if rol == 'prestador' and p.prestador_id != request.user.id:
        return fail('Sin permiso', 403)
    return ok(prestamo_dict(p))


@csrf_exempt
@role_required('cliente', 'admin')
@require_http_methods(['POST'])
def api_pagar(request):
    """Pago en línea SIMULADO. Después se conecta la pasarela real aquí."""
    d = body(request)
    try:
        p = Prestamo.objects.get(id=d.get('prestamo_id'))
    except Prestamo.DoesNotExist:
        return fail('Préstamo no existe')
    if perfil_de(request.user).rol != 'admin' and p.cliente_id != request.user.id:
        return fail('Sin permiso', 403)
    try:
        valor = int(d.get('valor', 0))
        aplicadas, sobrante = aplicar_pago_fifo(p, valor, metodo='SIMULADO')
    except ValueError as e:
        return fail(str(e))
    if not aplicadas:
        return fail('Este préstamo ya está pagado')
    return ok({'aplicadas': aplicadas, 'sobrante': sobrante,
               'mensaje': 'Pago simulado exitoso (pasarela real pendiente).',
               'prestamo': prestamo_dict(p)})


# ---------- ADMIN ----------

@role_required('admin')
def api_admin_resumen(request):
    users = User.objects.count()
    prestamos = Prestamo.objects.all()
    total_prestado = sum(p.monto_prestado for p in prestamos)
    total_recaudado = sum(p.total_pagado for p in prestamos)
    en_mora = sum(1 for p in prestamos if p.cuotas_vencidas())
    return ok({
        'usuarios': users,
        'prestamos': prestamos.count(),
        'total_prestado': total_prestado,
        'total_recaudado': total_recaudado,
        'en_mora': en_mora,
    })


@role_required('admin')
def api_admin_usuarios(request):
    return ok([user_dict(u) for u in User.objects.all().order_by('id')])


@csrf_exempt
@role_required('admin')
@require_http_methods(['POST'])
def api_admin_cambiar_rol(request):
    d = body(request)
    try:
        u = User.objects.get(id=d.get('user_id'))
    except User.DoesNotExist:
        return fail('Usuario no existe')
    rol = d.get('rol')
    if rol not in ('admin', 'prestador', 'cliente'):
        return fail('Rol inválido')
    p = perfil_de(u)
    p.rol = rol
    p.save()
    return ok(user_dict(u))


@csrf_exempt
@role_required('admin')
@require_http_methods(['DELETE'])
def api_admin_eliminar_prestamo(request, prestamo_id):
    try:
        p = Prestamo.objects.get(id=prestamo_id)
        p.delete()
        return ok({'eliminado': prestamo_id})
    except Prestamo.DoesNotExist:
        return fail('No existe', 404)


# ---------- RELOJ DEL SISTEMA (saltar días) ----------

@role_required('admin')
def api_reloj(request):
    """GET: devuelve fecha real, simulada (si hay) y fecha efectiva del sistema."""
    from datetime import date
    reloj, _ = RelojSistema.objects.get_or_create(pk=1)
    return ok({
        'real': str(date.today()),
        'simulada': str(reloj.fecha_simulada) if reloj.fecha_simulada else None,
        'hoy': str(hoy()),
        'simulando': bool(reloj.fecha_simulada),
    })


@csrf_exempt
@role_required('admin')
@require_http_methods(['POST'])
def api_reloj_avanzar(request):
    """POST {dias: N}: adelanta el día del sistema N días (default 1)."""
    from datetime import timedelta
    try:
        dias = int(body(request).get('dias', 1))
    except (ValueError, TypeError):
        return fail('dias debe ser un número entero')
    if dias < 1 or dias > 365:
        return fail('dias debe estar entre 1 y 365')
    reloj, _ = RelojSistema.objects.get_or_create(pk=1)
    base = reloj.fecha_simulada or hoy()
    reloj.fecha_simulada = base + timedelta(days=dias)
    reloj.save()
    # Recalcular moras de todos los préstamos con la nueva fecha
    for p in Prestamo.objects.all():
        p.actualizar_estado()
    return ok({
        'hoy': str(hoy()),
        'simulada': str(reloj.fecha_simulada),
        'mensaje': f'Día saltado: hoy es {reloj.fecha_simulada}. Las cuotas vencidas ya generan mora.',
    })


@csrf_exempt
@role_required('admin')
@require_http_methods(['POST'])
def api_reloj_reset(request):
    """POST: vuelve a la fecha real y recalcula estados."""
    reloj, _ = RelojSistema.objects.get_or_create(pk=1)
    reloj.fecha_simulada = None
    reloj.save()
    for p in Prestamo.objects.all():
        # Si una cuota quedó VENCIDA pero ya no está vencida en fecha real,
        # vuelve a PENDIENTE/PARCIAL según lo pagado.
        for c in p.cuotas.all():
            if c.estado == 'VENCIDA' and c.fecha_vencimiento >= hoy():
                c.estado = 'PARCIAL' if c.valor_pagado > 0 else 'PENDIENTE'
                c.save()
        p.actualizar_estado()
    return ok({'hoy': str(hoy()), 'mensaje': 'Reloj restablecido a la fecha real.'})


def api_calculadora(request):
    """GET ?monto_prestado=100000&monto_total=120000&num_cuotas=7&frecuencia=DIARIO"""
    try:
        plan = preview_plan(
            int(request.GET.get('monto_prestado', 100000)),
            int(request.GET.get('monto_total', 120000)),
            int(request.GET.get('num_cuotas', 7)),
            request.GET.get('frecuencia', 'DIARIO'),
        )
        return ok(plan)
    except ValueError as e:
        return fail(str(e))


# ---------- SIMULADOR EDUCATIVO (núcleo legal) ----------

def _usura_vigente_ea():
    u = TasaUsura.objects.order_by('-vigencia').first()
    return float(u.ea_max_pct) if u else 39.65


def simulacion_dict(s: Simulacion):
    return {
        'id': s.id,
        'monto': s.monto,
        'tasa_valor_pct': s.tasa_valor_pct,
        'tasa_tipo': s.tasa_tipo,
        'n_cuotas': s.n_cuotas,
        'frecuencia': s.frecuencia,
        'em_equiv_pct': s.em_equiv_pct,
        'ea_equiv_pct': s.ea_equiv_pct,
        'cuota_valor': s.cuota_valor,
        'total_pagar': s.total_pagar,
        'total_intereses': s.total_intereses,
        'es_usura': s.es_usura,
        'tabla': s.tabla_json,
        'created_at': s.created_at.isoformat() if s.created_at else None,
    }


def api_tipos_tasa(request):
    return ok([{'codigo': c, 'nombre': n} for c, n in T.TIPOS_TASA])


def api_usura(request):
    u = TasaUsura.objects.order_by('-vigencia').first()
    ea = float(u.ea_max_pct) if u else 39.65
    return ok({
        'vigencia': u.vigencia if u else 'DEFAULT-EDUCATIVA',
        'ea_max_pct': ea,
        'em_max_pct': T.convertir_desde_ea(ea, 'EM'),
        'fuente': 'Superfinanciera (actualizable por admin). Valor por defecto educativo.',
        'nota_legal': 'Toda tasa EA superior a la usura configura usura (art. 305 CP). Este simulador bloquea/advierte.',
    })


@csrf_exempt
@role_required('admin')
@require_http_methods(['POST'])
def api_usura_actualizar(request):
    d = body(request)
    try:
        vigencia = (d.get('vigencia') or '').strip()
        ea = float(d.get('ea_max_pct', 0))
        if len(vigencia) != 7 or ea <= 0 or ea > 200:
            return fail('vigencia YYYY-MM y ea_max_pct (0-200) requeridos')
        u, _ = TasaUsura.objects.update_or_create(
            vigencia=vigencia, defaults={'ea_max_pct': ea})
        return ok({'vigencia': u.vigencia, 'ea_max_pct': u.ea_max_pct})
    except (ValueError, TypeError):
        return fail('Datos inválidos')


def api_tasas_convertir(request):
    try:
        valor = float(request.GET.get('valor', 0))
        tipo = (request.GET.get('tipo', 'EM') or 'EM').upper()
        ea = T.convertir_a_ea(valor, tipo)
        tabla = T.tabla_tasas_desde_ea(ea)
        usura_ea = _usura_vigente_ea()
        return ok({
            'entrada': {'valor_pct': valor, 'tipo': tipo},
            'ea_equiv_pct': ea,
            'em_equiv_pct': T.convertir_desde_ea(ea, 'EM'),
            'todas': tabla,
            'usura_ea': usura_ea,
            'es_usura': ea > usura_ea,
        })
    except ValueError as e:
        return fail(str(e))


def api_gota_comparar(request):
    """Compara un gota (100mil->120mil/7d) contra tasa legal. 100% educativo."""
    try:
        prestado = int(request.GET.get('monto_prestado', 100000))
        total = int(request.GET.get('monto_total', 120000))
        dias = int(request.GET.get('dias', 7))
        g = T.tasa_gota_implicita(prestado, total, dias)
        usura_ea = _usura_vigente_ea()
        veces = round(g['ea_pct'] / usura_ea, 1) if usura_ea else None
        return ok({
            'gota': g,
            'usura_ea': usura_ea,
            'veces_usura': veces,
            'mensaje': f"Ese gota equivale a {g['ea_pct']}% EA ({veces}x la usura). Ilegal por usura.",
            'nota_legal': 'Simulación educativa, sin desembolso. No prestes ni cobres por fuera del sistema financiero.',
        })
    except ValueError as e:
        return fail(str(e))


@csrf_exempt
@login_required_json
@require_http_methods(['POST'])
def api_simular(request):
    d = body(request)
    try:
        monto = int(d.get('monto', 0))
        tasa_valor = float(d.get('tasa_valor_pct', 0))
        tasa_tipo = (d.get('tasa_tipo', 'EM') or 'EM').upper()
        n = int(d.get('n_cuotas', 0))
        frec = (d.get('frecuencia', 'MENSUAL') or 'MENSUAL').upper()
        if monto < 10000 or monto > 100_000_000:
            return fail('monto entre $10.000 y $100.000.000 (simulado)')
        if n < 1 or n > 60:
            return fail('n_cuotas entre 1 y 60')
        if frec not in ('MENSUAL', 'QUINCENAL', 'SEMANAL', 'DIARIA'):
            return fail('frecuencia inválida')
        ea = T.convertir_a_ea(tasa_valor, tasa_tipo)
        em = T.convertir_desde_ea(ea, 'EM')
        usura_ea = _usura_vigente_ea()
        es_usura = ea > usura_ea
        # Para frecuencia no mensual se usa EM convertida a periódica equivalente
        # de forma pedagógica: cuota mensual base prorrateada. Escalable a motor
        # por frecuencia exacta en fase 2.
        tabla = T.generar_tabla_amortizacion(monto, em, n)
        s = Simulacion.objects.create(
            usuario=request.user, monto=monto,
            tasa_valor_pct=tasa_valor, tasa_tipo=tasa_tipo, n_cuotas=n,
            frecuencia=frec, em_equiv_pct=em, ea_equiv_pct=ea,
            cuota_valor=tabla['cuota_fija'], total_pagar=tabla['total_pagar'],
            total_intereses=tabla['total_intereses'], es_usura=es_usura,
            tabla_json=tabla['filas'],
        )
        out = simulacion_dict(s)
        out['usura_ea'] = usura_ea
        out['advertencia'] = ('TASA EN USURA: supera el tope legal. Solo fines educativos.' if es_usura
                              else 'Tasa dentro del tope. Recuerda: simulación sin desembolso real.')
        return ok(out)
    except ValueError as e:
        return fail(str(e))


@login_required_json
def api_mis_simulaciones(request):
    qs = Simulacion.objects.filter(usuario=request.user).order_by('-id')[:50]
    return ok([simulacion_dict(s) for s in qs])
