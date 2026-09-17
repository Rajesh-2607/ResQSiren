import uuid
from datetime import datetime

from resq_shared.db import Base
from sqlalchemy import JSON, DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

SCHEMA = "dispatch"


def new_id() -> str:
    return str(uuid.uuid4())


class Call(Base):
    __tablename__ = "calls"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    caller_name: Mapped[str] = mapped_column(String)
    phone: Mapped[str] = mapped_column(String)
    symptom: Mapped[str] = mapped_column(String)
    severity: Mapped[str] = mapped_column(String)
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)
    attendant_consent: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Dispatch(Base):
    __tablename__ = "dispatches"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    call_id: Mapped[str] = mapped_column(ForeignKey(f"{SCHEMA}.calls.id"))
    ambulance_id: Mapped[str] = mapped_column(String)
    hospital_id: Mapped[str] = mapped_column(String)
    severity: Mapped[str] = mapped_column(String)
    origin: Mapped[dict] = mapped_column(JSON)
    destination: Mapped[dict] = mapped_column(JSON)
    route: Mapped[dict] = mapped_column(JSON)
    eta_seconds: Mapped[float] = mapped_column(Float)
    signature: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="EN_ROUTE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
