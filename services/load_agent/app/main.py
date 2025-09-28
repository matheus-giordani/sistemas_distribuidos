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
    port: int = Field(default=8004, validation_alias="PORT")


settings = Settings()
logger = logging.getLogger(__name__)


class LoadAgentService(energy_pb2_grpc.LoadAgentServicer):
    def __init__(self) -> None:
        self._state: Dict[str, float | datetime] = {
            "critical_load_kw": 3.0,
            "flexible_load_kw": 2.0,
            "shed_kw": 0.0,
            "total_nominal_load_kw": 5.0,
            "total_consumption_kw": 5.0,
            "last_updated": time.utc_now(),
        }

    def _recompute(self) -> None:
        critical = float(self._state["critical_load_kw"])
        flexible = float(self._state["flexible_load_kw"])
        shed = min(float(self._state["shed_kw"]), flexible)
        self._state["shed_kw"] = shed
        self._state["total_nominal_load_kw"] = critical + flexible
        self._state["total_consumption_kw"] = critical + max(flexible - shed, 0.0)

    def _status(self) -> energy_pb2.LoadStatus:
        return energy_pb2.LoadStatus(
            critical_load_kw=float(self._state["critical_load_kw"]),
            flexible_load_kw=float(self._state["flexible_load_kw"]),
            shed_kw=float(self._state["shed_kw"]),
            total_nominal_load_kw=float(self._state["total_nominal_load_kw"]),
            total_consumption_kw=float(self._state["total_consumption_kw"]),
            last_updated=time.to_timestamp(self._state["last_updated"]),
        )

    async def Health(self, request, context):  # noqa: N802
        return energy_pb2.HealthResponse(status="ok")

    async def GetStatus(self, request, context):  # noqa: N802
        await auth.require_api_key(context, settings.api_key)
        return self._status()

    async def UpdateLoad(self, request, context):  # noqa: N802
        await auth.require_api_key(context, settings.api_key)
        if request.critical_load_kw < 0 or request.flexible_load_kw < 0:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "load values must be non-negative")
        self._state["critical_load_kw"] = request.critical_load_kw
        self._state["flexible_load_kw"] = request.flexible_load_kw
        self._recompute()
        self._state["last_updated"] = time.utc_now()
        return self._status()

    async def ApplyShedding(self, request, context):  # noqa: N802
        await auth.require_api_key(context, settings.api_key)
        if request.shed_kw < 0:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "shed_kw must be non-negative")
        flexible = float(self._state["flexible_load_kw"])
        if request.shed_kw > flexible:
            await context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                f"Cannot shed {request.shed_kw} kW; only {flexible} kW flexible load available.",
            )
        self._state["shed_kw"] = request.shed_kw
        self._recompute()
        self._state["last_updated"] = time.utc_now()
        return self._status()


async def serve() -> None:
    server = grpc.aio.server()
    energy_pb2_grpc.add_LoadAgentServicer_to_server(LoadAgentService(), server)
    server.add_insecure_port(f"[::]:{settings.port}")
    await server.start()
    logger.info("Load agent gRPC server listening on %s", settings.port)
    await server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(serve())
