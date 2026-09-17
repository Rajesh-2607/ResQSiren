import { useEffect, useState } from 'react'
import ArrivedList from './components/ArrivedList'
import HospitalPicker from './components/HospitalPicker'
import IncomingCard from './components/IncomingCard'
import NotificationsFeed from './components/NotificationsFeed'
import { dispatchApi, routingApi } from './lib/api'
import type { Call, Dispatch, Hospital } from './lib/types'

const STORAGE_KEY = 'resq.hospital-dashboard.selectedHospitalId'

function loadStoredHospitalId(): string {
  try {
    return localStorage.getItem(STORAGE_KEY) ?? ''
  } catch {
    return ''
  }
}

function storeHospitalId(id: string) {
  try {
    localStorage.setItem(STORAGE_KEY, id)
  } catch {
    // storage blocked (private mode, etc.) - selection just won't persist
  }
}

export default function App() {
  const [hospitals, setHospitals] = useState<Hospital[]>([])
  const [selectedId, setSelectedId] = useState(loadStoredHospitalId)
  const [dispatches, setDispatches] = useState<Dispatch[]>([])
  const [calls, setCalls] = useState<Call[]>([])

  useEffect(() => {
    routingApi.hospitals().then((v) => {
      const list = v as Hospital[]
      setHospitals(list)
      setSelectedId((prev) => prev || list[0]?.id || '')
    })
  }, [])

  useEffect(() => {
    function refresh() {
      dispatchApi.listDispatches().then((v) => setDispatches(v as Dispatch[]))
      dispatchApi.listCalls().then((v) => setCalls(v as Call[]))
    }
    refresh()
    const interval = setInterval(refresh, 4000)
    return () => clearInterval(interval)
  }, [])

  function handleSelect(id: string) {
    setSelectedId(id)
    storeHospitalId(id)
  }

  const callsById = new Map(calls.map((c) => [c.id, c]))
  const forThisHospital = dispatches.filter((d) => d.hospital_id === selectedId)
  const incoming = forThisHospital.filter((d) => d.status === 'EN_ROUTE')
  const arrived = forThisHospital.filter((d) => d.status === 'ARRIVED')

  return (
    <div className="min-h-screen">
      <header className="bg-gray-900 text-white px-4 py-3">
        <h1 className="font-semibold">resQ Siren - Hospital ER Dashboard</h1>
      </header>

      <main className="grid grid-cols-1 lg:grid-cols-3 gap-4 p-4">
        <div className="lg:col-span-2 space-y-4">
          <HospitalPicker hospitals={hospitals} selectedId={selectedId} onChange={handleSelect} />

          <div>
            <h2 className="font-semibold text-gray-900 mb-2">Incoming ambulances</h2>
            {incoming.length === 0 ? (
              <div className="bg-white rounded-lg p-4 shadow-sm text-sm text-gray-500">
                No incoming ambulances
              </div>
            ) : (
              <div className="space-y-3">
                {incoming.map((d) => (
                  <IncomingCard key={d.id} dispatch={d} call={callsById.get(d.call_id)} />
                ))}
              </div>
            )}
          </div>

          <ArrivedList dispatches={arrived} />
        </div>

        <div className="space-y-4">
          <NotificationsFeed />
        </div>
      </main>
    </div>
  )
}
