from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.api_register),
    path('login/', views.api_login),
    path('logout/', views.api_logout),
    path('me/', views.api_me),

    path('mi-codigo/', views.api_mi_codigo),
    path('prestador/clientes/', views.api_mis_clientes),
    path('prestador/prestamos/', views.api_prestamos_prestador),
    path('prestador/prestamos/crear/', views.api_crear_prestamo),
    path('prestador/reja/<int:prestamo_id>/', views.api_marcar_reja),

    path('cliente/mis-prestamos/', views.api_mis_prestamos),
    path('cliente/prestamo/<int:prestamo_id>/', views.api_detalle_prestamo),
    path('cliente/pagar/', views.api_pagar),

    path('admin/resumen/', views.api_admin_resumen),
    path('admin/usuarios/', views.api_admin_usuarios),
    path('admin/usuarios/rol/', views.api_admin_cambiar_rol),
    path('admin/prestamo/<int:prestamo_id>/', views.api_admin_eliminar_prestamo),

    path('admin/reloj/', views.api_reloj),
    path('admin/reloj/avanzar/', views.api_reloj_avanzar),
    path('admin/reloj/reset/', views.api_reloj_reset),

    path('calculadora/', views.api_calculadora),

    # Simulador educativo legal
    path('tasas/tipos/', views.api_tipos_tasa),
    path('tasas/convertir/', views.api_tasas_convertir),
    path('tasas/usura/', views.api_usura),
    path('tasas/usura/actualizar/', views.api_usura_actualizar),
    path('tasas/gota-comparar/', views.api_gota_comparar),
    path('simular/', views.api_simular),
    path('mis-simulaciones/', views.api_mis_simulaciones),
]
