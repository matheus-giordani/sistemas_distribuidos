from __future__ import annotations

from datetime import datetime
from typing import Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


class LoadMeasurement(BaseModel):
    critical_load_kw: float = Field(..., ge=0)
    flexible_load_kw: float = Field(..., ge=0)

    @property
    def total_load_kw(self) -> float:
        return self.critical_load_kw + self.flexible_load_kw


class LoadSheddingRequest(BaseModel):
    shed_kw: float = Field(..., ge=0)


class LoadStatus(BaseModel):
    critical_load_kw: float
    flexible_load_kw: float
    shed_kw: float
    total_nominal_load_kw: float
    total_consumption_kw: float
    last_updated: datetime


DEFAULTS: Dict[str, float | datetime] = {
    "critical_load_kw": 3.0,
    "flexible_load_kw": 2.0,
    "shed_kw": 0.0,
    "total_nominal_load_kw": 5.0,
    "total_consumption_kw": 5.0,
    "last_updated": datetime.utcnow(),
}


state: Dict[str, float | datetime] = DEFAULTS.copy()
app = FastAPI(title="Flexible Load Agent", version="1.0.0")


def recompute_totals() -> None:
    critical = float(state["critical_load_kw"])
    flexible = float(state["flexible_load_kw"])
    shed = min(float(state["shed_kw"]), flexible)
    state["shed_kw"] = shed
    state["total_nominal_load_kw"] = critical + flexible
    state["total_consumption_kw"] = critical + max(flexible - shed, 0.0)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/status", response_model=LoadStatus)
def get_status() -> LoadStatus:
    return LoadStatus(**state)


@app.post("/update", response_model=LoadStatus)
def update_loads(measurement: LoadMeasurement) -> LoadStatus:
    state["critical_load_kw"] = measurement.critical_load_kw
    state["flexible_load_kw"] = measurement.flexible_load_kw
    recompute_totals()
    state["last_updated"] = datetime.utcnow()
    return LoadStatus(**state)


@app.post("/shed", response_model=LoadStatus)
def apply_shedding(request: LoadSheddingRequest) -> LoadStatus:
    flexible = float(state["flexible_load_kw"])
    if request.shed_kw > flexible:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot shed {request.shed_kw} kW; only {flexible} kW flexible load available.",
        )
    state["shed_kw"] = request.shed_kw
    recompute_totals()
    state["last_updated"] = datetime.utcnow()
    return LoadStatus(**state)


__all__ = ["app"]
