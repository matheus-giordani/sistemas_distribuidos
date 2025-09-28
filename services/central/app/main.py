from __future__ import annotations

import asyncio
import logging
import grpc
from google.protobuf import empty_pb2
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from services.common import auth
from services.protos import energy_pb2, energy_pb2_grpc


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="")

    solar_agent_target: str = Field(
        default="solar-agent:8001",
        validation_alias=AliasChoices("SOLAR_AGENT_TARGET", "SOLAR_AGENT_URL"),
    )
    battery_agent_target: str = Field(
        default="battery-agent:8002",
        validation_alias=AliasChoices("BATTERY_AGENT_TARGET", "BATTERY_AGENT_URL"),
    )
    vehicle_agent_target: str = Field(
        default="vehicle-agent:8003",
        validation_alias=AliasChoices("VEHICLE_AGENT_TARGET", "VEHICLE_AGENT_URL"),
    )
    load_agent_target: str = Field(
        default="load-agent:8004",
        validation_alias=AliasChoices("LOAD_AGENT_TARGET", "LOAD_AGENT_URL"),
    )
    rpc_timeout: float = Field(default=5.0, validation_alias="RPC_CLIENT_TIMEOUT")
    api_key: str = Field(..., validation_alias="SERVICE_API_KEY")
    port: int = Field(default=8000, validation_alias="PORT")


settings = Settings()
logger = logging.getLogger(__name__)


