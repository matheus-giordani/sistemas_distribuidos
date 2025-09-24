from __future__ import annotations

import asyncio
from enum import Enum
from typing import Optional

import httpx
from fastapi import Depends, FastAPI, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="")

    solar_agent_url: str = Field(
        default="http://solar-agent:8001", validation_alias="SOLAR_AGENT_URL"
    )
    battery_agent_url: str = Field(
        default="http://battery-agent:8002", validation_alias="BATTERY_AGENT_URL"
    )
    vehicle_agent_url: str = Field(
        default="http://vehicle-agent:8003", validation_alias="VEHICLE_AGENT_URL"
    )
    load_agent_url: str = Field(
        default="http://load-agent:8004", validation_alias="LOAD_AGENT_URL"
    )
    http_timeout: float = Field(default=5.0, validation_alias="HTTP_CLIENT_TIMEOUT")
    api_key: str = Field(..., validation_alias="SERVICE_API_KEY")


settings = Settings()
app = FastAPI(title="Central Coordination Agent", version="1.0.0")
API_KEY_HEADER_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=False)


def require_api_key(api_key: str = Security(api_key_header)) -> str:
    if api_key is None or api_key != settings.api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return api_key


class SolarMeasurement(BaseModel):
    production_kw: float = Field(..., ge=0)


class LoadMeasurement(BaseModel):
    critical_load_kw: float = Field(..., ge=0)
    flexible_load_kw: float = Field(..., ge=0)


class BatteryMeasurement(BaseModel):
    state_of_charge_kwh: float = Field(..., ge=0)
    capacity_kwh: Optional[float] = Field(None, gt=0)


class VehicleMeasurement(BaseModel):
    connected: Optional[bool] = None
    state_of_charge_kwh: float = Field(..., ge=0)
    capacity_kwh: Optional[float] = Field(None, gt=0)


class CoordinationPayload(BaseModel):
    solar: Optional[SolarMeasurement] = None
    load: Optional[LoadMeasurement] = None
    battery: Optional[BatteryMeasurement] = None
    vehicle: Optional[VehicleMeasurement] = None


class BatteryMode(str, Enum):
    charge = "charge"
    discharge = "discharge"
    idle = "idle"


class VehicleMode(str, Enum):
    charge = "charge"
    discharge = "discharge"
    idle = "idle"


class SolarStatus(BaseModel):
    production_kw: float


class BatteryStatus(BaseModel):
    capacity_kwh: float
    state_of_charge_kwh: float
    min_state_of_charge_kwh: float
    max_charge_rate_kw: float
    max_discharge_rate_kw: float
    mode: BatteryMode
    power_kw: float


class VehicleStatus(BaseModel):
    connected: bool
    capacity_kwh: float
    state_of_charge_kwh: float
    max_charge_rate_kw: float
    max_discharge_rate_kw: float
    mode: VehicleMode
    power_kw: float


class LoadStatus(BaseModel):
    critical_load_kw: float
    flexible_load_kw: float
    shed_kw: float
    total_nominal_load_kw: float
    total_consumption_kw: float


class SystemStatus(BaseModel):
    solar: SolarStatus
    battery: BatteryStatus
    vehicle: VehicleStatus
    load: LoadStatus


class BatteryAction(BaseModel):
    mode: BatteryMode = BatteryMode.idle
    requested_power_kw: float = 0.0
    applied_power_kw: float = 0.0


class VehicleAction(BaseModel):
    mode: VehicleMode = VehicleMode.idle
    requested_power_kw: float = 0.0
    applied_power_kw: float = 0.0


class LoadAction(BaseModel):
    shed_target_kw: float = 0.0


class CoordinationActions(BaseModel):
    battery: BatteryAction
    vehicle: VehicleAction
    load: LoadAction


class CoordinateResponse(BaseModel):
    actions: CoordinationActions
    status: SystemStatus


async def _raise_on_transport_error(call):
    try:
        response = await call
        response.raise_for_status()
        return response
    except httpx.RequestError as exc:
        raise HTTPException(status_code=503, detail=f"Error contacting remote service: {exc}") from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc


async def fetch_statuses(client: httpx.AsyncClient) -> SystemStatus:
    responses = await asyncio.gather(
        _raise_on_transport_error(client.get(f"{settings.solar_agent_url}/status")),
        _raise_on_transport_error(client.get(f"{settings.battery_agent_url}/status")),
        _raise_on_transport_error(client.get(f"{settings.vehicle_agent_url}/status")),
        _raise_on_transport_error(client.get(f"{settings.load_agent_url}/status")),
    )
    solar_data, battery_data, vehicle_data, load_data = [response.json() for response in responses]
    return SystemStatus(
        solar=SolarStatus(**solar_data),
        battery=BatteryStatus(**battery_data),
        vehicle=VehicleStatus(**vehicle_data),
        load=LoadStatus(**load_data),
    )


async def push_measurements(payload: CoordinationPayload, client: httpx.AsyncClient) -> None:
    tasks = []
    if payload.solar:
        tasks.append(
            _raise_on_transport_error(
                client.post(f"{settings.solar_agent_url}/production", json=payload.solar.model_dump())
            )
        )
    if payload.load:
        tasks.append(
            _raise_on_transport_error(
                client.post(f"{settings.load_agent_url}/update", json=payload.load.model_dump())
            )
        )
    if payload.battery:
        tasks.append(
            _raise_on_transport_error(
                client.post(f"{settings.battery_agent_url}/update", json=payload.battery.model_dump())
            )
        )
    if payload.vehicle:
        tasks.append(
            _raise_on_transport_error(
                client.post(f"{settings.vehicle_agent_url}/update", json=payload.vehicle.model_dump())
            )
        )
    if tasks:
        await asyncio.gather(*tasks)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/status", response_model=SystemStatus)
