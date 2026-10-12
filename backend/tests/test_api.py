import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_health_and_root():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

        root_resp = await client.get("/")
        assert root_resp.status_code == 200
        assert "agents" in root_resp.json()

@pytest.mark.asyncio
async def test_sample_scenarios_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/samples")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 3
        assert "scenario-01-engineering-spec" in [s["id"] for s in data]

@pytest.mark.asyncio
async def test_compliance_analysis_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "reference_text": "The submitted report must contain design calculations and material specifications.",
            "submitted_text": "Design calculations: Available. Material specification: Available."
        }
        resp = await client.post("/api/compliance/analyze", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "job_id" in data
        assert "compliance_score" in data
        assert len(data["requirements_matrix"]) >= 2
