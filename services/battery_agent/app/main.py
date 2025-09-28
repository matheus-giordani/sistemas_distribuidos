from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Dict

import grpc
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from services.common import auth, time
from services.protos import energy_pb2, energy_pb2_grpc


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="")

    api_key: str = Field(..., validation_alias="SERVICE_API_KEY")
    port: int = Field(default=8002, validation_alias="PORT")


settings = Settings()
logger = logging.getLogger(__name__)


class BatteryAgentService(energy_pb2_grpc.BatteryAgentServicer):
    def __init__(self) -> None:
        self._state: Dict[str, float | datetime | energy_pb2.BatteryMode] = {
            "capacity_kwh": 10.0,
            "state_of_charge_kwh": 5.0,
            "min_state_of_charge_kwh": 1.0,
            "max_charge_rate_kw": 3.0,
            "max_discharge_rate_kw": 3.0,
            "mode": energy_pb2.BatteryMode.BATTERY_MODE_IDLE,
            "power_kw": 0.0,
            "last_updated": time.utc_now(),
        }

    def _clamp_state_of_charge(self) -> None:
        min_soc = float(self._state["min_state_of_charge_kwh"])
        capacity = float(self._state["capacity_kwh"])
        soc = float(self._state["state_of_charge_kwh"])
        self._state["state_of_charge_kwh"] = max(min(soc, capacity), min_soc)

    def _status(self) -> energy_pb2.BatteryStatus:
        return energy_pb2.BatteryStatus(
            capacity_kwh=float(self._state["capacity_kwh"]),
            state_of_charge_kwh=float(self._state["state_of_charge_kwh"]),
            min_state_of_charge_kwh=float(self._state["min_state_of_charge_kwh"]),
            max_charge_rate_kw=float(self._state["max_charge_rate_kw"]),
            max_discharge_rate_kw=float(self._state["max_discharge_rate_kw"]),
            mode=self._state["mode"],
            power_kw=float(self._state["power_kw"]),
            last_updated=time.to_timestamp(self._state["last_updated"]),
        )

    async def Health(self, request, context):  # noqa: N802
        return energy_pb2.HealthResponse(status="ok")

    async def GetStatus(self, request, context):  # noqa: N802
        await auth.require_api_key(context, settings.api_key)
        return self._status()

    async def UpdateMeasurement(self, request, context):  # noqa: N802
        await auth.require_api_key(context, settings.api_key)
        if request.state_of_charge_kwh < 0:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "state_of_charge_kwh must be non-negative")
        if request.HasField("capacity_kwh"):
            if request.capacity_kwh.value <= 0:
                await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "capacity_kwh must be positive")
            self._state["capacity_kwh"] = request.capacity_kwh.value
        self._state["state_of_charge_kwh"] = request.state_of_charge_kwh
        self._clamp_state_of_charge()
        self._state["last_updated"] = time.utc_now()
        return self._status()

    async def ApplyControl(self, request, context):  # noqa: N802
        await auth.require_api_key(context, settings.api_key)
        if request.power_kw < 0:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "power_kw must be non-negative")
        if request.mode == energy_pb2.BatteryMode.BATTERY_MODE_UNSPECIFIED:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "mode is required")

        soc = float(self._state["state_of_charge_kwh"])
        min_soc = float(self._state["min_state_of_charge_kwh"])
        capacity = float(self._state["capacity_kwh"])
        effective_power = 0.0

        if request.mode == energy_pb2.BatteryMode.BATTERY_MODE_CHARGE:
            available_room = max(capacity - soc, 0.0)
            if available_room > 0:
                effective_power = min(
                    request.power_kw,
                    float(self._state["max_charge_rate_kw"]),
                    available_room,
                )
                soc += effective_power
        elif request.mode == energy_pb2.BatteryMode.BATTERY_MODE_DISCHARGE:
            available_energy = max(soc - min_soc, 0.0)
            if available_energy > 0:
                effective_power = min(
                    request.power_kw,
                    float(self._state["max_discharge_rate_kw"]),
                    available_energy,
                )
                soc -= effective_power
        elif request.mode == energy_pb2.BatteryMode.BATTERY_MODE_IDLE:
            effective_power = 0.0
        else:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Unsupported mode")

        self._state["state_of_charge_kwh"] = soc
        self._state["mode"] = request.mode
        self._state["power_kw"] = effective_power
        self._clamp_state_of_charge()
        self._state["last_updated"] = time.utc_now()
        return self._status()


async def serve() -> None:
    server = grpc.aio.server()
    energy_pb2_grpc.add_BatteryAgentServicer_to_server(BatteryAgentService(), server)
    server.add_insecure_port(f"[::]:{settings.port}")
    await server.start()
    logger.info("Battery agent gRPC server listening on %s", settings.port)
    await server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(serve())
