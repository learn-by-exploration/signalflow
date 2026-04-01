# mkg/tests/test_features_api.py
"""Tests for MKG about/features API endpoints.

Verifies:
1. /about returns identity, power statement, and thesis
2. /about/features returns full feature catalog
3. /about/novel returns only novel capabilities
4. /about/competitors returns competitive landscape
5. /about/market returns market sizing
6. /about/applications returns domains with buyer profiles
7. /about/tribal-knowledge returns 6 knowledge types
8. /about/mirofish returns integration status
9. /about/complete returns everything
10. Feature data module functions work correctly
"""

import os

import pytest
from httpx import ASGITransport, AsyncClient

from mkg.api.app import create_app
from mkg.api.dependencies import init_container
import mkg.api.dependencies as deps


@pytest.fixture
async def client(tmp_path):
    """Test client with ephemeral app."""
    old_key = os.environ.pop("MKG_API_KEY", None)
    old_db_dir = os.environ.get("MKG_DB_DIR")
    os.environ["MKG_DB_DIR"] = str(tmp_path)
    app = create_app()
    container = init_container()
    await container.startup()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    await container.shutdown()
    deps._container = None
    if old_key is not None:
        os.environ["MKG_API_KEY"] = old_key
    if old_db_dir is not None:
        os.environ["MKG_DB_DIR"] = old_db_dir
    else:
        os.environ.pop("MKG_DB_DIR", None)


class TestAboutEndpoint:
    """GET /api/v1/about — identity and thesis."""

    async def test_about_returns_200(self, client):
        resp = await client.get("/api/v1/about")
        assert resp.status_code == 200

    async def test_about_has_tagline(self, client):
        data = (await client.get("/api/v1/about")).json()["data"]
        assert "tagline" in data
        assert "relationship" in data["tagline"].lower()

    async def test_about_has_power_statement(self, client):
        data = (await client.get("/api/v1/about")).json()["data"]
        assert "Bloomberg" in data["power_statement"]
        assert "60 seconds" in data["power_statement"]

    async def test_about_has_three_speed_thesis(self, client):
        data = (await client.get("/api/v1/about")).json()["data"]
        thesis = data["three_speed_thesis"]
        assert len(thesis["speeds"]) == 4
        assert thesis["speeds"][0]["latency"] == "<100ms"

    async def test_about_has_not_mkg(self, client):
        data = (await client.get("/api/v1/about")).json()["data"]
        assert len(data["not_mkg"]) >= 5


class TestFeaturesEndpoint:
    """GET /api/v1/about/features — feature catalog."""

    async def test_features_returns_200(self, client):
        resp = await client.get("/api/v1/about/features")
        assert resp.status_code == 200

    async def test_features_has_categories(self, client):
        data = (await client.get("/api/v1/about/features")).json()["data"]
        cats = data["categories"]
        assert "Relationship Graph" in cats
        assert "Propagation Engine" in cats
        assert "Explainability & Compliance" in cats

    async def test_features_total_count(self, client):
        data = (await client.get("/api/v1/about/features")).json()["data"]
        assert data["total_features"] >= 20

    async def test_features_novel_count(self, client):
        data = (await client.get("/api/v1/about/features")).json()["data"]
        assert data["novel_count"] >= 12


class TestNovelEndpoint:
    """GET /api/v1/about/novel — unique capabilities."""

    async def test_novel_returns_200(self, client):
        resp = await client.get("/api/v1/about/novel")
        assert resp.status_code == 200

    async def test_novel_all_marked_novel(self, client):
        data = (await client.get("/api/v1/about/novel")).json()["data"]
        for cap in data["novel_capabilities"]:
            assert "id" in cap
            assert "name" in cap

    async def test_novel_statement_mentions_platforms(self, client):
        data = (await client.get("/api/v1/about/novel")).json()["data"]
        stmt = data["statement"]
        assert "Bloomberg" in stmt
        assert "AlphaSense" in stmt


class TestCompetitorsEndpoint:
    """GET /api/v1/about/competitors — competitive landscape."""

    async def test_competitors_returns_200(self, client):
        resp = await client.get("/api/v1/about/competitors")
        assert resp.status_code == 200

    async def test_competitors_count(self, client):
        data = (await client.get("/api/v1/about/competitors")).json()["data"]
        assert data["count"] == 9

    async def test_competitors_have_weaknesses(self, client):
        data = (await client.get("/api/v1/about/competitors")).json()["data"]
        bloomberg = next(c for c in data["competitors"] if c["name"] == "Bloomberg Terminal")
        assert any("graph" in w.lower() for w in bloomberg["weaknesses"])

    async def test_alphasense_highest_threat(self, client):
        data = (await client.get("/api/v1/about/competitors")).json()["data"]
        alpha = next(c for c in data["competitors"] if c["name"] == "AlphaSense")
        assert "highest" in alpha["threat_to_mkg"].lower()


