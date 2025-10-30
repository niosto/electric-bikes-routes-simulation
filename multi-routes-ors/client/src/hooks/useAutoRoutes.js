import { useEffect, useMemo, useRef, useState } from "react";
import * as api from "../services/api.js";

export default function useAutoRoutes({ vehicles, enabled = true }) {
  const [routes, setRoutes] = useState({});
  const [selectedAlt, setSelectedAlt] = useState({});
  const [options, setOptions] = useState({
    profile: "driving",
    alternatives: false, // fijo en tu caso
    steps: true,        // fijo en tu caso
    geometries: "geojson",
    alt_count: 1,
    alt_share: 0.6,
    alt_weight: 1.4,
  });

  const debounceTimer = useRef(null);
  const abortRef = useRef(null);
  const genRef = useRef(0); // versión para invalidar respuestas viejas

  const cancelPending = () => {
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
      debounceTimer.current = null;
    }
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
    genRef.current += 1; // invalida cualquier respuesta en vuelo
  };

  const cleanNow = (vlist) => {
    setRoutes(prev => {
      const next = { ...prev };
      vlist.forEach(v => {
        if (v.waypoints.length < 2 && next[v.id]) delete next[v.id];
      });
      return next;
    });
    setSelectedAlt(prev => {
      const n = { ...prev };
      vlist.forEach(v => {
        if (v.waypoints.length < 2 && n[v.id] !== undefined) delete n[v.id];
      });
      return n;
    });
  };

  const recompute = async (vlist) => {
    if (!enabled) return;

    const ready = vlist
      .filter(v => v.waypoints.length >= 2)
      .map(v => ({ vehicle_id: v.id, waypoints: v.waypoints }));

    if (ready.length === 0) return;

    // preparar cancelación
    cancelPending();
    const localGen = ++genRef.current;
    const ctrl = new AbortController();
    abortRef.current = ctrl;

    // Forzar opciones a una sola ruta sin pasos
    const safeOptions = { ...options, alternatives: false, steps: true };

    const data = await api.postRoutesJSON(
      { options: safeOptions, vehicles: ready },
      { signal: ctrl.signal }
    ).catch((err) => {
      if (err?.name === "AbortError") return null;
      throw err;
    });

    if (!data) return;                       // abortado
    if (localGen !== genRef.current) return; // respuesta vieja

    const map = {};
    (data.routes || []).forEach(r => { map[r.vehicle_id] = r; });

    setRoutes(prev => {
      const keep = {};
      ready.forEach(r => { if (prev[r.vehicle_id]) keep[r.vehicle_id] = prev[r.vehicle_id]; });
      return { ...keep, ...map };
    });

    setSelectedAlt(prev => {
      const next = { ...prev };
      ready.forEach(r => { if (next[r.vehicle_id] == null) next[r.vehicle_id] = 0; });
      return next;
    });
  };

  useEffect(() => {
    if (!enabled) {
      cancelPending();
      setRoutes({});
      setSelectedAlt({});
      return;
    }
    cleanNow(vehicles);
    if (debounceTimer.current) clearTimeout(debounceTimer.current);
    debounceTimer.current = setTimeout(() => recompute(vehicles), 250);
    return () => clearTimeout(debounceTimer.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [vehicles, options, enabled]);

  const computeRoutesManual = () => {
    if (enabled) { cleanNow(vehicles); recompute(vehicles); }
  };

  const totalSummary = useMemo(() => {
    const entries = Object.values(routes);
    const dist = entries.reduce((s, r) => s + (r?.summary?.distance || 0), 0);
    const dur  = entries.reduce((s, r) => s + (r?.summary?.duration || 0), 0);
    return {
      distance_km: (dist / 1000).toFixed(2),
      duration_min: (dur / 60).toFixed(1)
    };
  }, [routes]);

  return { options, setOptions, routes, selectedAlt, setSelectedAlt, totalSummary, computeRoutesManual };
}