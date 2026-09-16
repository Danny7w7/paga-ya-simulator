import { useEffect, useState } from 'react'
import { api, cop } from '../api'

/* Simulador educativo: todas las tasas, usura y comparativa gota. Sin desembolso real. */
export default function Simulador() {
  const [tipos, setTipos] = useState([])
  const [usura, setUsura] = useState(null)
  const [f, setF] = useState({ monto: 500000, tasa_valor_pct: 2.0, tasa_tipo: 'EM', n_cuotas: 12, frecuencia: 'MENSUAL' })
  const [res, setRes] = useState(null)
  const [conv, setConv] = useState(null)
  const [gota, setGota] = useState({ monto_prestado: 100000, monto_total: 120000, dias: 7 })
  const [gotaRes, setGotaRes] = useState(null)
  const [msg, setMsg] = useState('')

  useEffect(() => {
    api.tiposTasa().then(setTipos).catch(() => {})
    api.usura().then(setUsura).catch(() => {})
  }, [])

  const set = (k) => (e) => setF({ ...f, [k]: e.target.value })

  const simular = async (e) => {
    e.preventDefault()
    setMsg('')
    try {
      const r = await api.simular({
        monto: Number(f.monto),
        tasa_valor_pct: Number(f.tasa_valor_pct),
        tasa_tipo: f.tasa_tipo,
        n_cuotas: Number(f.n_cuotas),
        frecuencia: f.frecuencia,
      })
      setRes(r)
    } catch (e) { setMsg('Error: ' + e.message) }
  }

  const convertir = async () => {
    try { setConv(await api.convertir(f.tasa_valor_pct, f.tasa_tipo)) }
    catch (e) { setMsg('Error: ' + e.message) }
  }

  const compararGota = async () => {
    try { setGotaRes(await api.gotaComparar(gota.monto_prestado, gota.monto_total, gota.dias)) }
    catch (e) { setMsg('Error: ' + e.message) }
  }

  return (
    <>
      <h2>Simulador Educativo 📚 (sin plata real)</h2>
      <div className="card" style={{ borderColor: '#4ade80' }}>
        <b>Usura vigente:</b> {usura ? `${usura.ea_max_pct}% EA (${usura.em_max_pct}% EM) — ${usura.vigencia}` : 'cargando...'}
        <br /><span style={{ opacity: .7 }}>Toda tasa EA superior configura usura (art. 305 CP). Solo educación financiera.</span>
      </div>

      <div className="card">
        <h3>1. Simular crédito legal</h3>
        <form onSubmit={simular}>
          <div className="row">
            <div><label>Monto simulado (COP)</label><input type="number" value={f.monto} onChange={set('monto')} /></div>
            <div><label>Tasa valor (%)</label><input type="number" step="0.01" value={f.tasa_valor_pct} onChange={set('tasa_valor_pct')} /></div>
            <div><label>Tipo tasa (todas)</label>
              <select value={f.tasa_tipo} onChange={set('tasa_tipo')}>
                {tipos.map(t => <option key={t.codigo} value={t.codigo}>{t.codigo} — {t.nombre}</option>)}
              </select>
            </div>
          </div>
          <div className="row">
            <div><label>N° cuotas</label><input type="number" value={f.n_cuotas} onChange={set('n_cuotas')} /></div>
            <div><label>Frecuencia</label>
              <select value={f.frecuencia} onChange={set('frecuencia')}>
                <option value="MENSUAL">Mensual</option><option value="QUINCENAL">Quincenal</option>
                <option value="SEMANAL">Semanal</option><option value="DIARIA">Diaria (pedagógica)</option>
              </select>
            </div>
          </div>
          <button>Simular</button>{' '}
          <button type="button" className="sec" onClick={convertir}>Ver todas las equivalencias</button>
        </form>
        {msg && <p>{msg}</p>}
      </div>

      {conv && (
        <div className="card">
          <h3>Todas las equivalencias de {conv.entrada.valor_pct}% {conv.entrada.tipo}</h3>
          <p>EA: <b>{conv.ea_equiv_pct}%</b> | EM: <b>{conv.em_equiv_pct}%</b> | {conv.es_usura ? <span className="badge b-mora">EN USURA</span> : <span className="badge b-ok">DENTRO TOPE</span>}</p>
          <table><thead><tr><th>Tipo</th><th>Valor %</th></tr></thead>
            <tbody>{Object.entries(conv.todas).map(([k, v]) => <tr key={k}><td>{k}</td><td>{v}</td></tr>)}</tbody></table>
        </div>
      )}

      {res && (
        <div className="card">
          <h3>Resultado {res.es_usura ? <span className="badge b-mora">EN USURA — solo educativo</span> : <span className="badge b-ok">TASA LEGAL</span>}</h3>
          <p>EM <b>{res.em_equiv_pct}%</b> | EA <b>{res.ea_equiv_pct}%</b> | Cuota <b>{cop(res.cuota_valor)}</b> | Total <b>{cop(res.total_pagar)}</b> (intereses {cop(res.total_intereses)})</p>
          <p style={{ opacity: .8 }}>{res.advertencia}</p>
          <table><thead><tr><th>#</th><th>Cuota</th><th>Interés</th><th>Capital</th><th>Saldo</th></tr></thead>
            <tbody>{res.tabla.map(r => <tr key={r.numero}><td>{r.numero}</td><td>{cop(r.cuota)}</td><td>{cop(r.interes)}</td><td>{cop(r.abono_capital)}</td><td>{cop(r.saldo)}</td></tr>)}</tbody></table>
        </div>
      )}

      <div className="card">
        <h3>2. Comparar un gota contra lo legal</h3>
        <div className="row">
          <input type="number" value={gota.monto_prestado} onChange={e => setGota({ ...gota, monto_prestado: +e.target.value })} placeholder="Prestado" />
          <input type="number" value={gota.monto_total} onChange={e => setGota({ ...gota, monto_total: +e.target.value })} placeholder="Total gota" />
          <input type="number" value={gota.dias} onChange={e => setGota({ ...gota, dias: +e.target.value })} placeholder="Días" />
        </div>
        <button className="sec" onClick={compararGota}>Comparar</button>
        {gotaRes && <p><b>{gotaRes.mensaje}</b><br />ED {gotaRes.gota.ed_pct}% | EM {gotaRes.gota.em_pct}% | EA {gotaRes.gota.ea_pct}%<br /><span style={{ opacity: .7 }}>{gotaRes.nota_legal}</span></p>}
      </div>
    </>
  )
}
