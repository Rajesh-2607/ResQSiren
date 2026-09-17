import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.models import Severity


class LoginRequest(BaseModel):
    username: str
    role: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CallCreate(BaseModel):
    location: str
    originLat: float
    originLng: float
    hospitalId: str
    severity: Severity
    notes: str | None = None


class CallOut(BaseModel):
    id: uuid.UUID
    location: str
    originLat: float
    originLng: float
    hospitalId: str
    severity: Severity
    notes: str | None
    createdAt: datetime

    model_config = {"populate_by_name": True}


class DispatchCreate(BaseModel):
    ambulanceId: str
    severity: Severity
    hospitalId: str
    callId: uuid.UUID | None = None
    # Only needed if callId isn't set (no call to pull pickup coordinates from).
    originLat: float | None = None
    originLng: float | None = None
    # Optional: send a real SMS alert (e.g. to the receiving hospital or
    # traffic control room) via Twilio when this dispatch is created.
    notifyPhone: str | None = None


class DispatchOut(BaseModel):
    id: uuid.UUID
    ambulanceId: str
    severity: Severity
    hospitalId: str
    status: str
    hospitalResponse: str = "PENDING"
    createdAt: datetime
    route: dict | None = None
    patientSummary: str | None = None


class PreemptRequest(BaseModel):
    dispatchId: uuid.UUID
    etaSeconds: int


class PreemptResponse(BaseModel):
    junctionId: str
    winnerDispatchId: uuid.UUID
    reason: str


class TripOut(BaseModel):
    id: uuid.UUID
    dispatchId: uuid.UUID
    junctionsCleared: list
    arbitrationsInvolved: list
    declinedHospitalIds: list
    route: dict | None
    startedAt: datetime
    pickedUpAt: datetime | None
    completedAt: datetime | None


class HospitalResponseRequest(BaseModel):
    decision: Literal["ACCEPT", "DECLINE"]


class LocationUpdate(BaseModel):
    lat: float
    lng: float


class LocationOut(BaseModel):
    lat: float
    lng: float
    updatedAt: str


class EmergencyRequest(BaseModel):
    symptom: Literal["CARDIAC_OR_UNCONSCIOUS", "SEVERE_BLEEDING_OR_FRACTURE", "STABLE_NON_URGENT"]
    lat: float
    lng: float
    notes: str | None = None


class EmergencyResponseOut(BaseModel):
    callId: uuid.UUID
    dispatchId: uuid.UUID
    ambulanceId: str
    hospitalId: str
    severity: Severity
    route: dict | None
    patientSummary: str | None


class EmergencyStatusOut(BaseModel):
    dispatchId: uuid.UUID
    ambulanceId: str
    hospitalId: str
    severity: Severity
    status: str
    hospitalResponse: str
    route: dict | None
