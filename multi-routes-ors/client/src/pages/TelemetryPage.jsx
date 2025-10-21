import React, { useMemo, useRef, useState } from "react";
import { Card, CardContent } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Slider } from "../components/ui/slider";
import { Upload, Undo2, Route, FileJson } from "lucide-react";
import MapView from "../components/map/MapView.jsx";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  AreaChart,
  Area,
  ResponsiveContainer,
} from "recharts";

/* ---------------- Utilidades geo / tiempo ---------------- */
function to2D(coords) {
  if (!Array.isArray(coords)) return [];
  return coords
    .map((c) => [Number(c[0]), Number(c[1])])
    .filter(([lon, lat]) => Number.isFinite(lon) && Number.isFinite(lat));
}
function fromBikesToFC(src) {
  if (!src.bikes || !Array.isArray(src.bikes)) return null;
  const features = [];
  src.bikes.forEach((bikeGroup, gi) => {
    if (!Array.isArray(bikeGroup)) return;
    bikeGroup.forEach((segmento, li) => {
      const coords = segmento?.coords;
      if (!Array.isArray(coords) || coords.length < 2) return;
      const processed = to2D(coords);
      if (processed.length < 2) return;
      const props = {
        vehicle_id: `moto-${gi + 1}`,
        leg: li + 1,
        origen: segmento.origen,
        destino: segmento.destino,
      };
      features.push({
        type: "Feature",
        properties: props,
        geometry: { type: "LineString", coordinates: processed },
      });
    });
  });
  return { type: "FeatureCollection", features };
}
function parseFechaToEpochSeconds(fecha) {
  try {
    if (typeof fecha !== "string") return null;
    const [ddmmyy, hhmmssRaw] = fecha.split(":");
    if (!ddmmyy || !hhmmssRaw) return null;
    const dd = +ddmmyy.slice(0, 2);
    const MM = +ddmmyy.slice(2, 4);
    const yy = +ddmmyy.slice(4, 6);
    const year = 2000 + yy;
    const hh = +hhmmssRaw.slice(0, 2);
    const mm = +hhmmssRaw.slice(2, 4);
    const ss = parseFloat(hhmmssRaw.slice(4));
    const d = new Date(Date.UTC(year, MM - 1, dd, hh, mm, ss));
    const secs = Math.floor(d.getTime() / 1000);
    return Number.isFinite(secs) ? secs : null;
  } catch {
    return null;
  }
}
function haversineKm([lng1, lat1], [lng2, lat2]) {
  const R = 6371;
  const toRad = (x) => (x * Math.PI) / 180;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lng2 - lng1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}
const cumulative = (arr) => {
  let s = 0;
  return arr.map((v) => (s += v));
};

