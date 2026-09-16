import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { api } from '../api'

export default function Register({ setUser }) {
  const [params] = useSearchParams()
  const codigoUrl = params.get('code') || ''
  const [form, setForm] = useState({ username: '', password: '', nombre: '', telefono: '', rol: codigoUrl ? 'cliente' : 'prestador', codigo: codigoUrl })
  const [err, setErr] = useState('')
  const nav = useNavigate()
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  const enviar = async (e) => {
    e.preventDefault()
    setErr('')
    try {
      const u = await api.register(form)
      setUser(u)
      nav(u.rol === 'admin' ? '/admin' : u.rol === 'prestador' ? '/prestador' : '/cliente')
    } catch (e) { setErr(e.message) }
  }

  return (
    <div className="card" style={{ maxWidth: 480, margin: '30px auto' }}>
      <h2>Crear cuenta</h2>
      {codigoUrl && <p style={{ color: '#4ade80' }}>Vienes con el link de tu prestador (código {codigoUrl}). Tu cuenta será de <b>cliente</b>.</p>}
      <form onSubmit={enviar}>
        <input placeholder="Usuario" value={form.username} onChange={set('username')} />
        <input placeholder="Contraseña" type="password" value={form.password} onChange={set('password')} />
        <input placeholder="Nombre completo" value={form.nombre} onChange={set('nombre')} />
        <input placeholder="Teléfono" value={form.telefono} onChange={set('telefono')} />
        {!codigoUrl && (
          <select value={form.rol} onChange={set('rol')}>
            <option value="prestador">Soy Prestador (pagadiario)</option>
            <option value="cliente">Soy Cliente</option>
          </select>
        )}
        <input placeholder="Código del prestador (si tienes link)" value={form.codigo} onChange={set('codigo')} />
        {err && <p style={{ color: '#f87171' }}>{err}</p>}
        <button style={{ width: '100%' }}>Registrarme y aceptar préstamo</button>
      </form>
    </div>
  )
}
