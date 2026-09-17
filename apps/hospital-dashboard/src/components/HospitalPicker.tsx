import type { Hospital } from '../lib/types'

interface Props {
  hospitals: Hospital[]
  selectedId: string
  onChange: (id: string) => void
}

export default function HospitalPicker({ hospitals, selectedId, onChange }: Props) {
  return (
    <div className="bg-white rounded-lg p-3 shadow-sm flex items-center gap-2 text-sm">
      <label className="text-gray-500">Viewing as</label>
      <select
        value={selectedId}
        onChange={(e) => onChange(e.target.value)}
        className="rounded border border-gray-300 px-2 py-1"
      >
        {hospitals.map((h) => (
          <option key={h.id} value={h.id}>
            {h.name}
          </option>
        ))}
      </select>
    </div>
  )
}
