import React from "react";
import PageShell from "./components/layout/PageShell.jsx";
import TopNav from "./components/layout/TopNav.jsx";
import MapPage from "./pages/MapPage.jsx";
import "./index.css";

export default function App() {
  return (
    <PageShell>
      <TopNav brand={null} tabs={[{ key: "map", label: "Mapa (Rutas)" }]} activeKey="map" />
      <MapPage />
    </PageShell>
  );
}