class CentralCoordinatorService(energy_pb2_grpc.CentralCoordinatorServicer):
    def __init__(self, service_settings: Settings) -> None:
        self._settings = service_settings
        self._metadata = auth.metadata(service_settings.api_key)
        self._solar_channel = grpc.aio.insecure_channel(service_settings.solar_agent_target)
        self._battery_channel = grpc.aio.insecure_channel(service_settings.battery_agent_target)
        self._vehicle_channel = grpc.aio.insecure_channel(service_settings.vehicle_agent_target)
        self._load_channel = grpc.aio.insecure_channel(service_settings.load_agent_target)
        self._solar = energy_pb2_grpc.SolarAgentStub(self._solar_channel)
        self._battery = energy_pb2_grpc.BatteryAgentStub(self._battery_channel)
        self._vehicle = energy_pb2_grpc.VehicleAgentStub(self._vehicle_channel)
        self._load = energy_pb2_grpc.LoadAgentStub(self._load_channel)

    async def close(self) -> None:
        await asyncio.gather(
            self._solar_channel.close(),
            self._battery_channel.close(),
            self._vehicle_channel.close(),
            self._load_channel.close(),
        )

    async def Health(self, request, context):  # noqa: N802
        return energy_pb2.HealthResponse(status="ok")

    async def GetStatus(self, request, context):  # noqa: N802
        await auth.require_api_key(context, self._settings.api_key)
        return await self._fetch_statuses(context)

    async def Coordinate(self, request, context):  # noqa: N802
        await auth.require_api_key(context, self._settings.api_key)

        if request.HasField("updates"):
            await self._push_measurements(request.updates, context)

        status = await self._fetch_statuses(context)
        actions = energy_pb2.CoordinationActions(
            battery=energy_pb2.BatteryAction(
                mode=energy_pb2.BatteryMode.BATTERY_MODE_IDLE,
                requested_power_kw=0.0,
                applied_power_kw=0.0,
            ),
            vehicle=energy_pb2.VehicleAction(
                mode=energy_pb2.VehicleMode.VEHICLE_MODE_IDLE,
                requested_power_kw=0.0,
                applied_power_kw=0.0,
            ),
            load=energy_pb2.LoadAction(shed_target_kw=status.load.shed_kw),
        )

        net_power = status.solar.production_kw - status.load.total_consumption_kw

        if net_power > 0:
            battery_capacity_room = max(status.battery.capacity_kwh - status.battery.state_of_charge_kwh, 0.0)
            if battery_capacity_room > 0:
                requested = min(
                    net_power,
                    status.battery.max_charge_rate_kw,
                    battery_capacity_room,
                )
                if requested > 0:
                    response = await self._safe_call(
                        self._battery.ApplyControl(
                            energy_pb2.BatteryControl(
                                mode=energy_pb2.BatteryMode.BATTERY_MODE_CHARGE,
                                power_kw=requested,
                            ),
                            metadata=self._metadata,
                            timeout=self._settings.rpc_timeout,
                        ),
                        context,
                    )
                    status.battery.CopyFrom(response)
                    actions.battery.mode = response.mode
                    actions.battery.requested_power_kw = requested
                    actions.battery.applied_power_kw = response.power_kw
                    net_power = max(net_power - response.power_kw, 0.0)

            if net_power > 0 and status.vehicle.connected:
                vehicle_capacity_room = max(status.vehicle.capacity_kwh - status.vehicle.state_of_charge_kwh, 0.0)
                if vehicle_capacity_room > 0:
                    requested = min(
                        net_power,
                        status.vehicle.max_charge_rate_kw,
                        vehicle_capacity_room,
                    )
                    if requested > 0:
                        response = await self._safe_call(
                            self._vehicle.ApplyControl(
                                energy_pb2.VehicleControl(
                                    mode=energy_pb2.VehicleMode.VEHICLE_MODE_CHARGE,
                                    power_kw=requested,
                                ),
                                metadata=self._metadata,
                                timeout=self._settings.rpc_timeout,
                            ),
                            context,
                        )
                        status.vehicle.CopyFrom(response)
                        actions.vehicle.mode = response.mode
                        actions.vehicle.requested_power_kw = requested
                        actions.vehicle.applied_power_kw = response.power_kw
                        net_power = max(net_power - response.power_kw, 0.0)

        if net_power < 0:
            deficit = -net_power
            available_battery = max(
                status.battery.state_of_charge_kwh - status.battery.min_state_of_charge_kwh,
                0.0,
            )
            if available_battery > 0:
                requested = min(
                    deficit,
                    status.battery.max_discharge_rate_kw,
                    available_battery,
                )
                if requested > 0:
                    response = await self._safe_call(
                        self._battery.ApplyControl(
                            energy_pb2.BatteryControl(
                                mode=energy_pb2.BatteryMode.BATTERY_MODE_DISCHARGE,
                                power_kw=requested,
                            ),
                            metadata=self._metadata,
                            timeout=self._settings.rpc_timeout,
                        ),
                        context,
                    )
                    status.battery.CopyFrom(response)
                    actions.battery.mode = response.mode
                    actions.battery.requested_power_kw = requested
                    actions.battery.applied_power_kw = response.power_kw
                    deficit = max(deficit - response.power_kw, 0.0)
                    net_power = -deficit

            if deficit > 0 and status.vehicle.connected and status.vehicle.state_of_charge_kwh > 0:
                available_vehicle = status.vehicle.state_of_charge_kwh
                requested = min(
                    deficit,
                    status.vehicle.max_discharge_rate_kw,
                    available_vehicle,
                )
                if requested > 0:
                    response = await self._safe_call(
                        self._vehicle.ApplyControl(
                            energy_pb2.VehicleControl(
                                mode=energy_pb2.VehicleMode.VEHICLE_MODE_DISCHARGE,
                                power_kw=requested,
                            ),
                            metadata=self._metadata,
                            timeout=self._settings.rpc_timeout,
                        ),
                        context,
                    )
                    status.vehicle.CopyFrom(response)
                    actions.vehicle.mode = response.mode
                    actions.vehicle.requested_power_kw = requested
                    actions.vehicle.applied_power_kw = response.power_kw
                    deficit = max(deficit - response.power_kw, 0.0)
                    net_power = -deficit

            if deficit > 0:
                current_shed = status.load.shed_kw
                max_additional = max(status.load.flexible_load_kw - current_shed, 0.0)
                additional = min(deficit, max_additional)
                target = current_shed + additional
                if target != current_shed:
                    response = await self._safe_call(
                        self._load.ApplyShedding(
                            energy_pb2.LoadSheddingRequest(shed_kw=target),
                            metadata=self._metadata,
                            timeout=self._settings.rpc_timeout,
                        ),
                        context,
                    )
                    status.load.CopyFrom(response)
                    actions.load.shed_target_kw = target
                else:
                    actions.load.shed_target_kw = current_shed
            else:
                actions.load.shed_target_kw = status.load.shed_kw

        return energy_pb2.CoordinateResponse(actions=actions, status=status)

    async def _fetch_statuses(self, context) -> energy_pb2.SystemStatus:
        try:
            solar_status, battery_status, vehicle_status, load_status = await asyncio.gather(
                self._solar.GetStatus(
                    empty_pb2.Empty(), metadata=self._metadata, timeout=self._settings.rpc_timeout
                ),
                self._battery.GetStatus(
                    empty_pb2.Empty(), metadata=self._metadata, timeout=self._settings.rpc_timeout
                ),
                self._vehicle.GetStatus(
                    empty_pb2.Empty(), metadata=self._metadata, timeout=self._settings.rpc_timeout
                ),
                self._load.GetStatus(
                    empty_pb2.Empty(), metadata=self._metadata, timeout=self._settings.rpc_timeout
                ),
            )
        except grpc.aio.AioRpcError as exc:
            await context.abort(exc.code(), exc.details() or "Failed to fetch remote status")
        return energy_pb2.SystemStatus(
            solar=solar_status,
            battery=battery_status,
            vehicle=vehicle_status,
            load=load_status,
        )

    async def _push_measurements(
        self, payload: energy_pb2.CoordinationPayload, context
    ) -> None:
        calls = []
        if payload.HasField("solar"):
            if payload.solar.production_kw < 0:
                await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "solar.production_kw must be non-negative")
            calls.append(
                self._solar.UpdateProduction(
                    payload.solar, metadata=self._metadata, timeout=self._settings.rpc_timeout
                )
            )
        if payload.HasField("load"):
            if payload.load.critical_load_kw < 0 or payload.load.flexible_load_kw < 0:
                await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "load values must be non-negative")
            calls.append(
                self._load.UpdateLoad(
                    payload.load, metadata=self._metadata, timeout=self._settings.rpc_timeout
                )
            )
        if payload.HasField("battery"):
            if payload.battery.state_of_charge_kwh < 0:
                await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "battery.state_of_charge_kwh must be non-negative")
            if payload.battery.HasField("capacity_kwh") and payload.battery.capacity_kwh.value <= 0:
                await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "battery.capacity_kwh must be positive")
            calls.append(
                self._battery.UpdateMeasurement(
                    payload.battery, metadata=self._metadata, timeout=self._settings.rpc_timeout
                )
            )
        if payload.HasField("vehicle"):
            if payload.vehicle.state_of_charge_kwh < 0:
                await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "vehicle.state_of_charge_kwh must be non-negative")
            if payload.vehicle.HasField("capacity_kwh") and payload.vehicle.capacity_kwh.value <= 0:
                await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "vehicle.capacity_kwh must be positive")
            calls.append(
                self._vehicle.UpdateMeasurement(
                    payload.vehicle, metadata=self._metadata, timeout=self._settings.rpc_timeout
                )
            )
        if not calls:
            return
        try:
            await asyncio.gather(*calls)
        except grpc.aio.AioRpcError as exc:
            await context.abort(exc.code(), exc.details() or "Failed to push measurement")

    async def _safe_call(self, rpc, context):
        try:
            return await rpc
        except grpc.aio.AioRpcError as exc:
            await context.abort(exc.code(), exc.details() or "Remote call failed")


async def serve() -> None:
    server = grpc.aio.server()
    service = CentralCoordinatorService(settings)
    energy_pb2_grpc.add_CentralCoordinatorServicer_to_server(service, server)
    server.add_insecure_port(f"[::]:{settings.port}")
    await server.start()
    logger.info("Central coordinator gRPC server listening on %s", settings.port)
    try:
        await server.wait_for_termination()
    finally:
        await service.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(serve())
