import { useEffect, useState } from 'react'
import { api, cop } from '../api'

/* Panel ADMIN: ve y regula todo. */
export default function AdminDashboard() {
  const [res, setRes] = useState(null)
  const [users, setUsers] = useState([])
  const [prestamos, setPrestamos] = useState([])
  const [reloj, setReloj] = useState(null)
  const [dias, setDias] = useState(1)
  const [msg, setMsg] = useState('')

  const cargar = async () => {
    setRes(await api.adminResumen().catch(() => null))
    setUsers(await api.adminUsuarios().catch(() => []))
    setPrestamos(await api.prestamosPrestador().catch(() => []))
    setReloj(await api.reloj().catch(() => null))
  }
  useEffect(() => { cargar() }, [])

  const rol = async (u, nuevo) => {
    await api.cambiarRol(u.id, nuevo)
    cargar()
  }

  const saltar = async () => {
    setMsg('')
    try {
      const r = await api.saltarDia(Number(dias) || 1)
      setMsg('⏩ ' + r.mensaje)
      cargar()
    } catch (e) { setMsg('Error: ' + e.message) }
  }

  const reset = async () => {
    const r = await api.resetReloj()
    setMsg('🕒 ' + r.mensaje)
    cargar()
  }

  return (
    <>
      <h2>Panel Administrador 🛠️ (simulador)</h2>
      <div className="card" style={{ borderColor: '#4ade80' }}>
        Gestiona usura en <b>/simulador</b> (API <code>/api/tasas/usura/actualizar/</code>). La reja fue eliminada por legalidad.
      </div>
      <div className="card">
        <h3>⏰ Reloj del sistema {reloj?.simulando && <span className="badge b-mora">SIMULANDO</span>}</h3>
        <p>
          Fecha real: <b>{reloj?.real}</b> | Fecha del sistema: <b>{reloj?.hoy}</b>
          {reloj?.simulando && <> (simulada: {reloj.simulada})</>}
        </p>
        <p style={{ opacity: .7 }}>Reloj pedagógico para históricos. El flujo legal está en /simulador (sin mora intimidante).</p>
        <div className="row" style={{ alignItems: 'end' }}>
          <div>
            <label>Días a saltar</label>
            <input type="number" min="1" max="365" value={dias} onChange={e => setDias(e.target.value)} />
          </div>
          <div>
            <button onClick={saltar}>⏩ Saltar el día</button>{' '}
            <button className="sec" onClick={() => { setDias(7); }}>7 días</button>{' '}
            <button className="danger" onClick={reset}>Volver a fecha real</button>
          </div>
        </div>
      </div>
      {res && <div className="row">
        <div className="card"><b>Usuarios</b><br /><span style={{ fontSize: 26 }}>{res.usuarios}</span></div>
        <div className="card"><b>Préstamos</b><br /><span style={{ fontSize: 26 }}>{res.prestamos}</span></div>
        <div className="card"><b>Total prestado</b><br /><span style={{ fontSize: 22 }}>{cop(res.total_prestado)}</span></div>
        <div className="card"><b>Total recaudado</b><br /><span style={{ fontSize: 22 }}>{cop(res.total_recaudado)}</span></div>
        <div className="card"><b>En mora</b><br /><span style={{ fontSize: 26, color: '#f87171' }}>{res.en_mora}</span></div>
      </div>}
      <div className="card">
        <h3>Usuarios y roles</h3>
        <table><thead><tr><th>ID</th><th>Usuario</th><th>Rol</th><th>Prestador</th><th>Código invite</th><th>Acción</th></tr></thead>
          <tbody>{users.map(u => <tr key={u.id}>
            <td>{u.id}</td><td>{u.username}</td><td>{u.rol}</td><td>{u.prestador || '-'}</td><td>{u.codigo_invite || '-'}</td>
            <td>
              <button className="sec" onClick={() => rol(u, 'admin')}>Admin</button>{' '}
              <button className="sec" onClick={() => rol(u, 'prestador')}>Prestador</button>{' '}
              <button className="sec" onClick={() => rol(u, 'cliente')}>Cliente</button>
            </td></tr>)}</tbody></table>
      </div>
      <div className="card">
        <h3>Histórico (solo comparativa)</h3>
        {prestamos.map(p => (
          <p key={p.id}>#{p.id} {p.cliente} ← {p.prestador} | {cop(p.monto_prestado)} → {cop(p.monto_total)} | saldo {cop(p.saldo_plata)} | mora {p.dias_mora}d ({p.cuotas_vencidas}) | {p.estado}</p>
        ))}
      </div>
      {msg && <p>{msg}</p>}
    </>
  )
}