/* ---------------- Página ---------------- */
export default function TelemetryPage() {
  const [fileName, setFileName] = useState("");
  const [geojson, setGeojson] = useState(null);
  const [telemetryRows, setTelemetryRows] = useState([]);
  const [downsample, setDownsample] = useState(1);
  const [tab, setTab] = useState("energy"); // power | speed | alt | energy
  const inputRef = useRef(null);

  function handleFile(e) {
    const f = e.target.files?.[0];
    if (!f) return;
    setFileName(f.name);
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const json = JSON.parse(reader.result);
        let fc = null;
        let rows = null;

        if (json?.type === "FeatureCollection") {
          fc = json;
        } else if (json?.bikes) {
          fc = fromBikesToFC(json);
        } else if (Array.isArray(json) && json.length > 1 && "latitude" in json[0]) {
          const coords = json.map((p) => [Number(p.longitude), Number(p.latitude)]);
          fc = {
            type: "FeatureCollection",
            features: [
              {
                type: "Feature",
                properties: { source: "telemetry" },
                geometry: { type: "LineString", coordinates: coords },
              },
            ],
          };
          rows = json.map((p, i) => ({
            i,
            lat: Number(p.latitude),
            lng: Number(p.longitude),
            alt: Number(p.altitude),
            speed_kmh: Number.isFinite(Number(p.speed)) ? Number(p.speed) * 3.6 : null,
            power_kW: Number.isFinite(Number(p.pw)) ? Number(p.pw) : null,
            t_epoch: parseFechaToEpochSeconds(p.fecha),
          }));
        }

        if (!fc) {
          alert("Formato no reconocido: usa FeatureCollection, bikes o lista de puntos.");
          return;
        }
        setGeojson(fc);
        setTelemetryRows(rows || []);
      } catch (err) {
        console.error(err);
        alert("Error procesando JSON: " + err.message);
      }
    };
    reader.readAsText(f);
  }

  function clearAll() {
    setFileName("");
    setGeojson(null);
    setTelemetryRows([]);
  }

  /* ---------- Cálculos/Métricas/datasets ---------- */
  const {
    totalKm,
    totalTimeMin,
    totalEnergy_kWh,
    chart_time_power,
    chart_speed,
    chart_alt,
    chart_energy_vs_dist,
  } = useMemo(() => {
    const coords = geojson?.features?.[0]?.geometry?.coordinates || [];
    const segKm = [];
    for (let i = 0; i < coords.length - 1; i++) segKm.push(haversineKm(coords[i], coords[i + 1]));
    const cumDistKm = cumulative(segKm);
    const totalKm = segKm.reduce((a, b) => a + b, 0);

    if (!telemetryRows?.length) {
      return {
        totalKm,
        totalTimeMin: 0,
        totalEnergy_kWh: 0,
        chart_time_power: [],
        chart_speed: [],
        chart_alt: [],
        chart_energy_vs_dist: cumDistKm.map((v, i) => ({ i, cum_km: v, cum_kWh: 0 })),
      };
    }

    const rows = [...telemetryRows];
    const haveEpoch = rows.every((r) => r.t_epoch !== null);
    if (haveEpoch) rows.sort((a, b) => a.t_epoch - b.t_epoch);
    const ds = Math.max(1, Math.round(downsample));
    const dsRows = rows.filter((_, idx) => idx % ds === 0);

    let cum_kWh = 0;
    let totalSeconds = 0;
    const t0 = haveEpoch ? dsRows[0].t_epoch : 0;

    const chart_time_power = [];
    const chart_speed = [];
    const chart_alt = [];
    const chart_energy_vs_dist = [];

    for (let i = 0; i < dsRows.length; i++) {
      const r = dsRows[i];
      const t = haveEpoch ? r.t_epoch - t0 : i;

      if (i > 0) {
        const prev = dsRows[i - 1];
        let dt = haveEpoch ? r.t_epoch - prev.t_epoch : 1;
        if (!Number.isFinite(dt) || dt <= 0) dt = 1;
        totalSeconds += dt;

        const P = Number.isFinite(prev.power_kW) ? prev.power_kW : 0;
        cum_kWh += P * (dt / 3600);
      }

      chart_time_power.push({ t_s: t, power_kW: Number.isFinite(r.power_kW) ? r.power_kW : 0 });
      chart_speed.push({ t_s: t, speed_kmh: Number.isFinite(r.speed_kmh) ? r.speed_kmh : 0 });
      chart_alt.push({ t_s: t, alt_m: Number.isFinite(r.alt) ? r.alt : null });

      const idxDist = Math.min(i, Math.max(0, cumulative(segKm).length - 1));
      chart_energy_vs_dist.push({
        i: i + 1,
        cum_km: cumulative(segKm)[idxDist] || 0,
        cum_kWh: cum_kWh,
      });
    }

    return {
      totalKm,
      totalTimeMin: totalSeconds / 60,
      totalEnergy_kWh: cum_kWh,
      chart_time_power,
      chart_speed,
      chart_alt,
      chart_energy_vs_dist,
    };
  }, [geojson, telemetryRows, downsample]);

  /* ---------- Layout 50/50 ---------- */
  const pageHeight = "calc(100vh - 96px)";

  return (
    <section
      className="w-full"
      style={{ display: "flex", gap: 12, height: pageHeight, padding: 16, boxSizing: "border-box" }}
    >
      {/* --------- IZQUIERDA (50%) --------- */}
      <aside
        className="rounded-2xl border bg-white shadow-sm"
        style={{ width: "50%", minWidth: "50%", maxWidth: "50%", display: "flex", flexDirection: "column" }}
      >
        <div className="h-12 px-4 flex items-center justify-between border-b bg-white/80 backdrop-blur">
          <div className="flex items-center gap-2">
            <Route className="w-5 h-5" />
            <h2 className="font-semibold">Telemetría</h2>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => inputRef.current?.click()}>
              <Upload className="w-4 h-4 mr-1" /> Cargar
            </Button>
            <Button variant="ghost" size="sm" onClick={clearAll} disabled={!geojson}>
              <Undo2 className="w-4 h-4 mr-1" /> Limpiar
            </Button>
          </div>
          <input ref={inputRef} type="file" accept=".json,.geojson" className="hidden" onChange={handleFile} />
        </div>

        <div className="flex-1 overflow-auto p-4">
          {fileName && (
            <div className="text-sm text-gray-500 mb-2">
              <FileJson className="inline w-4 h-4 mr-1" /> {fileName}
            </div>
          )}

          {/* Métricas (cards como en Rutas) */}
          <div className="grid grid-cols-3 gap-3 mb-4">
            <Card className="rounded-xl shadow-none border">
              <CardContent className="p-3">
                <div className="text-[11px] text-gray-500 uppercase">Distancia</div>
                <div className="text-xl font-semibold">{(totalKm ?? 0).toFixed(2)} km</div>
              </CardContent>
            </Card>
            <Card className="rounded-xl shadow-none border">
              <CardContent className="p-3">
                <div className="text-[11px] text-gray-500 uppercase">Tiempo</div>
                <div className="text-xl font-semibold">{(totalTimeMin ?? 0).toFixed(1)} min</div>
              </CardContent>
            </Card>
            <Card className="rounded-xl shadow-none border">
              <CardContent className="p-3">
                <div className="text-[11px] text-gray-500 uppercase">Energía</div>
                <div className="text-xl font-semibold">{(totalEnergy_kWh ?? 0).toFixed(3)} kWh</div>
              </CardContent>
            </Card>
          </div>

          {/* Downsample + grupo de botones estilo Rutas */}
          <div className="mb-3">
            <label className="text-sm font-medium">Downsample</label>
            <Slider value={[downsample]} onValueChange={([v]) => setDownsample(Math.max(1, Math.round(v)))} min={1} max={10} step={1} />
            <div className="text-xs text-gray-500">{downsample}x</div>
          </div>

          {/* Grupo de botones (segmentado) para tabs — MISMO estilo que en Rutas */}
          <div className="inline-flex items-center rounded-md border bg-white shadow-sm overflow-hidden mb-3">
            <Button size="sm" variant={tab === "power" ? "default" : "outline"} onClick={() => setTab("power")} className="rounded-none">
              Potencia
            </Button>
            <Button size="sm" variant={tab === "speed" ? "default" : "outline"} onClick={() => setTab("speed")} className="rounded-none -ml-px">
              Velocidad
            </Button>
            <Button size="sm" variant={tab === "alt" ? "default" : "outline"} onClick={() => setTab("alt")} className="rounded-none -ml-px">
              Altitud
            </Button>
            <Button size="sm" variant={tab === "energy" ? "default" : "outline"} onClick={() => setTab("energy")} className="rounded-none -ml-px">
              Energía
            </Button>
          </div>

          {/* Gráfica activa */}
          <Card className="rounded-2xl shadow-sm">
            <CardContent className="p-3">
              <div style={{ height: 380 }}>
                <ResponsiveContainer width="100%" height="100%">
                  {tab === "power" && (
                    <AreaChart data={chart_time_power}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="t_s" />
                      <YAxis label={{ value: "kW", angle: -90, position: "insideLeft" }} />
                      <Tooltip />
                      <Area type="monotone" dataKey="power_kW" fill="#c7d2fe" stroke="#4f46e5" />
                    </AreaChart>
                  )}
                  {tab === "speed" && (
                    <LineChart data={chart_speed}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="t_s" />
                      <YAxis label={{ value: "km/h", angle: -90, position: "insideLeft" }} />
                      <Tooltip />
                      <Line type="monotone" dataKey="speed_kmh" stroke="#10b981" dot={false} />
                    </LineChart>
                  )}
                  {tab === "alt" && (
                    <LineChart data={chart_alt}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="t_s" />
                      <YAxis label={{ value: "m", angle: -90, position: "insideLeft" }} />
                      <Tooltip />
                      <Line type="monotone" dataKey="alt_m" stroke="#f59e0b" dot={false} />
                    </LineChart>
                  )}
                  {tab === "energy" && (
                    <AreaChart data={chart_energy_vs_dist}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="cum_km" />
                      <YAxis label={{ value: "kWh", angle: -90, position: "insideLeft" }} />
                      <Tooltip />
                      <Area type="monotone" dataKey="cum_kWh" fill="#e9d5ff" stroke="#7e22ce" />
                    </AreaChart>
                  )}
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </div>
      </aside>

      {/* --------- DERECHA (50%) --------- */}
      <div
        className="rounded-2xl overflow-hidden border bg-white shadow-sm"
        style={{ width: "50%", minWidth: "50%", maxWidth: "50%", display: "flex", flexDirection: "column" }}
      >
        <div className="h-12 px-4 flex items-center justify-between border-b bg-white/80 backdrop-blur">
          <div className="flex items-center gap-2">
            <Route className="w-5 h-5" />
            <h3 className="font-semibold">Mapa</h3>
          </div>
          <div className="text-xs text-neutral-500">{geojson ? "Ruta cargada" : "Carga un JSON para pintar la ruta"}</div>
        </div>
        <div style={{ flex: 1 }}>
          <MapView vehicles={[]} routes={{}} importedGeoJSON={geojson} drawOnly={true} />
        </div>
      </div>
    </section>
  );
}