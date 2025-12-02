"use client"
import { NavLink, useNavigate } from "react-router-dom"
import { User } from "lucide-react"

export default function TopNav({ brand, tabs = [], activeKey }) {
  const navigate = useNavigate()

  const routeByKey = {
    home: "/home",
    docs: "/docs",
    map: "/mapa",
    telemetry: "/telemetry",
  }

  return (
    <header className="topnav-black">
      {/* Logo y brand */}
      <div className="topnav-brand">
        <div className="logo-text">
          <div className="logo-university">UNIVERSIDAD</div>
          <div className="logo-name">EAFIT</div>
        </div>
      </div>

      {/* Navegación centrada */}
      <nav className="topnav-nav">
        {tabs.map((tab) => {
          const path = routeByKey[tab.key] || "/home"
          return (
            <NavLink key={tab.key} to={path} className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}>
              {tab.label}
            </NavLink>
          )
        })}
      </nav>

      <button className="user-icon" onClick={() => navigate("/home")} title="Perfil">
        <User size={20} color="white" />
      </button>
    </header>
  )
}
