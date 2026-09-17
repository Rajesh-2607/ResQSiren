import { useState, type FormEvent } from 'react'
import { ApiError, dispatchApi } from '../lib/api'
import type { Call } from '../lib/types'
import { SYMPTOMS } from '../lib/types'

const DEFAULT_LOCATION = { lat: 13.0604, lng: 80.2496 }

interface Props {
  onCreated: (call: Call) => void
}

export default function CallIntake({ onCreated }: Props) {
  const [callerName, setCallerName] = useState('')
  const [phone, setPhone] = useState('')
  const [symptom, setSymptom] = useState(SYMPTOMS[0].value)
  const [consent, setConsent] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      const call = (await dispatchApi.createCall({
        caller_name: callerName,
        phone,
        symptom,
        location: DEFAULT_LOCATION,
        attendant_consent: consent,
      })) as Call
      onCreated(call)
      setCallerName('')
      setPhone('')
      setConsent(false)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to create call')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3 bg-white rounded-lg p-4 shadow-sm">
      <h2 className="font-semibold text-gray-900">Call intake</h2>
      <input
        required
        placeholder="Caller name"
        value={callerName}
        onChange={(e) => setCallerName(e.target.value)}
        className="w-full rounded border border-gray-300 px-2 py-1.5 text-sm"
      />
      <input
        required
        placeholder="Phone"
        value={phone}
        onChange={(e) => setPhone(e.target.value)}
        className="w-full rounded border border-gray-300 px-2 py-1.5 text-sm"
      />
      <select
        value={symptom}
        onChange={(e) => setSymptom(e.target.value)}
        className="w-full rounded border border-gray-300 px-2 py-1.5 text-sm"
      >
        {SYMPTOMS.map((s) => (
          <option key={s.value} value={s.value}>
            {s.label}
          </option>
        ))}
      </select>
      <label className="flex items-center gap-2 text-sm text-gray-700">
        <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} />
        Attendant consent given (ABHA record access)
      </label>
      {error && <p className="text-sm text-red-600">{error}</p>}
      <button
        type="submit"
        disabled={submitting}
        className="w-full rounded bg-red-600 py-1.5 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
      >
        {submitting ? 'Logging call...' : 'Log call & assign severity'}
      </button>
    </form>
  )
}