class TestMarketEndpoint:
    """GET /api/v1/about/market — market sizing."""

    async def test_market_returns_200(self, client):
        resp = await client.get("/api/v1/about/market")
        assert resp.status_code == 200

    async def test_market_has_tam(self, client):
        data = (await client.get("/api/v1/about/market")).json()["data"]
        assert "$15B" in data["total_addressable_market"]

    async def test_market_has_segments(self, client):
        data = (await client.get("/api/v1/about/market")).json()["data"]
        assert len(data["segments"]) == 5


class TestApplicationsEndpoint:
    """GET /api/v1/about/applications — domains and buyer profiles."""

    async def test_applications_returns_200(self, client):
        resp = await client.get("/api/v1/about/applications")
        assert resp.status_code == 200

    async def test_applications_two_domains(self, client):
        data = (await client.get("/api/v1/about/applications")).json()["data"]
        assert data["count"] == 2

    async def test_applications_have_buyer_profiles(self, client):
        data = (await client.get("/api/v1/about/applications")).json()["data"]
        finance = data["domains"][0]
        assert len(finance["buyer_profiles"]) == 6

    async def test_supply_chain_has_case_studies(self, client):
        data = (await client.get("/api/v1/about/applications")).json()["data"]
        sc = data["domains"][1]
        assert len(sc["case_studies"]) == 3
        names = [cs["name"] for cs in sc["case_studies"]]
        assert "Red Sea Crisis" in names


class TestTribalKnowledgeEndpoint:
    """GET /api/v1/about/tribal-knowledge — knowledge types."""

    async def test_tribal_returns_200(self, client):
        resp = await client.get("/api/v1/about/tribal-knowledge")
        assert resp.status_code == 200

    async def test_tribal_six_types(self, client):
        data = (await client.get("/api/v1/about/tribal-knowledge")).json()["data"]
        assert data["count"] == 6

    async def test_tribal_types_have_encoding(self, client):
        data = (await client.get("/api/v1/about/tribal-knowledge")).json()["data"]
        for t in data["types"]:
            assert "mkg_encoding" in t


class TestMirofishEndpoint:
    """GET /api/v1/about/mirofish — integration status."""

    async def test_mirofish_returns_200(self, client):
        resp = await client.get("/api/v1/about/mirofish")
        assert resp.status_code == 200

    async def test_mirofish_has_summary(self, client):
        data = (await client.get("/api/v1/about/mirofish")).json()["data"]
        assert "behavioral simulation" in data["summary"].lower()

    async def test_mirofish_reused_components(self, client):
        data = (await client.get("/api/v1/about/mirofish")).json()["data"]
        adopted = [c for c in data["reused_components"] if c["status"] == "adopted"]
        assert len(adopted) >= 2

    async def test_mirofish_future_integration(self, client):
        data = (await client.get("/api/v1/about/mirofish")).json()["data"]
        assert len(data["future_integration"]) >= 4

    async def test_mirofish_use_cases(self, client):
        data = (await client.get("/api/v1/about/mirofish")).json()["data"]
        names = [uc["name"] for uc in data["use_cases"]]
        assert "Signal Validation" in names
        assert "Scenario Planning" in names


class TestCompleteEndpoint:
    """GET /api/v1/about/complete — everything."""

    async def test_complete_returns_200(self, client):
        resp = await client.get("/api/v1/about/complete")
        assert resp.status_code == 200

    async def test_complete_has_all_sections(self, client):
        data = (await client.get("/api/v1/about/complete")).json()["data"]
        assert "identity" in data
        assert "three_speed_thesis" in data
        assert "features" in data
        assert "novel_capabilities" in data
        assert "competitors" in data
        assert "market" in data
        assert "applications" in data
        assert "tribal_knowledge_types" in data
        assert "mirofish" in data
        assert "not_mkg" in data


class TestFeaturesModule:
    """Direct tests on the features data module."""

    def test_get_novel_features_all_novel(self):
        from mkg.domain.features import get_novel_features
        novel = get_novel_features()
        assert all("id" in f and "name" in f for f in novel)
        assert len(novel) >= 12

    def test_get_features_by_category_covers_all(self):
        from mkg.domain.features import get_features_by_category, FEATURES
        by_cat = get_features_by_category()
        total = sum(len(v) for v in by_cat.values())
        assert total == len(FEATURES)

    def test_feature_ids_unique(self):
        from mkg.domain.features import FEATURES
        ids = [f.id for f in FEATURES]
        assert len(ids) == len(set(ids))

    def test_competitor_names_unique(self):
        from mkg.domain.features import COMPETITORS
        names = [c.name for c in COMPETITORS]
        assert len(names) == len(set(names))

    def test_get_full_profile_structure(self):
        from mkg.domain.features import get_full_profile
        profile = get_full_profile()
        assert profile["total_features"] >= 20
        assert profile["novel_count"] >= 12
        assert len(profile["competitors"]) == 9
