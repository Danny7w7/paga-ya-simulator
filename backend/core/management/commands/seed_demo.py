"""
Datos demo SIMULADOR EDUCATIVO (legal, sin reja, sin préstamo real nuevo).

Uso:
    python manage.py seed_demo

Crea:
  - 1 admin, 2 prestadores (ahora rol educativo), 4 clientes
  - TasaUsura vigente educativa
  - Préstamos históricos solo para comparar (sin reja)
"""
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import Perfil, Prestamo, Cuota, TasaUsura, hoy
from core.utils import preview_plan, generar_vencimientos, aplicar_pago_fifo


def crear_usuario(username, password, rol, nombre='', telefono='', prestador=None,
                  staff=False, superuser=False):
    user, created = User.objects.get_or_create(
        username=username, defaults={'first_name': nombre})
    user.first_name = nombre
    user.is_staff = staff
    user.is_superuser = superuser
    user.set_password(password)
    user.save()
    perfil, _ = Perfil.objects.get_or_create(user=user)
    perfil.rol = rol
    perfil.telefono = telefono
    perfil.prestador = prestador
    perfil.save()  # genera codigo_invite si es prestador
    return user


def crear_prestamo(cliente, prestador, modalidad, frecuencia,
                   monto_prestado, monto_total, num_cuotas, inicio_offset_dias=0):
    plan = preview_plan(monto_prestado, monto_total, num_cuotas, frecuencia)
    fecha_inicio = hoy() + timedelta(days=inicio_offset_dias)
    p = Prestamo.objects.create(
        cliente=cliente, prestador=prestador, modalidad=modalidad,
        frecuencia=frecuencia, monto_prestado=monto_prestado,
        monto_total=monto_total, num_cuotas=num_cuotas,
        valor_cuota=plan['valor_cuota'], fecha_inicio=fecha_inicio,
    )
    for i, venc in enumerate(
            generar_vencimientos(fecha_inicio, num_cuotas, frecuencia), start=1):
        Cuota.objects.create(prestamo=p, numero=i,
                             fecha_vencimiento=venc, valor=plan['valor_cuota'])
    diff = monto_total - plan['valor_cuota'] * num_cuotas
    if diff:
        last = p.cuotas.order_by('-numero').first()
        last.valor += diff
        last.save()
    p.actualizar_estado()
    return p


class Command(BaseCommand):
    help = 'Pobla la base con usuarios y préstamos de demostración'

    def handle(self, *args, **options):
        self.stdout.write('--- Poblando Paga-Ya SIMULADOR (legal) ---')

        TasaUsura.objects.get_or_create(
            vigencia='2026-09', defaults={'ea_max_pct': 39.65})
        self.stdout.write('Usura educativa 2026-09: 39.65% EA (actualizable por admin).')

        admin = crear_usuario('admin', 'admin123', 'admin',
                              nombre='Administrador', staff=True, superuser=True)
        chepe = crear_usuario('don_chepe', 'chepe123', 'prestador',
                              nombre='Don Chepe', telefono='3001112233')
        patrona = crear_usuario('la_patrona', 'patrona123', 'prestador',
                                nombre='La Patrona', telefono='3004445566')
        carlos = crear_usuario('carlos', 'cliente123', 'cliente',
                               nombre='Carlos R.', telefono='3011111111',
                               prestador=chepe)
        maria = crear_usuario('maria', 'cliente123', 'cliente',
                              nombre='María L.', telefono='3012222222',
                              prestador=chepe)
        juan = crear_usuario('juan', 'cliente123', 'cliente',
                             nombre='Juan P.', telefono='3023333333',
                             prestador=patrona)
        lucia = crear_usuario('lucia', 'cliente123', 'cliente',
                              nombre='Lucía F.', telefono='3024444444',
                              prestador=patrona)

        if Prestamo.objects.exists():
            self.stdout.write('Ya hay préstamos históricos, no se crean duplicados.')
        else:
            # 1) Histórico al día con abono: 100mil -> 120mil en 7 días (SOLO para comparar usura)
            p1 = crear_prestamo(carlos, chepe, 'TOTAL_PLAZO', 'DIARIO',
                                100000, 120000, 7, inicio_offset_dias=0)
            aplicar_pago_fifo(p1, p1.valor_cuota)

            # 2) Histórico en MORA pedagógica (SIN reja): 5000 diarios x 24 días
            p2 = crear_prestamo(maria, chepe, 'CUOTA_DIARIA', 'DIARIO',
                                100000, 5000 * 24, 24, inicio_offset_dias=-20)
            aplicar_pago_fifo(p2, 15000)
            # SIN reja_tumbada: eliminado por legalidad
            p2.actualizar_estado()

            # 3) Semanal al día: 500mil -> 600mil en 4 semanas
            crear_prestamo(juan, patrona, 'PERIODICO', 'SEMANAL',
                           500000, 600000, 4, inicio_offset_dias=0)

            # 4) Quincenal PAGADO: 300mil -> 360mil en 2 quincenas
            p4 = crear_prestamo(lucia, patrona, 'PERIODICO', 'QUINCENAL',
                                300000, 360000, 2, inicio_offset_dias=-40)
            aplicar_pago_fifo(p4, 360000)

            self.stdout.write('4 préstamos históricos creados (solo comparativa educativa, sin reja).')

        chepe.perfil.refresh_from_db()
        patrona.perfil.refresh_from_db()
        self.stdout.write(self.style.SUCCESS(
            '\nListo. Credenciales demo:\n'
            '  admin / admin123  (administrador)\n'
            '  don_chepe / chepe123  (prestador)\n'
            '  la_patrona / patrona123  (prestadora)\n'
            '  carlos - maria - juan - lucia / cliente123  (clientes)\n'
            f'  Link don_chepe:  http://localhost:5173/register?code={chepe.perfil.codigo_invite}\n'
            f'  Link la_patrona: http://localhost:5173/register?code={patrona.perfil.codigo_invite}\n'
        ))
