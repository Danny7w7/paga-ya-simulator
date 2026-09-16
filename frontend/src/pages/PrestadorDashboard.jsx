import { useEffect, useState } from 'react'
import { api, cop } from '../api'

/* Panel PRESTADOR (modo histórico-educativo): sin reja. Uso real en /simulador. */
export default function PrestadorDashboard() {
  const [codigo, setCodigo] = useState(null)
  const [clientes, setClientes] = useState([])
  const [prestamos, setPrestamos] = useState([])
  const [msg, setMsg] = useState('')
  const [f, setF] = useState({
    cliente_username: '', monto_prestado: 100000, monto_total: 120000,
    num_cuotas: 7, frecuencia: 'DIARIO', modalidad: 'TOTAL_PLAZO', fecha_inicio: '',
  })
  // helpers de calculadora (todo variable, sin interés compuesto)
  const [calc, setCalc] = useState({ modo: 'TOTAL_PLAZO', monto: 100000, total: 120000, dias: 7, cuotaDiaria: 5000, numDias: 24, frec: 'SEMANAL', nCuotas: 4 })

  const cargar = async () => {
    setCodigo(await api.miCodigo().catch(() => null))
    setClientes(await api.misClientes().catch(() => []))
    setPrestamos(await api.prestamosPrestador().catch(() => []))
  }
  useEffect(() => { cargar() }, [])
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value })

  // Los 3 ejemplos del dueño, pero 100% editables:
  const aplicarEjemplo = (n) => {
    if (n === 1) setF({ ...f, modalidad: 'TOTAL_PLAZO', monto_prestado: calc.monto, monto_total: calc.total, num_cuotas: calc.dias, frecuencia: 'DIARIO' })
    if (n === 2) setF({ ...f, modalidad: 'CUOTA_DIARIA', monto_prestado: 100000, monto_total: calc.cuotaDiaria * calc.numDias, num_cuotas: calc.numDias, frecuencia: 'DIARIO' })
    if (n === 3) setF({ ...f, modalidad: 'PERIODICO', monto_prestado: calc.monto, monto_total: calc.total, num_cuotas: calc.nCuotas, frecuencia: calc.frec })
  }

  const crear = async (e) => {
    e.preventDefault()
    setMsg('')
    try {
      const payload = {
        cliente_username: f.cliente_username, modalidad: f.modalidad, frecuencia: f.frecuencia,
        monto_prestado: Number(f.monto_prestado), monto_total: Number(f.monto_total),
        num_cuotas: Number(f.num_cuotas),
        ...(f.fecha_inicio ? { fecha_inicio: f.fecha_inicio } : {}),
      }
      await api.crearPrestamo(payload)
      setMsg('Préstamo creado con éxito (valores fijos, sin interés compuesto).')
      cargar()
    } catch (e) { setMsg('Error: ' + e.message) }
  }

  const reja = async (id) => {
    alert('Función eliminada por legalidad. Usa el Simulador (/simulador) y acuerdos de pago dignos.')
  }

  return (
    <>
      <h2>Panel Prestador 💰 (histórico-educativo)</h2>
      <div className="card" style={{ borderColor: '#4ade80' }}>
        Este panel conserva préstamos históricos solo para comparar. El flujo legal está en <b>/simulador</b> (todas las tasas + usura, sin desembolso).
      </div>
      {codigo && <div className="card">
        <h3>Tu link para registrar clientes</h3>
        <div className="linkbox">{codigo.link}</div>
        <p>Compártelo por WhatsApp. Quien se registre ahí queda como tu cliente y acepta el préstamo.</p>
        <button className="sec" onClick={() => navigator.clipboard.writeText(codigo.link)}>Copiar link</button>
      </div>}

      <div className="card">
        <h3>Mis clientes ({clientes.length}) — 1 prestador : N clientes</h3>
        <table><thead><tr><th>Cliente</th><th>Tel</th><th>Préstamos</th><th>Cuotas caídas</th></tr></thead>
          <tbody>{clientes.map(c => <tr key={c.id}>
            <td>{c.username}</td><td>{c.telefono}</td><td>{c.num_prestamos}</td>
            <td>{c.cuotas_vencidas > 0 ? <span className="badge b-mora">{c.cuotas_vencidas} caídas</span> : <span className="badge b-ok">al día</span>}</td>
          </tr>)}</tbody></table>
      </div>

      <div className="card">
        <h3>Crear préstamo (SIN interés compuesto — todo variable)</h3>
        <div className="row">
          <div className="card"><b>1) 100mil → 120mil en 7 días</b>
            <input type="number" value={calc.monto} onChange={e => setCalc({ ...calc, monto: +e.target.value })} placeholder="Prestado" />
            <input type="number" value={calc.total} onChange={e => setCalc({ ...calc, total: +e.target.value })} placeholder="Total" />
            <input type="number" value={calc.dias} onChange={e => setCalc({ ...calc, dias: +e.target.value })} placeholder="Días" />
            <button className="sec" onClick={() => aplicarEjemplo(1)}>Usar estos valores</button></div>
          <div className="card"><b>2) 5000 diarios por X días</b>
            <input type="number" value={calc.cuotaDiaria} onChange={e => setCalc({ ...calc, cuotaDiaria: +e.target.value })} placeholder="Cuota diaria" />
            <input type="number" value={calc.numDias} onChange={e => setCalc({ ...calc, numDias: +e.target.value })} placeholder="X días" />
            <p>Total = {cop(calc.cuotaDiaria * calc.numDias)}</p>
            <button className="sec" onClick={() => aplicarEjemplo(2)}>Usar estos valores</button></div>
          <div className="card"><b>3) Semanal / quincenal / mensual</b>
            <select value={calc.frec} onChange={e => setCalc({ ...calc, frec: e.target.value })}>
              <option value="SEMANAL">Semanal</option><option value="QUINCENAL">Quincenal</option><option value="MENSUAL">Mensual</option>
            </select>
            <input type="number" value={calc.nCuotas} onChange={e => setCalc({ ...calc, nCuotas: +e.target.value })} placeholder="N° cuotas" />
            <button className="sec" onClick={() => aplicarEjemplo(3)}>Usar estos valores</button></div>
        </div>
        <form onSubmit={crear}>
          <div className="row">
            <input placeholder="Usuario del cliente (se registró con tu link)" value={f.cliente_username} onChange={set('cliente_username')} />
            <input type="number" placeholder="Monto prestado" value={f.monto_prestado} onChange={set('monto_prestado')} />
            <input type="number" placeholder="Monto total a pagar" value={f.monto_total} onChange={set('monto_total')} />
          </div>
          <div className="row">
            <input type="number" placeholder="N° cuotas" value={f.num_cuotas} onChange={set('num_cuotas')} />
            <select value={f.frecuencia} onChange={set('frecuencia')}>
              <option value="DIARIO">Diario</option><option value="SEMANAL">Semanal</option>
              <option value="QUINCENAL">Quincenal</option><option value="MENSUAL">Mensual</option>
            </select>
            <select value={f.modalidad} onChange={set('modalidad')}>
              <option value="TOTAL_PLAZO">Total en plazo</option><option value="CUOTA_DIARIA">Cuota diaria fija</option><option value="PERIODICO">Periódico</option>
            </select>
            <input type="date" value={f.fecha_inicio} onChange={set('fecha_inicio')} />
          </div>
          <button>Generar préstamo y cuotas</button>
        </form>
        {msg && <p>{msg}</p>}
      </div>

      <div className="card">
        <h3>Préstamos ({prestamos.length})</h3>
        {prestamos.map(p => (
          <div key={p.id} className="card">
            <b>#{p.id} {p.cliente}</b> — {cop(p.monto_prestado)} → {cop(p.monto_total)} | {p.frecuencia} {cop(p.valor_cuota)} x {p.num_cuotas} | Saldo {cop(p.saldo_plata)}
            {' '}<span className={`badge ${p.estado === 'MORA' ? 'b-mora' : p.estado === 'PAGADO' ? 'b-ok' : 'b-pend'}`}>{p.estado}</span>
            {p.cuotas_vencidas > 0 && (
              <div className="alerta-prestador">
                ⚠️ Este caso histórico tuvo {p.cuotas_vencidas} cuota(s) en mora ({p.dias_mora} días).
                En el simulador esto se resuelve con <b>acuerdo de pago digno</b>, nunca con intimidación.
                <br /><br />
                <span className="badge b-pend">Cobranza respetuosa (Ley 2300/23)</span>
              </div>
            )}
            <table><thead><tr><th>#</th><th>Vence</th><th>Valor</th><th>Pagado</th><th>Estado</th></tr></thead>
              <tbody>{p.cuotas.map(c => <tr key={c.id}><td>{c.numero}</td><td>{c.fecha_vencimiento}</td><td>{cop(c.valor)}</td><td>{cop(c.valor_pagado)}</td><td>{c.estado}</td></tr>)}</tbody></table>
          </div>
        ))}
      </div>
    </>
  )
}
