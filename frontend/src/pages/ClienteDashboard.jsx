import { useEffect, useState } from 'react'
import { api, cop } from '../api'

/* Panel CLIENTE (histórico-educativo): sin alerta intimidante. */
export default function ClienteDashboard() {
  const [prestamos, setPrestamos] = useState([])
  const [monto, setMonto] = useState({})
  const [msg, setMsg] = useState('')

  const cargar = async () => setPrestamos(await api.misPrestamos().catch(() => []))
  useEffect(() => { cargar() }, [])

  const enMora = prestamos.filter(p => p.cuotas_vencidas > 0)

  const pagar = async (id) => {
    setMsg('')
    try {
      const r = await api.pagar(id, Number(monto[id] || 0))
      setMsg(r.mensaje + ` Aplicado a cuotas: ${r.aplicadas.map(a => '#' + a[0] + ' ' + cop(a[1])).join(', ')}`)
      cargar()
    } catch (e) { setMsg('Error: ' + e.message) }
  }

  return (
    <>
      <h2>Mis casos históricos 📅</h2>
      <div className="card" style={{ borderColor: '#4ade80' }}>
        Módulo educativo. Para simular un crédito legal con todas las tasas ve a <b>/simulador</b>.
      </div>
      {enMora.length > 0 && (
        <div className="card" style={{ borderColor: '#fbbf24' }}>⚠️ Tienes {enMora.reduce((a, p) => a + p.cuotas_vencidas, 0)} cuota(s) histórica(s) en mora. En el simulador puedes comparar y planear un acuerdo de pago.
        </div>
      )}
      {prestamos.length === 0 && <div className="card">Aún no tienes préstamos. Regístrate con el link de tu prestador.</div>}
      {prestamos.map(p => (
        <div key={p.id} className="card">
          <h3>Préstamo #{p.id} con {p.prestador} — <span className={`badge ${p.estado === 'MORA' ? 'b-mora' : p.estado === 'PAGADO' ? 'b-ok' : 'b-pend'}`}>{p.estado}</span></h3>
          <div className="row">
            <div className="card">💰 Abonado a capital<br /><b style={{ fontSize: 24, color: '#4ade80' }}>{cop(p.abono_capital)}</b><br />de {cop(p.monto_total)}</div>
            <div className="card">💸 Debes (plata)<br /><b style={{ fontSize: 24, color: '#f87171' }}>{cop(p.saldo_plata)}</b></div>
            <div className="card">📆 Debes (días)<br /><b style={{ fontSize: 24, color: '#fbbf24' }}>{p.dias_deuda} días</b><br />{p.cuotas_vencidas} cuota(s) vencida(s)</div>
          </div>
          <p>Prestamo: {cop(p.monto_prestado)} → pagar {cop(p.monto_total)} en {p.num_cuotas} cuotas {p.frecuencia.toLowerCase()}s de {cop(p.valor_cuota)} (sin interés compuesto).</p>
          <table><thead><tr><th>#</th><th>Vence</th><th>Valor</th><th>Pagado</th><th>Saldo</th><th>Estado</th></tr></thead>
            <tbody>{p.cuotas.map(c => <tr key={c.id}><td>{c.numero}</td><td>{c.fecha_vencimiento}</td><td>{cop(c.valor)}</td><td>{cop(c.valor_pagado)}</td><td>{cop(c.saldo)}</td><td>{c.estado}</td></tr>)}</tbody></table>
          {p.estado !== 'PAGADO' && (
            <div className="row" style={{ marginTop: 12 }}>
              <input type="number" placeholder="Valor a pagar (COP)" value={monto[p.id] || ''} onChange={e => setMonto({ ...monto, [p.id]: e.target.value })} />
              <button onClick={() => pagar(p.id)}>Abonar (histórico)</button>
            </div>
          )}
        </div>
      ))}
      {msg && <div className="card">{msg}</div>}
      <p style={{ opacity: .6 }}>Histórico educativo. La simulación legal está en /simulador (sin desembolso real).</p>
    </>
  )
}
