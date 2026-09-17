import type { Severity } from './types'

/**
 * Deterministic, client-side stand-in for a real ABHA-backed patient
 * summary. No LLM call and no health record access in this build — this
 * exists only to show hospital staff what an advance alert would look like.
 */
export function mockPatientSummary(symptom: string, severity: Severity, attendantConsent: boolean): string {
  const readableSymptom = symptom.replaceAll('_', ' ')
  const consentText = attendantConsent ? 'yes' : 'no'
  return `Suspected ${readableSymptom}. Triage: ${severity}. Attendant consent for ABHA record pull: ${consentText}.`
}
