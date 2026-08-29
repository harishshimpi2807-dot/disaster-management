"use client";

import { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { api } from "@/lib/api";
import { labelize } from "@/lib/format";

const COLORS: Record<string, string> = {
  disasters: "#cbb992",
  damage: "#d46a48",
  claims: "#c9a227",
  fund_requests: "#7d93a3",
  allocations: "#8aa0ae",
  anomalies: "#e07a5f",
  recovery: "#4a9b8c",
  inspections: "#7a9a6e",
  duplicates: "#c45c3a",
};

type Layers = Record<string, GeoJSON.FeatureCollection | { open_count?: number; features?: GeoJSON.Feature[] }>;

export default function MapView() {
  const ref = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const [layers, setLayers] = useState<Layers>({});
  const [disasters, setDisasters] = useState<{ id: number; name: string }[]>([]);
  const [disasterId, setDisasterId] = useState("");
  const [on, setOn] = useState<Record<string, boolean>>({
    disasters: true,
    damage: true,
    claims: true,
    fund_requests: true,
    allocations: true,
    anomalies: true,
    recovery: true,
    inspections: true,
    duplicates: true,
  });
  const [sel, setSel] = useState<GeoJSON.GeoJsonProperties | null>(null);
  const [q, setQ] = useState("");
  const [err, setErr] = useState("");

  function load(id?: string) {
    const p = id ? `?disaster_id=${id}` : "";
    api<Layers>(`/api/v1/gis/layers${p}`).then(setLayers).catch((e) => setErr(e.message));
  }

  useEffect(() => {
    load();
    api<{ id: number; name: string }[]>("/api/v1/disasters").then(setDisasters);
  }, []);

  useEffect(() => {
    if (!ref.current || mapRef.current) return;
    const map = new maplibregl.Map({
      container: ref.current,
      style: {
        version: 8,
        sources: {
          osm: { type: "raster", tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"], tileSize: 256, attribution: "© OpenStreetMap" },
        },
        layers: [{ id: "osm", type: "raster", source: "osm" }],
      },
      center: [78.9, 21.1],
      zoom: 4.4,
    });
    map.addControl(new maplibregl.NavigationControl(), "top-left");
    map.on("load", () => {
      mapRef.current = map;
      paint(map, layers, on, setSel);
    });
    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map?.isStyleLoaded()) return;
    paint(map, layers, on, setSel);
  }, [layers, on]);

  function search() {
    const map = mapRef.current;
    if (!map || !q.trim()) return;
    for (const fc of Object.values(layers)) {
      if (!fc || !("features" in fc) || !fc.features) continue;
      const hit = fc.features.find((f) => JSON.stringify(f.properties).toLowerCase().includes(q.toLowerCase()));
      if (hit?.geometry && hit.geometry.type !== "GeometryCollection") {
        const c = centroid(hit.geometry);
        if (c) {
          map.flyTo({ center: c, zoom: 9 });
          setSel(hit.properties);
          return;
        }
      }
    }
  }

  return (
    <div className="map-wrap">
      <div ref={ref} className="map-el" role="application" aria-label="Geospatial intelligence map" />
      <aside className="side">
        <h2>Layers</h2>
        <p className="lede" style={{ marginBottom: 12 }}>
          Filter by disaster, toggle layers, search, then click a feature. Inspection and anomaly points cluster at country scale.
        </p>
        <label className="field">
          Disaster filter
          <select
            value={disasterId}
            onChange={(e) => {
              setDisasterId(e.target.value);
              load(e.target.value);
            }}
          >
            <option value="">All events</option>
            {disasters.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>
        </label>
        <div className="row" style={{ margin: "12px 0" }}>
          <label className="field">
            Search map entities
            <input value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => e.key === "Enter" && search()} />
          </label>
          <button className="btn ghost" onClick={search}>
            Find
          </button>
        </div>
        {err ? <div className="error">{err}</div> : null}
        <div className="layers">
          {Object.keys(on).map((k) => (
            <label key={k}>
              <input type="checkbox" checked={on[k]} onChange={() => setOn((s) => ({ ...s, [k]: !s[k] }))} />
              <span style={{ width: 10, height: 10, background: COLORS[k], display: "inline-block" }} />
              {labelize(k)}
            </label>
          ))}
        </div>
        {sel ? (
          <div className="panel">
            <h2>Selection</h2>
            <dl>
              {Object.entries(sel).map(([k, v]) => (
                <div key={k} style={{ display: "flex", justifyContent: "space-between", gap: 8, fontSize: 13, padding: "4px 0" }}>
                  <dt style={{ color: "var(--muted)" }}>{labelize(k)}</dt>
                  <dd className="mono">{String(v)}</dd>
                </div>
              ))}
            </dl>
            {typeof sel.href === "string" ? (
              <a className="btn" href={sel.href}>
                Open record
              </a>
            ) : null}
          </div>
        ) : (
          <div className="empty">No feature selected. Use layers and click a polygon, line, or point.</div>
        )}
      </aside>
    </div>
  );
}

function paint(map: maplibregl.Map, layers: Layers, on: Record<string, boolean>, setSel: (p: GeoJSON.GeoJsonProperties) => void) {
  for (const key of Object.keys(COLORS)) {
    const src = `src-${key}`;
    for (const id of [`fill-${key}`, `line-${key}`, `pt-${key}`, `cluster-${key}`, `cluster-count-${key}`]) {
      if (map.getLayer(id)) map.removeLayer(id);
    }
    if (map.getSource(src)) map.removeSource(src);
    const fc = layers[key];
    if (!on[key] || !fc || !("features" in fc) || !fc.features) continue;
    const cluster = key === "inspections" || key === "anomalies";
    map.addSource(src, { type: "geojson", data: fc as GeoJSON.FeatureCollection, cluster, clusterMaxZoom: 8, clusterRadius: 42 });
    map.addLayer({
      id: `fill-${key}`,
      type: "fill",
      source: src,
      filter: ["==", "$type", "Polygon"],
      paint: { "fill-color": COLORS[key], "fill-opacity": 0.28 },
    });
    map.addLayer({
      id: `line-${key}`,
      type: "line",
      source: src,
      paint: { "line-color": COLORS[key], "line-width": key === "duplicates" ? 3 : 1.6 },
    });
    if (cluster) {
      map.addLayer({
        id: `cluster-${key}`,
        type: "circle",
        source: src,
        filter: ["has", "point_count"],
        paint: { "circle-color": COLORS[key], "circle-radius": 16, "circle-opacity": 0.85 },
      });
      map.addLayer({
        id: `cluster-count-${key}`,
        type: "symbol",
        source: src,
        filter: ["has", "point_count"],
        layout: { "text-field": "{point_count_abbreviated}", "text-size": 11 },
        paint: { "text-color": "#11140f" },
      });
    }
    map.addLayer({
      id: `pt-${key}`,
      type: "circle",
      source: src,
      filter: cluster ? ["all", ["==", "$type", "Point"], ["!", ["has", "point_count"]]] : ["==", "$type", "Point"],
      paint: { "circle-color": COLORS[key], "circle-radius": 6, "circle-stroke-width": 1, "circle-stroke-color": "#11140f" },
    });
    const pick = (e: maplibregl.MapLayerMouseEvent) => {
      if (e.features?.[0]) setSel(e.features[0].properties);
    };
    map.on("click", `fill-${key}`, pick);
    map.on("click", `pt-${key}`, pick);
    map.on("click", `line-${key}`, pick);
  }
}

function centroid(g: GeoJSON.Geometry): [number, number] | null {
  const coords: number[][] = [];
  JSON.stringify(g, (_, v) => {
    if (Array.isArray(v) && typeof v[0] === "number" && typeof v[1] === "number") coords.push(v as number[]);
    return v;
  });
  if (!coords.length) return null;
  return [coords.reduce((s, c) => s + c[0], 0) / coords.length, coords.reduce((s, c) => s + c[1], 0) / coords.length];
}
