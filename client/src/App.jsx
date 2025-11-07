import React from "react";
import { BrowserRouter, Routes, Route, NavLink, useLocation, Navigate } from "react-router-dom";
import PageShell from "./components/layout/PageShell.jsx";
import TopNav from "./components/layout/TopNav.jsx";
import MapPage from "./pages/MapPage.jsx";
import TelemetryPage from "./pages/TelemetryPage.jsx";
import "./index.css";

// Mapea ruta -> clave activa para TopNav
function useActiveKey() {
  const { pathname } = useLocation();
  if (pathname === "/telemetry") return "telemetry";
  return "map";
}

function AppFrame({ children }) {
  const activeKey = useActiveKey();

  // Pestañas para TopNav (visual)
  const tabs = [
    { key: "map", label: "Mapa (Rutas)" },
    { key: "telemetry", label: "Telemetría" },
  ];

  return (
    <PageShell>
      <TopNav brand={null} tabs={tabs} activeKey={activeKey} />

      {/* Barra mínima de navegación (clickable) por si TopNav solo es visual */}
      <div style={{ padding: "8px 16px" }}>
        <NavLink
          to="/"
          end
          style={({ isActive }) => ({
            marginRight: 12,
            padding: "6px 10px",
            borderRadius: 8,
            textDecoration: "none",
            color: isActive ? "#fff" : "#111",
            background: isActive ? "#111" : "transparent",
            border: "1px solid #e5e7eb",
          })}
        >
          Mapa (Rutas)
        </NavLink>
        <NavLink
          to="/telemetry"
          style={({ isActive }) => ({
            padding: "6px 10px",
            borderRadius: 8,
            textDecoration: "none",
            color: isActive ? "#fff" : "#111",
            background: isActive ? "#111" : "transparent",
            border: "1px solid #e5e7eb",
          })}
        >
          Telemetría
        </NavLink>
      </div>

      {children}
    </PageShell>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppFrame>
        <Routes>
          <Route path="/" element={<MapPage />} />
          <Route path="/telemetry" element={<TelemetryPage />} />
          {/* Fallback a inicio si alguien pone una ruta rara */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppFrame>
    </BrowserRouter>
  );
}