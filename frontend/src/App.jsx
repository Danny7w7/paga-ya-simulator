import { useEffect, useState } from 'react'
import { Routes, Route, Link, useNavigate, Navigate } from 'react-router-dom'
import { api } from './api'
import Login from './pages/Login'
import Register from './pages/Register'
import AdminDashboard from './pages/AdminDashboard'
import PrestadorDashboard from './pages/PrestadorDashboard'
import ClienteDashboard from './pages/ClienteDashboard'
import Simulador from './pages/Simulador'

export default function App() {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const nav = useNavigate()

  const cargar = async () => {
    try { setUser(await api.me()) } catch { setUser(null) }
    setLoading(false)
  }
  useEffect(() => { cargar() }, [])

  const salir = async () => {
    await api.logout().catch(() => {})
    setUser(null)
    nav('/login')
  }

  if (loading) return <div className="container">Cargando Paga Ya...</div>

  const home = !user ? '/login'
    : user.rol === 'admin' ? '/admin'
    : user.rol === 'prestador' ? '/prestador' : '/cliente'

  return (
    <>
      <div className="nav">
        <b>📚 Paga-Ya Simulador</b>
        <span style={{ opacity: .7 }}>Educación financiera — sin préstamo real</span>
        <span style={{ flex: 1 }} />
        <Link to="/simulador">Simulador</Link>
        {user ? <>
          <span>{user.username} ({user.rol})</span>
          <button className="sec" onClick={salir}>Salir</button>
        </> : <>
          <Link to="/login">Entrar</Link>
          <Link to="/register">Registrarse</Link>
        </>}
      </div>
      <div className="container">
        <Routes>
          <Route path="/login" element={<Login setUser={setUser} />} />
          <Route path="/register" element={<Register setUser={setUser} />} />
          <Route path="/simulador" element={<Simulador />} />
          <Route path="/admin" element={user?.rol === 'admin' ? <AdminDashboard /> : <Navigate to={home} />} />
          <Route path="/prestador" element={(user?.rol === 'prestador' || user?.rol === 'admin') ? <PrestadorDashboard user={user} /> : <Navigate to={home} />} />
          <Route path="/cliente" element={(user?.rol === 'cliente' || user?.rol === 'admin') ? <ClienteDashboard /> : <Navigate to={home} />} />
          <Route path="*" element={<Navigate to={user ? '/simulador' : home} />} />
        </Routes>
      </div>
    </>
  )
}
