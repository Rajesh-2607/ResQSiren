import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { useEffect, useRef } from "react";
import type { GeoJSONLineString } from "../lib/types";

// Vite doesn't resolve Leaflet's default marker image URLs from the CSS
// bundle — point them at the CDN-hosted originals instead of shipping a
// broken icon.
const defaultIcon = L.icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

const ambulanceIcon = L.divIcon({
  className: "",
  html: '<div style="font-size:26px;line-height:1;transform:translate(-50%,-100%)">🚑</div>',
  iconSize: [26, 26],
});

interface LiveMapProps {
  origin: [number, number]; // [lat, lng]
  destination: [number, number]; // [lat, lng]
  routeGeometry: GeoJSONLineString | null;
  ambulancePosition: [number, number] | null; // [lat, lng]
}

export function LiveMap({ origin, destination, routeGeometry, ambulancePosition }: LiveMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const ambulanceMarkerRef = useRef<L.Marker | null>(null);
  const routeLayerRef = useRef<L.Polyline | null>(null);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = L.map(containerRef.current).setView(origin, 13);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19,
    }).addTo(map);

    L.marker(origin, { icon: defaultIcon }).addTo(map).bindPopup("Pickup");
    L.marker(destination, { icon: defaultIcon }).addTo(map).bindPopup("Hospital");

    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    if (routeLayerRef.current) {
      routeLayerRef.current.remove();
      routeLayerRef.current = null;
    }
    if (routeGeometry) {
      const latlngs = routeGeometry.coordinates.map(([lng, lat]) => [lat, lng] as [number, number]);
      const line = L.polyline(latlngs, { color: "#0d8f88", weight: 4 }).addTo(map);
      routeLayerRef.current = line;
      map.fitBounds(line.getBounds(), { padding: [24, 24] });
    }
  }, [routeGeometry]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ambulancePosition) return;

    if (!ambulanceMarkerRef.current) {
      ambulanceMarkerRef.current = L.marker(ambulancePosition, { icon: ambulanceIcon }).addTo(map);
    } else {
      ambulanceMarkerRef.current.setLatLng(ambulancePosition);
    }
  }, [ambulancePosition]);

  return (
    <div className="overflow-hidden rounded-lg border border-slate-200">
      <div ref={containerRef} style={{ height: 320, width: "100%" }} />
      {!ambulancePosition && (
        <p className="border-t border-slate-200 bg-slate-50 px-3 py-1.5 text-xs text-slate-500">
          Waiting for ambulance GPS…
        </p>
      )}
    </div>
  );
}
