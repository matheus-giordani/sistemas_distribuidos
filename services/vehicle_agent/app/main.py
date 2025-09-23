from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


class VehicleMode(str, Enum):
    charge = "charge"
    discharge = "discharge"
    idle = "idle"


class VehicleMeasurement(BaseModel):
    connected: Optional[bool] = True
    state_of_charge_kwh: float = Field(..., ge=0)
    capacity_kwh: Optional[float] = Field(None, gt=0)


class VehicleControl(BaseModel):
    mode: VehicleMode
    power_kw: float = Field(..., ge=0)


class VehicleStatus(BaseModel):
    connected: bool
    capacity_kwh: float
    state_of_charge_kwh: float
    max_charge_rate_kw: float
    max_discharge_rate_kw: float
    mode: VehicleMode
    power_kw: float
    last_updated: datetime


DEFAULTS: Dict[str, float | bool | datetime | VehicleMode] = {
    "connected": True,
    "capacity_kwh": 60.0,
    "state_of_charge_kwh": 30.0,
    "max_charge_rate_kw": 7.0,
    "max_discharge_rate_kw": 7.0,
    "mode": VehicleMode.idle,
    "power_kw": 0.0,
    "last_updated": datetime.utcnow(),
}


state: Dict[str, float | bool | datetime | VehicleMode] = DEFAULTS.copy()
app = FastAPI(title="Electric Vehicle Agent", version="1.0.0")


def clamp_state_of_charge() -> None:
    capacity = float(state["capacity_kwh"])
    soc = float(state["state_of_charge_kwh"])
    state["state_of_charge_kwh"] = min(max(soc, 0.0), capacity)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/status", response_model=VehicleStatus)
def get_status() -> VehicleStatus:
    return VehicleStatus(**state)


@app.post("/update", response_model=VehicleStatus)
def update_measurement(measurement: VehicleMeasurement) -> VehicleStatus:
    if measurement.connected is not None:
        state["connected"] = measurement.connected
    if measurement.capacity_kwh:
        state["capacity_kwh"] = measurement.capacity_kwh
    state["state_of_charge_kwh"] = measurement.state_of_charge_kwh
    clamp_state_of_charge()
    state["last_updated"] = datetime.utcnow()
    return VehicleStatus(**state)


@app.post("/control", response_model=VehicleStatus)
def apply_control(control: VehicleControl) -> VehicleStatus:
    if not state["connected"] and control.mode != VehicleMode.idle:
        raise HTTPException(status_code=400, detail="Vehicle not connected")

    state["mode"] = control.mode
    effective_power = 0.0
    soc = float(state["state_of_charge_kwh"])
    capacity = float(state["capacity_kwh"])

    if control.mode == VehicleMode.charge:
        available_room = capacity - soc
        if available_room > 0:
            effective_power = min(control.power_kw, float(state["max_charge_rate_kw"]), available_room)
            state["state_of_charge_kwh"] = soc + effective_power
    elif control.mode == VehicleMode.discharge:
        available_energy = soc
        if available_energy > 0:
            effective_power = min(control.power_kw, float(state["max_discharge_rate_kw"]), available_energy)
            state["state_of_charge_kwh"] = soc - effective_power
    elif control.mode == VehicleMode.idle:
        effective_power = 0.0
    else:
        raise HTTPException(status_code=400, detail="Unsupported mode")

    state["power_kw"] = effective_power
    clamp_state_of_charge()
    state["last_updated"] = datetime.utcnow()
    return VehicleStatus(**state)


__all__ = ["app"]
