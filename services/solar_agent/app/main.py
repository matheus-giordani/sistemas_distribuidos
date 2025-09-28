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
    port: int = Field(default=8001, validation_alias="PORT")


settings = Settings()
logger = logging.getLogger(__name__)


class SolarAgentService(energy_pb2_grpc.SolarAgentServicer):
    def __init__(self) -> None:
        self._state: Dict[str, float | datetime] = {
            "production_kw": 0.0,
            "last_updated": time.utc_now(),
        }

    def _current_status(self) -> energy_pb2.SolarStatus:
        return energy_pb2.SolarStatus(
            production_kw=float(self._state["production_kw"]),
            last_updated=time.to_timestamp(self._state["last_updated"]),
        )

    async def Health(self, request, context):  # noqa: N802 (gRPC naming)
        return energy_pb2.HealthResponse(status="ok")

    async def GetStatus(self, request, context):  # noqa: N802
        await auth.require_api_key(context, settings.api_key)
        return self._current_status()

    async def UpdateProduction(self, request, context):  # noqa: N802
        await auth.require_api_key(context, settings.api_key)
        if request.production_kw < 0:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "production_kw must be non-negative")
        self._state["production_kw"] = request.production_kw
        self._state["last_updated"] = time.utc_now()
        return self._current_status()


async def serve() -> None:
    server = grpc.aio.server()
    energy_pb2_grpc.add_SolarAgentServicer_to_server(SolarAgentService(), server)
    server.add_insecure_port(f"[::]:{settings.port}")
    await server.start()
    logger.info("Solar agent gRPC server listening on %s", settings.port)
    await server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(serve())
