// Exporta JSON de entrada (para backend /routes)
export function buildVehiclesJSON(vehicles, options) {
  return {
    options: {
      profile: options?.profile ?? "driving",
      alternatives: !!options?.alternatives,
      steps: !!options?.steps,
      geometries: "geojson",
      alt_count: options?.alt_count ?? 3,
      alt_share: options?.alt_share ?? 0.6,
      alt_weight: options?.alt_weight ?? 1.4,
    },
    vehicles: vehicles.map(v => ({
      vehicle_id: v.id,
      waypoints: v.waypoints.map(wp => ({ coordinates: [wp.coordinates[0], wp.coordinates[1]] })),
    })),
  };
}

// Exporta GeoJSON de las rutas calculadas por ORS
export function buildRoutesFeatureCollection(routes, selectedAlt = {}) {
  const features = Object.entries(routes).map(([vehicle_id, info]) => {
    const sel = selectedAlt[vehicle_id] ?? 0;
    const chosen = sel === 0 ? info.geometry : (info.alternatives?.[sel - 1]?.geometry);
    const coords = (chosen?.coordinates || []).map(c => [c[0], c[1]]);
    return {
      type: "Feature",
      properties: { vehicle_id, selected_alt: sel },
      geometry: { type: "LineString", coordinates: coords },
    };
  });
  return { type: "FeatureCollection", features };
}

// (Opcional) Exporta GeoJSON de los waypoints (como LineString)
export function buildWaypointsFeatureCollection(vehicles) {
  const features = vehicles
    .filter(v => v.waypoints.length >= 2)
    .map(v => ({
      type: "Feature",
      properties: { vehicle_id: v.id },
      geometry: {
        type: "LineString",
        coordinates: v.waypoints.map(wp => [wp.coordinates[0], wp.coordinates[1]]),
      },
    }));
  return { type: "FeatureCollection", features };
}