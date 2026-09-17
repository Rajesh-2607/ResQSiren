import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { useEffect, useRef } from 'react'
import type { Ambulance, Dispatch, Hospital, Junction } from '../lib/types'
import { SEVERITY_COLOR } from '../lib/types'

const CENTER: [number, number] = [13.045, 80.235]

function severityIcon(color: string) {
  return L.divIcon({
    className: '',
    html: `<div style="width:14px;height:14px;border-radius:50%;background:${color};border:2px solid white;box-shadow:0 0 0 1px rgba(0,0,0,.3)"></div>`,
    iconSize: [14, 14],
  })
}

const hospitalIcon = L.divIcon({
  className: '',
  html: `<div style="width:12px;height:12px;background:#2563eb;border:2px solid white;box-shadow:0 0 0 1px rgba(0,0,0,.3)"></div>`,
  iconSize: [12, 12],
})

const junctionIcon = L.divIcon({
  className: '',
  html: `<div style="width:10px;height:10px;transform:rotate(45deg);background:#111827;border:2px solid white"></div>`,
  iconSize: [10, 10],
})

interface Props {
  hospitals: Hospital[]
  ambulances: Ambulance[]
  junctions: Junction[]
  dispatches: Dispatch[]
}

export default function LiveMap({ hospitals, ambulances, junctions, dispatches }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<L.Map | null>(null)
  const layerRef = useRef<L.LayerGroup | null>(null)

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return
    const map = L.map(containerRef.current).setView(CENTER, 12)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
    }).addTo(map)
    mapRef.current = map
    layerRef.current = L.layerGroup().addTo(map)
    return () => {
      map.remove()
      mapRef.current = null
    }
  }, [])

  useEffect(() => {
    const layer = layerRef.current
    if (!layer) return
    layer.clearLayers()

    for (const h of hospitals) {
      L.marker([h.lat, h.lng], { icon: hospitalIcon }).addTo(layer).bindTooltip(h.name)
    }
    for (const j of junctions) {
      L.marker([j.lat, j.lng], { icon: junctionIcon }).addTo(layer).bindTooltip(`Junction: ${j.name}`)
    }
    for (const a of ambulances) {
      L.marker([a.lat, a.lng], { icon: severityIcon('#6b7280') }).addTo(layer).bindTooltip(a.callsign)
    }
    for (const d of dispatches) {
      const color = SEVERITY_COLOR[d.severity]
      const points = d.route.path.map((p) => [p.lat, p.lng] as [number, number])
      L.polyline(points, { color, weight: 4, opacity: 0.8 }).addTo(layer)
      L.marker([d.origin.lat, d.origin.lng], { icon: severityIcon(color) })
        .addTo(layer)
        .bindTooltip(`Dispatch ${d.id.slice(0, 8)} (${d.severity})`)
    }
  }, [hospitals, ambulances, junctions, dispatches])

  return <div ref={containerRef} className="h-full w-full rounded-lg overflow-hidden" />
}
