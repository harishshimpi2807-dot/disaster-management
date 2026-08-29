"use client";

import dynamic from "next/dynamic";

const MapView = dynamic(() => import("./MapView"), {
  ssr: false,
  loading: () => <div className="loading">Loading geospatial canvas…</div>,
});

export default function MapPage() {
  return <MapView />;
}
