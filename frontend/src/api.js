const BASE = 'http://localhost:8000/api'

async function req(path, opts = {}) {
  const res = await fetch(BASE + path, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  })
  const data = await res.json().catch(() => ({}))
  if (!data.ok) throw new Error(data.error || 'Error en el servidor')
  return data.data
}

export const api = {
  me: () => req('/me/'),
  login: (username, password) =>
    req('/login/', { method: 'POST', body: JSON.stringify({ username, password }) }),
  register: (payload) =>
    req('/register/', { method: 'POST', body: JSON.stringify(payload) }),
  logout: () => req('/logout/', { method: 'POST', body: '{}' }),

  miCodigo: () => req('/mi-codigo/'),
  misClientes: () => req('/prestador/clientes/'),
  prestamosPrestador: (cliente_id) =>
    req('/prestador/prestamos/' + (cliente_id ? `?cliente_id=${cliente_id}` : '')),
  crearPrestamo: (payload) =>
    req('/prestador/prestamos/crear/', { method: 'POST', body: JSON.stringify(payload) }),

  misPrestamos: () => req('/cliente/mis-prestamos/'),
  detalle: (id) => req(`/cliente/prestamo/${id}/`),
  pagar: (prestamo_id, valor) =>
    req('/cliente/pagar/', { method: 'POST', body: JSON.stringify({ prestamo_id, valor }) }),

  adminResumen: () => req('/admin/resumen/'),
  adminUsuarios: () => req('/admin/usuarios/'),
  cambiarRol: (user_id, rol) =>
    req('/admin/usuarios/rol/', { method: 'POST', body: JSON.stringify({ user_id, rol }) }),
  reloj: () => req('/admin/reloj/'),
  saltarDia: (dias = 1) =>
    req('/admin/reloj/avanzar/', { method: 'POST', body: JSON.stringify({ dias }) }),
  resetReloj: () =>
    req('/admin/reloj/reset/', { method: 'POST', body: '{}' }),

  calculadora: (params) =>
    req('/calculadora/?' + new URLSearchParams(params).toString()),

  // Simulador educativo legal
  tiposTasa: () => req('/tasas/tipos/'),
  usura: () => req('/tasas/usura/'),
  usuraActualizar: (vigencia, ea_max_pct) =>
    req('/tasas/usura/actualizar/', { method: 'POST', body: JSON.stringify({ vigencia, ea_max_pct }) }),
  convertir: (valor, tipo) =>
    req(`/tasas/convertir/?valor=${valor}&tipo=${tipo}`),
  gotaComparar: (monto_prestado, monto_total, dias) =>
    req(`/tasas/gota-comparar/?monto_prestado=${monto_prestado}&monto_total=${monto_total}&dias=${dias}`),
  simular: (payload) =>
    req('/simular/', { method: 'POST', body: JSON.stringify(payload) }),
  misSimulaciones: () => req('/mis-simulaciones/'),
}

export function cop(v) {
  return '$' + Number(v || 0).toLocaleString('es-CO')
}
