"""
Modelos Paga-Ya SIMULADOR EDUCATIVO (legal).

Ya NO se presta plata real ni se cobra con "reja".
- Prestamo/Cuota/Pago se conservan solo por compatibilidad histórica
  (demo antigua). El flujo nuevo es Simulacion (sin desembolso).
- Tasas formales colombianas: EM, EA, Nominal MV/MA/TV/TA/SV/SA/AV/AA,
  Periódica, Diaria/Semanal. Ver core/tasas.py.
"""
import secrets
from datetime import date, timedelta
from django.db import models
from django.contrib.auth.models import User

ROLES = (
    ('admin', 'Administrador'),
    ('prestador', 'Prestador'),
    ('cliente', 'Cliente'),
)

FRECUENCIAS = (
    ('DIARIO', 'Diario'),
    ('SEMANAL', 'Semanal'),
    ('QUINCENAL', 'Quincenal'),
    ('MENSUAL', 'Mensual'),
)

MODALIDADES = (
    ('TOTAL_PLAZO', 'Monto total en X días (ej: 100mil -> 120mil en 7 días)'),
    ('CUOTA_DIARIA', 'Cuota diaria fija por X días (ej: 5000 diarios por X días)'),
    ('PERIODICO', 'Cuota semanal / quincenal / mensual'),
)

# Días que suma cada frecuencia para generar vencimientos
DIAS_POR_FRECUENCIA = {
    'DIARIO': 1,
    'SEMANAL': 7,
    'QUINCENAL': 15,
    'MENSUAL': 30,
}


class RelojSistema(models.Model):
    """Fecha simulada del sistema (para el botón 'Saltar el día' del admin).

    Si fecha_simulada es NULL se usa la fecha real. Todo el cálculo de
    mora/vencimientos usa hoy() en vez de date.today().
    """
    id = models.IntegerField(primary_key=True, default=1)
    fecha_simulada = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Reloj: {self.fecha_simulada or 'fecha real'}"


def hoy():
    """Fecha 'actual' del sistema: simulada si el admin saltó días, real si no."""
    try:
        reloj = RelojSistema.objects.filter(pk=1).first()
        if reloj and reloj.fecha_simulada:
            return reloj.fecha_simulada
    except Exception:
        pass
    return date.today()


class Perfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    rol = models.CharField(max_length=20, choices=ROLES, default='cliente')
    telefono = models.CharField(max_length=30, blank=True)
    # Si es cliente: a qué prestador pertenece (1 prestador -> N clientes)
    prestador = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='clientes', help_text='Prestador dueño de este cliente'
    )
    # Si es prestador: código para armar su link de registro
    codigo_invite = models.CharField(max_length=20, unique=True, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} ({self.rol})"

    def save(self, *args, **kwargs):
        if self.rol == 'prestador' and not self.codigo_invite:
            self.codigo_invite = secrets.token_hex(4).upper()
        super().save(*args, **kwargs)


