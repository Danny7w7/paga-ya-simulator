import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { api } from '../api'

export default function Login({ setUser }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [err, setErr] = useState('')
  const nav = useNavigate()

  const entrar = async (e) => {
    e.preventDefault()
    setErr('')
    try {
      const u = await api.login(username, password)
      setUser(u)
      nav(u.rol === 'admin' ? '/admin' : u.rol === 'prestador' ? '/prestador' : '/cliente')
    } catch (e) { setErr(e.message) }
  }

  return (
    <div className="card" style={{ maxWidth: 420, margin: '40px auto' }}>
      <h2>Entrar a Paga Ya</h2>
      <form onSubmit={entrar}>
        <input placeholder="Usuario" value={username} onChange={e => setUsername(e.target.value)} />
        <input placeholder="Contraseña" type="password" value={password} onChange={e => setPassword(e.target.value)} />
        {err && <p style={{ color: '#f87171' }}>{err}</p>}
        <button style={{ width: '100%' }}>Entrar</button>
      </form>
      <p>¿Eres cliente de un prestador? <Link to="/register">Regístrate con su link</Link></p>
      <div style={{ background: '#020617', borderRadius: 8, padding: 10, fontSize: 13, opacity: .9 }}>
        <b>Cuentas demo</b> (las crea el seed):<br />
        🛠️ admin / admin123<br />
        💰 don_chepe / chepe123 &nbsp;·&nbsp; la_patrona / patrona123<br />
        📅 carlos, maria, juan, lucia / cliente123
      </div>
    </div>
  )
}
