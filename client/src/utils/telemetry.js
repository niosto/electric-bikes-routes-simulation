// client/src/utils/telemetry.js

export function buildClientTelemetry(route) {
  const coords = route.geometry.coordinates || [];
  const potencia = route.properties.potencia || [];
  const soc = route.properties.soc || [];

  const telemetry = coords.map((c, i) => ({
    lat: c[1],
    lng: c[0],
    altitude: c[2] ?? null,
    power_kW: potencia[i] ?? null,
    soc: soc[i] ?? null,
    speed_kmh: null,     // backend synthetic unless included
    energy_kWh: null,    // backend synthetic unless included
    t_epoch: null        // backend synthetic unless included
  }));

  return telemetry;
}