class Prestamo(models.Model):
    ESTADOS = (
        ('ACTIVO', 'Activo'),
        ('PAGADO', 'Pagado'),
        ('MORA', 'En mora'),
    )
    cliente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prestamos_como_cliente')
    prestador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prestamos_como_prestador')
    modalidad = models.CharField(max_length=20, choices=MODALIDADES, default='TOTAL_PLAZO')
    frecuencia = models.CharField(max_length=20, choices=FRECUENCIAS, default='DIARIO')
    monto_prestado = models.IntegerField(help_text='Capital entregado en COP')
    monto_total = models.IntegerField(help_text='Total a pagar (capital + ganancia fija, SIN interés compuesto)')
    num_cuotas = models.IntegerField()
    valor_cuota = models.IntegerField()
    fecha_inicio = models.DateField(default=hoy)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='ACTIVO')
    # DEPRECADO LEGAL: lógica "reja" eliminada (cobranza intimidante).
    # Campos conservados para no romper migraciones antiguas. No usar.
    reja_tumbada = models.BooleanField(default=False)
    fecha_reja = models.DateTimeField(null=True, blank=True)
    nota_reja = models.CharField(max_length=255, blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Préstamo #{self.id} {self.cliente.username} ${self.monto_prestado} -> ${self.monto_total}"

    @property
    def total_pagado(self):
        return sum(c.valor_pagado for c in self.cuotas.all())

    @property
    def saldo_plata(self):
        return max(0, self.monto_total - self.total_pagado)

    def cuotas_vencidas(self):
        fecha = hoy()
        return [c for c in self.cuotas.all()
                if c.estado != 'PAGADA' and c.fecha_vencimiento < fecha]

    @property
    def dias_mora(self):
        """Días en mora = días desde el vencimiento más antiguo sin pagar."""
        vencidas = self.cuotas_vencidas()
        if not vencidas:
            return 0
        mas_antigua = min(c.fecha_vencimiento for c in vencidas)
        return max(0, (hoy() - mas_antigua).days)

    def actualizar_estado(self):
        """Marca cuotas vencidas y estado del préstamo. Se llama en cada lectura."""
        from django.utils import timezone
        fecha = hoy()
        changed = False
        for c in self.cuotas.all():
            if c.estado != 'PAGADA' and c.fecha_vencimiento < fecha and c.estado != 'VENCIDA':
                c.estado = 'VENCIDA'
                c.save()
                changed = True
        cuotas = list(self.cuotas.all())
        if cuotas and all(c.estado == 'PAGADA' for c in cuotas):
            if self.estado != 'PAGADO':
                self.estado = 'PAGADO'
                self.save()
        elif self.cuotas_vencidas():
            if self.estado != 'MORA':
                self.estado = 'MORA'
                self.save()
        elif self.estado == 'MORA' and not self.cuotas_vencidas():
            self.estado = 'ACTIVO'
            self.save()
        return changed


class Cuota(models.Model):
    ESTADOS = (
        ('PENDIENTE', 'Pendiente'),
        ('PARCIAL', 'Abono parcial'),
        ('VENCIDA', 'Vencida'),
        ('PAGADA', 'Pagada'),
    )
    prestamo = models.ForeignKey(Prestamo, on_delete=models.CASCADE, related_name='cuotas')
    numero = models.IntegerField()
    fecha_vencimiento = models.DateField()
    valor = models.IntegerField()
    valor_pagado = models.IntegerField(default=0)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    fecha_pago = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['numero']
        unique_together = ('prestamo', 'numero')

    def __str__(self):
        return f"Cuota {self.numero} préstamo #{self.prestamo_id} ${self.valor}"

    @property
    def saldo(self):
        return max(0, self.valor - self.valor_pagado)


class Pago(models.Model):
    """Pago SIMULADO (pasarela real se integra después)."""
    prestamo = models.ForeignKey(Prestamo, on_delete=models.CASCADE, related_name='pagos')
    cuota = models.ForeignKey(Cuota, on_delete=models.SET_NULL, null=True, blank=True, related_name='pagos')
    cliente = models.ForeignKey(User, on_delete=models.CASCADE)
    valor = models.IntegerField()
    fecha = models.DateTimeField(auto_now_add=True)
    metodo = models.CharField(max_length=30, default='SIMULADO')
    referencia = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"Pago ${self.valor} préstamo #{self.prestamo_id}"


class TasaUsura(models.Model):
    """Tope legal Superfinanciera. Escalable: una fila por vigencia mensual."""

    vigencia = models.CharField(max_length=7, unique=True, help_text='YYYY-MM')
    ea_max_pct = models.FloatField(help_text='Usura E.A. en %, ej 39.65')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-vigencia']

    def __str__(self):
        return f"Usura {self.vigencia}: {self.ea_max_pct}% EA"

    @property
    def em_max_pct(self):
        from .tasas import convertir_desde_ea
        try:
            return convertir_desde_ea(self.ea_max_pct, 'EM')
        except Exception:
            return None


class Simulacion(models.Model):
    """Simulación educativa SIN desembolso. Producto principal del simulador."""

    FRECS_SIM = (
        ('MENSUAL', 'Mensual'),
        ('QUINCENAL', 'Quincenal'),
        ('SEMANAL', 'Semanal'),
        ('DIARIA', 'Diaria (solo pedagógica)'),
    )
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='simulaciones')
    monto = models.IntegerField(help_text='Monto simulado en COP')
    tasa_valor_pct = models.FloatField(help_text='Tasa ingresada en %')
    tasa_tipo = models.CharField(max_length=10, default='EM')
    n_cuotas = models.IntegerField()
    frecuencia = models.CharField(max_length=20, choices=FRECS_SIM, default='MENSUAL')
    em_equiv_pct = models.FloatField()
    ea_equiv_pct = models.FloatField()
    cuota_valor = models.IntegerField()
    total_pagar = models.IntegerField()
    total_intereses = models.IntegerField()
    es_usura = models.BooleanField(default=False)
    tabla_json = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return f"Sim #{self.id} ${self.monto} {self.tasa_valor_pct}% {self.tasa_tipo}"
