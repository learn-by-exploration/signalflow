# mkg/tests/test_alert_system.py
"""Tests for AlertSystem — generates alerts from causal chain analysis.

R-AL1 through R-AL5: Threshold-based alerting, severity levels,
alert dedup, and subscription filtering.
"""

import pytest


class TestAlertSystem:

    @pytest.fixture
    def system(self):
        from mkg.domain.services.alert_system import AlertSystem
        return AlertSystem(impact_thresholds={"critical": 0.8, "high": 0.6, "medium": 0.3})

    def test_generate_alert_from_chain(self, system):
        chain = {
            "trigger": "tsmc",
            "trigger_name": "TSMC",
            "trigger_event": "Factory fire",
            "affected_entity": "nvidia",
            "affected_name": "NVIDIA",
            "impact_score": 0.9,
            "hops": 1,
            "narrative": "TSMC fire affects NVIDIA via supplies to (90% impact).",
        }
        alert = system.generate_alert(chain)
        assert alert is not None
        assert alert["severity"] == "critical"

    def test_severity_levels(self, system):
        for i, (impact, expected) in enumerate([(0.9, "critical"), (0.7, "high"), (0.4, "medium"), (0.1, "low")]):
            chain = {"impact_score": impact, "trigger_event": f"test-{i}",
                     "affected_name": "X", "trigger_name": "Y",
                     "narrative": "n", "affected_entity": f"x{i}", "trigger": "y", "hops": 1}
            alert = system.generate_alert(chain)
            assert alert["severity"] == expected, f"impact={impact}, expected={expected}"

    def test_alert_has_required_fields(self, system):
        chain = {
            "trigger": "tsmc", "trigger_name": "TSMC",
            "trigger_event": "Supply cut", "affected_entity": "nvidia",
            "affected_name": "NVIDIA", "impact_score": 0.85,
            "hops": 1, "narrative": "A affects B.",
        }
        alert = system.generate_alert(chain)
        assert "id" in alert
        assert "severity" in alert
        assert "title" in alert
        assert "message" in alert
        assert "timestamp" in alert
        assert "source_chain" in alert

    def test_dedup_same_chain(self, system):
        chain = {
            "trigger": "tsmc", "trigger_name": "TSMC",
            "trigger_event": "Fire", "affected_entity": "nvidia",
            "affected_name": "NVIDIA", "impact_score": 0.85,
            "hops": 1, "narrative": "A affects B.",
        }
        a1 = system.generate_alert(chain)
        a2 = system.generate_alert(chain)
        assert a1 is not None
        assert a2 is None  # Duplicate suppressed

    def test_reset_dedup_allows_realert(self, system):
        chain = {
            "trigger": "tsmc", "trigger_name": "TSMC",
            "trigger_event": "Fire", "affected_entity": "nvidia",
            "affected_name": "NVIDIA", "impact_score": 0.85,
            "hops": 1, "narrative": "A affects B.",
        }
        a1 = system.generate_alert(chain)
        system.clear_dedup()
        a2 = system.generate_alert(chain)
        assert a1 is not None
        assert a2 is not None

    def test_filter_by_min_severity(self, system):
        chains = [
            {"impact_score": 0.9, "trigger_event": "e1",
             "affected_name": "A", "trigger_name": "T",
             "narrative": "n", "affected_entity": "a", "trigger": "t", "hops": 1},
            {"impact_score": 0.1, "trigger_event": "e2",
             "affected_name": "B", "trigger_name": "T",
             "narrative": "n", "affected_entity": "b", "trigger": "t", "hops": 1},
        ]
        alerts = system.generate_alerts(chains, min_severity="high")
        assert len(alerts) == 1
        assert alerts[0]["severity"] in ("critical", "high")

    def test_get_recent_alerts(self, system):
        for i in range(5):
            chain = {
                "impact_score": 0.6 + i * 0.05,
                "trigger_event": f"event-{i}",
                "affected_name": f"Entity-{i}",
                "trigger_name": "T",
                "narrative": "n",
                "affected_entity": f"e{i}",
                "trigger": "t",
                "hops": 1,
            }
            system.generate_alert(chain)
        recent = system.get_recent_alerts(limit=3)
        assert len(recent) == 3

    def test_invalid_threshold_above_one(self):
        from mkg.domain.services.alert_system import AlertSystem
        with pytest.raises(ValueError, match="Threshold 'critical' must be in"):
            AlertSystem(impact_thresholds={"critical": 1.5, "high": 0.6, "medium": 0.3})

    def test_invalid_threshold_negative(self):
        from mkg.domain.services.alert_system import AlertSystem
        with pytest.raises(ValueError, match="Threshold 'medium' must be in"):
            AlertSystem(impact_thresholds={"critical": 0.8, "high": 0.6, "medium": -0.1})

    def test_valid_boundary_thresholds(self):
        from mkg.domain.services.alert_system import AlertSystem
        system = AlertSystem(impact_thresholds={"critical": 1.0, "high": 0.5, "medium": 0.0})
        assert system._thresholds["critical"] == 1.0
        assert system._thresholds["medium"] == 0.0
