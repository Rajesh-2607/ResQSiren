import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { useEffect, useRef } from 'react'
import type { Dispatch } from '../lib/types'
import { SEVERITY_COLOR } from '../lib/types'

function dotIcon(color: string) {
  return L.divIcon({
    className: '',
    html: `<div style="width:14px;height:14px;border-radius:50%;background:${color};border:2px solid white;box-shadow:0 0 0 1px rgba(0,0,0,.3)"></div>`,
    iconSize: [14, 14],
  })
}

const destinationIcon = L.divIcon({
  className: '',
  html: `<div style="width:12px;height:12px;background:#2563eb;border:2px solid white;box-shadow:0 0 0 1px rgba(0,0,0,.3)"></div>`,
  iconSize: [12, 12],
})

interface Props {
  dispatch: Dispatch
}

export default function RouteMap({ dispatch }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<L.Map | null>(null)
  const layerRef = useRef<L.LayerGroup | null>(null)

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return
    const map = L.map(containerRef.current).setView([dispatch.origin.lat, dispatch.origin.lng], 13)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
    }).addTo(map)
    mapRef.current = map
    layerRef.current = L.layerGroup().addTo(map)
    return () => {
      map.remove()
      mapRef.current = null
    }
  }, [dispatch.origin.lat, dispatch.origin.lng])

  useEffect(() => {
    const layer = layerRef.current
    const map = mapRef.current
    if (!layer || !map) return
    layer.clearLayers()

    const color = SEVERITY_COLOR[dispatch.severity]
    const points = dispatch.route.path.map((p) => [p.lat, p.lng] as [number, number])
    const line = L.polyline(points, { color, weight: 4, opacity: 0.8 }).addTo(layer)
    L.marker([dispatch.origin.lat, dispatch.origin.lng], { icon: dotIcon(color) })
      .addTo(layer)
      .bindTooltip('Pickup')
    L.marker([dispatch.destination.lat, dispatch.destination.lng], { icon: destinationIcon })
      .addTo(layer)
      .bindTooltip('Hospital')

    if (points.length > 1) {
      map.fitBounds(line.getBounds(), { padding: [24, 24] })
    }
  }, [dispatch])

  return <div ref={containerRef} className="h-full w-full rounded-lg overflow-hidden" />
}
