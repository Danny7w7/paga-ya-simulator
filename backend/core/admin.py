from django.contrib import admin
from .models import Perfil, Prestamo, Cuota, Pago, RelojSistema, TasaUsura, Simulacion

admin.site.register(Perfil)
admin.site.register(Prestamo)
admin.site.register(Cuota)
admin.site.register(Pago)
admin.site.register(RelojSistema)
admin.site.register(TasaUsura)
admin.site.register(Simulacion)
