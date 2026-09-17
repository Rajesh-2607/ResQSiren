import { useEffect, useState } from 'react'
import CallIntake from './components/CallIntake'
import CallsPanel from './components/CallsPanel'
import JunctionArbitration from './components/JunctionArbitration'
import LiveMap from './components/LiveMap'
import NotificationsFeed from './components/NotificationsFeed'
import SignalLog from './components/SignalLog'
import { dispatchApi, routingApi } from './lib/api'
import type { Ambulance, Call, Dispatch, Hospital, Junction } from './lib/types'

export default function App() {
  const [hospitals, setHospitals] = useState<Hospital[]>([])
  const [ambulances, setAmbulances] = useState<Ambulance[]>([])
  const [junctions, setJunctions] = useState<Junction[]>([])
  const [calls, setCalls] = useState<Call[]>([])
  const [dispatches, setDispatches] = useState<Dispatch[]>([])

  useEffect(() => {
    routingApi.hospitals().then((v) => setHospitals(v as Hospital[]))
    routingApi.ambulances().then((v) => setAmbulances(v as Ambulance[]))
    routingApi.junctions().then((v) => setJunctions(v as Junction[]))
    refreshCalls()
    refreshDispatches()
  }, [])

  function refreshCalls() {
    dispatchApi.listCalls().then((v) => setCalls(v as Call[]))
  }

  function refreshDispatches() {
    dispatchApi.listDispatches().then((v) => setDispatches(v as Dispatch[]))
  }

  return (
    <div className="min-h-screen">
      <header className="bg-gray-900 text-white px-4 py-3">
        <h1 className="font-semibold">resQ Siren - Dispatcher Console</h1>
      </header>

      <main className="grid grid-cols-1 lg:grid-cols-3 gap-4 p-4">
        <div className="space-y-4">
          <CallIntake onCreated={() => refreshCalls()} />
          <CallsPanel
            calls={calls}
            dispatches={dispatches}
            onDispatched={() => {
              refreshDispatches()
              refreshCalls()
            }}
          />
        </div>

        <div className="lg:col-span-2 space-y-4">
          <div className="bg-white rounded-lg shadow-sm h-96">
            <LiveMap hospitals={hospitals} ambulances={ambulances} junctions={junctions} dispatches={dispatches} />
          </div>
          <JunctionArbitration junctions={junctions} ambulances={ambulances} />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <SignalLog />
            <NotificationsFeed />
          </div>
        </div>
      </main>
    </div>
  )
}
