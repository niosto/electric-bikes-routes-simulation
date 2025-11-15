import React from "react";
import { NavLink } from "react-router-dom";

/**
 * TopNav con pestañas táctiles.
 *
 * props:
 *  - brand:      contenido opcional a la izquierda (logo, texto, etc.)
 *  - tabs:       [{ key: "home", label: "Home" }, ...]
 *  - activeKey:  clave activa (para resaltar por ruta, opcional)
 */
const routeByKey = {
  home: "/home",
  docs: "/docs",
  map: "/mapa",
  telemetry: "/telemetry",
};

export default function TopNav({ brand, tabs = [], activeKey }) {
  return (
    <header className="topnav">
      {/* Brand opcional (por ahora tú lo pasas como null) */}
      {brand && (
        <div style={{ marginRight: 16, fontWeight: 600 }}>
          {brand}
        </div>
      )}

      <nav className="tabs">
        {tabs.map((tab) => {
          const path = routeByKey[tab.key] || "/home";

          return (
            <NavLink
              key={tab.key}
              to={path}
              // NavLink ya genera <a>, y usamos la clase "active" para tu CSS
              className={({ isActive }) =>
                (isActive || activeKey === tab.key) ? "active" : ""
              }
              style={{ textDecoration: "none" }}
            >
              {tab.label}
            </NavLink>
          );
        })}
      </nav>
    </header>
  );
}