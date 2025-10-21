import React, { useMemo } from "react";
import L from "leaflet";
import {
  MapContainer,
  TileLayer,
  Marker,
  Polyline,
  LayersControl,
  GeoJSON,
  useMapEvents,
} from "react-leaflet";
import { COLORS } from "../../utils/colors.js";
import { makeColoredIcon } from "../../utils/icons.js";
import CoordsPanel from "./CoordsPanel.jsx";

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

function ClickToAdd({ onAdd }) {
  useMapEvents({
    click(e) {
      onAdd([+e.latlng.lng.toFixed(6), +e.latlng.lat.toFixed(6)]);
    },
  });
  return null;
}

export default function MapView({
  vehicles,
  activeVehicle,
  routes = {},
  lastPoint,
  handleAddWaypoint,
  removeWaypointAt,
  clearWaypointsActive,
  selectedAlt = {},
  setSelectedAlt = () => {},
  importedGeoJSON, // capa importada (solo pintar)
  drawOnly = false, // evita ORS y clicks cuando hay archivo
}) {
  const center = [6.2442, -75.5812];

  // Mapa de colores por vehicle_id en la capa importada
  const importedColorMap = useMemo(() => {
    const map = new Map();
    if (importedGeoJSON?.features?.length) {
      let idx = 0;
      for (const f of importedGeoJSON.features) {
        const vid =
          (f.properties && f.properties.vehicle_id) ||
          (f.properties && f.properties.id) ||
          "otros";
        if (!map.has(vid)) {
          map.set(vid, COLORS[idx % COLORS.length]);
          idx++;
        }
      }
    }
    return map;
  }, [importedGeoJSON?.features?.length]);

  const markerIcons = useMemo(
    () =>
      vehicles.map((_, i) => ({
        start: makeColoredIcon(COLORS[i % COLORS.length], i + 1, "start"),
        end: makeColoredIcon(COLORS[i % COLORS.length], i + 1, "end"),
        normal: makeColoredIcon(COLORS[i % COLORS.length], i + 1, "normal"),
      })),
    [vehicles.length]
  );

  const activeId = vehicles[activeVehicle]?.id;
  const activeRouteInfo = routes[activeId];
  const selectedAltIndex = selectedAlt?.[activeId] ?? 0;

  return (
    <>
      {/* CoordsPanel solo útil en modo manual */}
      {!drawOnly && (
        <CoordsPanel
          activeVehicleObj={vehicles[activeVehicle]}
          lastPoint={lastPoint}
          removeWaypointAt={removeWaypointAt}
          clearWaypointsActive={clearWaypointsActive}
          activeRouteInfo={activeRouteInfo}
          selectedAltIndex={selectedAltIndex}
          onChangeSelectedAlt={(i) =>
            setSelectedAlt((s) => ({ ...s, [activeId]: i }))
          }
        />
      )}

      <MapContainer
        center={center}
        zoom={16}
        className="map-root"
        zoomControl
        preferCanvas
      >
        <LayersControl position="topright">
          <LayersControl.BaseLayer checked name="CARTO (proxy local)">
            <TileLayer
              url="http://localhost:8000/tiles/carto/{z}/{x}/{y}.png"
              attribution="© OpenStreetMap contributors · © CARTO"
              detectRetina
              maxZoom={18}
            />
          </LayersControl.BaseLayer>
        </LayersControl>

        {/* Click para agregar puntos: SOLO en modo manual */}
        {!drawOnly && <ClickToAdd onAdd={handleAddWaypoint} />}

        {/* Capa importada (solo pintar) con colores por vehicle_id */}
        {importedGeoJSON?.features?.length > 0 && (
          <GeoJSON
            key="imported"
            data={importedGeoJSON}
            style={(feat) => {
              const vid =
                (feat.properties && feat.properties.vehicle_id) ||
                (feat.properties && feat.properties.id) ||
                "otros";
              const color = importedColorMap.get(vid) || "#6b7280";
              return {
                color,
                weight: 6,
                opacity: 1.0,
              };
            }}
          />
        )}

        {/* Marcadores de waypoints (solo en manual) */}
        {!drawOnly &&
          vehicles.map((v, vi) =>
            v.waypoints.map((wp, idx) => {
              const pos = [wp.coordinates[1], wp.coordinates[0]];
              const icon =
                idx === 0
                  ? markerIcons[vi].start
                  : idx === v.waypoints.length - 1
                  ? markerIcons[vi].end
                  : markerIcons[vi].normal;
              return (
                <Marker key={`${v.id}-wp-${idx}`} position={pos} icon={icon} />
              );
            })
          )}

        {/* Polylines ORS (solo en manual) */}
        {!drawOnly &&
          vehicles.map((v, idx) => {
            const info = routes[v.id];
            if (!info) return null;
            const sel = selectedAlt?.[v.id] ?? 0;
            const chosen =
              sel === 0 ? info.geometry : info.alternatives?.[sel - 1]?.geometry;
            if (!chosen?.coordinates?.length) return null;
            const coords = chosen.coordinates.map(([lng, lat]) => [lat, lng]);
            return (
              <Polyline
                key={`route-${v.id}`}
                positions={coords}
                pathOptions={{ color: COLORS[idx], weight: 5, opacity: 0.9 }}
              />
            );
          })}
      </MapContainer>
    </>
  );
}