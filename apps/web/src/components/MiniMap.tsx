"use client";

import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

type Props = {
  geojson?: GeoJSON.GeoJSON | null;
  center?: [number, number];
  zoom?: number;
  height?: number;
};

export default function MiniMap({ geojson, center = [73.52, 17.53], zoom = 8, height = 240 }: Props) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!ref.current) return;
    const map = new maplibregl.Map({
      container: ref.current,
      style: {
        version: 8,
        sources: {
          osm: { type: "raster", tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"], tileSize: 256, attribution: "© OpenStreetMap" },
        },
        layers: [{ id: "osm", type: "raster", source: "osm" }],
      },
      center,
      zoom,
    });
    map.on("load", () => {
      if (!geojson) return;
      map.addSource("focus", { type: "geojson", data: geojson });
      map.addLayer({ id: "focus-fill", type: "fill", source: "focus", filter: ["==", "$type", "Polygon"], paint: { "fill-color": "#cbb992", "fill-opacity": 0.28 } });
      map.addLayer({ id: "focus-line", type: "line", source: "focus", paint: { "line-color": "#cbb992", "line-width": 2 } });
      map.addLayer({ id: "focus-pt", type: "circle", source: "focus", filter: ["==", "$type", "Point"], paint: { "circle-radius": 6, "circle-color": "#4a9b8c" } });
    });
    return () => map.remove();
  }, [geojson, center, zoom]);

  return <div ref={ref} className="map-el" style={{ height }} role="img" aria-label="Location map" />;
}
