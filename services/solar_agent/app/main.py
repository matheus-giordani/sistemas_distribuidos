from datetime import datetime
from typing import Dict

from fastapi import FastAPI
from pydantic import BaseModel, Field


class ProductionUpdate(BaseModel):
    production_kw: float = Field(..., ge=0, description="Instantaneous solar production in kW")


class SolarStatus(BaseModel):
    production_kw: float
    last_updated: datetime


def default_state() -> Dict[str, datetime | float]:
    return {"production_kw": 0.0, "last_updated": datetime.utcnow()}


state = default_state()
app = FastAPI(title="Solar Generation Agent", version="1.0.0")


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/status", response_model=SolarStatus)
def get_status() -> SolarStatus:
    return SolarStatus(**state)


@app.post("/production", response_model=SolarStatus)
def update_production(update: ProductionUpdate) -> SolarStatus:
    state["production_kw"] = update.production_kw
    state["last_updated"] = datetime.utcnow()
    return SolarStatus(**state)


__all__ = ["app"]
