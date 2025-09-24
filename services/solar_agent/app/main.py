from datetime import datetime
from typing import Dict

from fastapi import Depends, FastAPI, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ProductionUpdate(BaseModel):
    production_kw: float = Field(..., ge=0, description="Instantaneous solar production in kW")


class SolarStatus(BaseModel):
    production_kw: float
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


def default_state() -> Dict[str, datetime | float]:
    return {"production_kw": 0.0, "last_updated": datetime.utcnow()}


state = default_state()
app = FastAPI(title="Solar Generation Agent", version="1.0.0")


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/status", response_model=SolarStatus)
def get_status(_: str = Depends(require_api_key)) -> SolarStatus:
    return SolarStatus(**state)


@app.post("/production", response_model=SolarStatus)
def update_production(update: ProductionUpdate, _: str = Depends(require_api_key)) -> SolarStatus:
    state["production_kw"] = update.production_kw
    state["last_updated"] = datetime.utcnow()
    return SolarStatus(**state)


__all__ = ["app"]