async def get_status(_: str = Depends(require_api_key)) -> SystemStatus:
    async with httpx.AsyncClient(
        timeout=settings.http_timeout, headers={API_KEY_HEADER_NAME: settings.api_key}
    ) as client:
        return await fetch_statuses(client)


@app.post("/coordinate", response_model=CoordinateResponse)
async def coordinate(payload: CoordinationPayload, _: str = Depends(require_api_key)) -> CoordinateResponse:
    async with httpx.AsyncClient(
        timeout=settings.http_timeout, headers={API_KEY_HEADER_NAME: settings.api_key}
    ) as client:
        await push_measurements(payload, client)
        status = await fetch_statuses(client)

        actions = CoordinationActions(
            battery=BatteryAction(mode=BatteryMode.idle),
            vehicle=VehicleAction(mode=VehicleMode.idle),
            load=LoadAction(shed_target_kw=status.load.shed_kw),
        )

        net_power = status.solar.production_kw - status.load.total_consumption_kw

        # Surplus scenario: charge battery then vehicle
        if net_power > 0:
            battery_capacity_room = max(status.battery.capacity_kwh - status.battery.state_of_charge_kwh, 0.0)
            if battery_capacity_room > 0:
                requested = min(net_power, status.battery.max_charge_rate_kw, battery_capacity_room)
                if requested > 0:
                    response = await _raise_on_transport_error(
                        client.post(
                            f"{settings.battery_agent_url}/control",
                            json={"mode": BatteryMode.charge.value, "power_kw": requested},
                        )
                    )
                    updated_battery = BatteryStatus(**response.json())
                    status = status.copy(update={"battery": updated_battery})
                    actions.battery = BatteryAction(
                        mode=updated_battery.mode,
                        requested_power_kw=requested,
                        applied_power_kw=updated_battery.power_kw,
                    )
                    net_power -= updated_battery.power_kw

            if net_power > 0 and status.vehicle.connected:
                vehicle_capacity_room = max(status.vehicle.capacity_kwh - status.vehicle.state_of_charge_kwh, 0.0)
                if vehicle_capacity_room > 0:
                    requested = min(net_power, status.vehicle.max_charge_rate_kw, vehicle_capacity_room)
                    if requested > 0:
                        response = await _raise_on_transport_error(
                            client.post(
                                f"{settings.vehicle_agent_url}/control",
                                json={"mode": VehicleMode.charge.value, "power_kw": requested},
                            )
                        )
                        updated_vehicle = VehicleStatus(**response.json())
                        status = status.copy(update={"vehicle": updated_vehicle})
                        actions.vehicle = VehicleAction(
                            mode=updated_vehicle.mode,
                            requested_power_kw=requested,
                            applied_power_kw=updated_vehicle.power_kw,
                        )
                    net_power -= updated_vehicle.power_kw

        # Deficit scenario: discharge battery then vehicle, then shed load
        if net_power < 0:
            deficit = -net_power
            available_battery = max(
                status.battery.state_of_charge_kwh - status.battery.min_state_of_charge_kwh,
                0.0,
            )
            if available_battery > 0:
                requested = min(deficit, status.battery.max_discharge_rate_kw, available_battery)
                if requested > 0:
                    response = await _raise_on_transport_error(
                        client.post(
                            f"{settings.battery_agent_url}/control",
                            json={"mode": BatteryMode.discharge.value, "power_kw": requested},
                        )
                    )
                    updated_battery = BatteryStatus(**response.json())
                    status = status.copy(update={"battery": updated_battery})
                    actions.battery = BatteryAction(
                        mode=updated_battery.mode,
                        requested_power_kw=requested,
                        applied_power_kw=updated_battery.power_kw,
                    )
                    deficit = max(deficit - updated_battery.power_kw, 0.0)
                    net_power = -deficit

            if deficit > 0 and status.vehicle.connected and status.vehicle.state_of_charge_kwh > 0:
                available_vehicle = status.vehicle.state_of_charge_kwh
                requested = min(deficit, status.vehicle.max_discharge_rate_kw, available_vehicle)
                if requested > 0:
                    response = await _raise_on_transport_error(
                        client.post(
                            f"{settings.vehicle_agent_url}/control",
                            json={"mode": VehicleMode.discharge.value, "power_kw": requested},
                        )
                    )
                    updated_vehicle = VehicleStatus(**response.json())
                    status = status.copy(update={"vehicle": updated_vehicle})
                    actions.vehicle = VehicleAction(
                        mode=updated_vehicle.mode,
                        requested_power_kw=requested,
                        applied_power_kw=updated_vehicle.power_kw,
                    )
                    deficit = max(deficit - updated_vehicle.power_kw, 0.0)
                    net_power = -deficit

            if deficit > 0:
                current_shed = status.load.shed_kw
                max_additional = max(status.load.flexible_load_kw - current_shed, 0.0)
                additional = min(deficit, max_additional)
                target = current_shed + additional
                if target != current_shed:
                    response = await _raise_on_transport_error(
                        client.post(
                            f"{settings.load_agent_url}/shed",
                            json={"shed_kw": target},
                        )
                    )
                    updated_load = LoadStatus(**response.json())
                    status = status.copy(update={"load": updated_load})
                    actions.load = LoadAction(shed_target_kw=target)
                else:
                    actions.load = LoadAction(shed_target_kw=current_shed)
            else:
                actions.load = LoadAction(shed_target_kw=status.load.shed_kw)

        return CoordinateResponse(actions=actions, status=status)


__all__ = ["app"]
