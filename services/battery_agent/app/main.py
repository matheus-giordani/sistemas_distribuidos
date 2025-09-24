from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, Optional

from fastapi import Depends, FastAPI, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BatteryMode(str, Enum):
    charge = "charge"
    discharge = "discharge"
    idle = "idle"


class BatteryMeasurement(BaseModel):
    state_of_charge_kwh: float = Field(..., ge=0)
    capacity_kwh: Optional[float] = Field(None, gt=0)


class BatteryControl(BaseModel):
    mode: BatteryMode
    power_kw: float = Field(..., ge=0)


class BatteryStatus(BaseModel):
    capacity_kwh: float
    state_of_charge_kwh: float
    min_state_of_charge_kwh: float
    max_charge_rate_kw: float
    max_discharge_rate_kw: float
    mode: BatteryMode
    power_kw: float
    last_updated: datetime


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="")

    api_key: str = Field(..., validation_alias="SERVICE_API_KEY")


settings = Settings()
API_KEY_HEADER_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=False)


def require_api_key(api_key: str = Security(api_key_header)) -> str:
    if api_key is None or api_key != settings.api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return api_key


DEFAULTS: Dict[str, float | datetime | BatteryMode] = {
    "capacity_kwh": 10.0,
    "state_of_charge_kwh": 5.0,
    "min_state_of_charge_kwh": 1.0,
    "max_charge_rate_kw": 3.0,
    "max_discharge_rate_kw": 3.0,
    "mode": BatteryMode.idle,
    "power_kw": 0.0,
    "last_updated": datetime.utcnow(),
}


state: Dict[str, float | datetime | BatteryMode] = DEFAULTS.copy()
app = FastAPI(title="Residential Battery Agent", version="1.0.0")


def clamp_state_of_charge() -> None:
    min_soc = float(state["min_state_of_charge_kwh"])
    capacity = float(state["capacity_kwh"])
    soc = float(state["state_of_charge_kwh"])
    state["state_of_charge_kwh"] = max(min(soc, capacity), min_soc)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/status", response_model=BatteryStatus)
def get_status(_: str = Depends(require_api_key)) -> BatteryStatus:
    return BatteryStatus(**state)


@app.post("/update", response_model=BatteryStatus)
def update_measurement(measurement: BatteryMeasurement, _: str = Depends(require_api_key)) -> BatteryStatus:
    if measurement.capacity_kwh:
        state["capacity_kwh"] = measurement.capacity_kwh
    state["state_of_charge_kwh"] = measurement.state_of_charge_kwh
    clamp_state_of_charge()
    state["last_updated"] = datetime.utcnow()
    return BatteryStatus(**state)


@app.post("/control", response_model=BatteryStatus)
def apply_control(control: BatteryControl, _: str = Depends(require_api_key)) -> BatteryStatus:
    state["mode"] = control.mode
    effective_power = 0.0
    soc = float(state["state_of_charge_kwh"])
    min_soc = float(state["min_state_of_charge_kwh"])
    capacity = float(state["capacity_kwh"])
    if control.mode == BatteryMode.charge:
        available_room = capacity - soc
        if available_room <= 0:
            effective_power = 0.0
        else:
            effective_power = min(control.power_kw, float(state["max_charge_rate_kw"]), available_room)
            state["state_of_charge_kwh"] = soc + effective_power
    elif control.mode == BatteryMode.discharge:
        available_energy = max(soc - min_soc, 0.0)
        if available_energy <= 0:
            effective_power = 0.0
        else:
            effective_power = min(control.power_kw, float(state["max_discharge_rate_kw"]), available_energy)
            state["state_of_charge_kwh"] = soc - effective_power
    elif control.mode == BatteryMode.idle:
        effective_power = 0.0
    else:
        raise HTTPException(status_code=400, detail="Unsupported mode")

    state["power_kw"] = effective_power
    clamp_state_of_charge()
    state["last_updated"] = datetime.utcnow()
    return BatteryStatus(**state)


__all__ = ["app"]
