from resq_shared.severity import Severity
from pydantic import BaseModel


class LatLng(BaseModel):
    lat: float
    lng: float


class CallCreateRequest(BaseModel):
    caller_name: str
    phone: str
    symptom: str
    location: LatLng
    attendant_consent: bool = False


class CallResponse(BaseModel):
    id: str
    caller_name: str
    phone: str
    symptom: str
    severity: Severity
    location: LatLng
    attendant_consent: bool

    class Config:
        from_attributes = True


class DispatchCreateRequest(BaseModel):
    call_id: str
    hospital_id: str | None = None  # omit to auto-select nearest


class ApproachingRequest(BaseModel):
    junction_id: str
    eta_seconds: float


class DispatchResponse(BaseModel):
    id: str
    call_id: str
    ambulance_id: str
    hospital_id: str
    severity: Severity
    origin: LatLng
    destination: LatLng
    route: dict
    eta_seconds: float
    status: str
    signature: str

    class Config:
        from_attributes = True
