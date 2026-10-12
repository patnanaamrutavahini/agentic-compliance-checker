from fastapi import APIRouter, HTTPException
from typing import List
from app.models.schemas import SampleScenario
from app.services.sample_data_service import get_sample_scenarios, get_scenario_by_id

router = APIRouter(prefix="/api/samples", tags=["Samples"])

@router.get("", response_model=List[SampleScenario])
async def list_sample_scenarios():
    """
    Returns available real-world compliance test scenarios (Aerospace, ISO 9001, GDPR, Healthcare).
    """
    return get_sample_scenarios()

@router.get("/{scenario_id}", response_model=SampleScenario)
async def get_single_scenario(scenario_id: str):
    """
    Returns text and metadata for a specific sample scenario.
    """
    scenario = get_scenario_by_id(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario
