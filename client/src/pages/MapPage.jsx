import React, { useState } from "react";
import ControlsPanel from "../components/map/ControlsPanel.jsx";
import MapView from "../components/map/MapView.jsx";
import useVehicles from "../hooks/useVehicles.js";
import useAutoRoutes from "../hooks/useAutoRoutes.js";
import StatsPanel from "../components/map/StatsPanel.jsx";


export default function MapPage() {
  const {
    vehicles,
    setVehicles,
    activeVehicle,
    setActiveVehicle,
    lastPoint,
    setLastPoint,
    addVehicle,
    removeVehicle,
    handleAddWaypoint,
    undoWaypoint,
    clearAll,
    removeWaypointAt,
    clearWaypointsActive,
  } = useVehicles();

  // Capa importada (solo pintar) y modo
  const [importedGeoJSON, setImportedGeoJSON] = useState(null);
  const [drawOnly, setDrawOnly] = useState(false);

  // cuando hay archivo cargado, el hook NO recibe vehículos (se queda sin input)
  const vehiclesForRouting = drawOnly ? [] : vehicles;

  const {
    options,
    setOptions,
    routes,
    selectedAlt,
    setSelectedAlt,
    totalSummary,
    computeRoutesManual,
  } = useAutoRoutes({ vehicles: vehiclesForRouting, enabled: !drawOnly });

  const handleGeoLoad = (fc) => {
    setImportedGeoJSON(fc);
    setDrawOnly(true);
  };

  const handleClearGeo = () => {
    setImportedGeoJSON(null);
    setDrawOnly(false);
  };

  return (
    <section className="page">
      {/* bloque superior: sidebar + mapa */}
      <div className="page-main">
        <aside className="sidebar">
          <ControlsPanel
            options={options}
            setOptions={setOptions}
            vehicles={vehicles}
            activeVehicle={activeVehicle}
            setActiveVehicle={setActiveVehicle}
            addVehicle={addVehicle}
            removeVehicle={removeVehicle}
            undoWaypoint={undoWaypoint}
            clearAll={clearAll}
            totalSummary={totalSummary}
            computeRoutesManual={computeRoutesManual}
            setVehicles={setVehicles}
            onGeoLoad={handleGeoLoad}
            onClearGeo={handleClearGeo}
            drawOnly={drawOnly}
            routes={routes}
            selectedAlt={selectedAlt}
          />
        </aside>

        <div className="map-wrapper">
          <MapView
            vehicles={vehicles}
            activeVehicle={activeVehicle}
            routes={routes}
            lastPoint={lastPoint}
            handleAddWaypoint={handleAddWaypoint}
            removeWaypointAt={removeWaypointAt}
            clearWaypointsActive={clearWaypointsActive}
            selectedAlt={selectedAlt}
            setSelectedAlt={setSelectedAlt}
            importedGeoJSON={importedGeoJSON}
            drawOnly={drawOnly}
          />
        </div>
      </div>

      {/* bloque inferior: estadísticas y gráficas */}
            {/* bloque inferior: estadísticas y gráficas */}
            {/* bloque inferior: estadísticas y gráficas */}
            {/* bloque inferior: estadísticas y gráficas */}
      <section className="stats-section">
        <StatsPanel
          routes={routes}
          totalSummary={totalSummary}
          vehicles={vehicles}
          activeVehicle={activeVehicle}
        />
      </section>
    </section>
  );
}