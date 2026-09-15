"""
test_quakemind.py - Comprehensive Unit Test Suite for QuakeMind Global.
Verifies geophysics calculations, MMI attenuation, PAP logic, and ATC-20 triage.
"""

import sys
import os
import pytest

# Ensure parent directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from quakemind_engine import (
    haversine_distance,
    hypocentral_distance,
    calculate_attenuation_mmi,
    get_mmi_description,
    compute_perceived_shaking,
    get_pap_guidance,
    evaluate_structural_safety,
    debunk_seismic_myth,
    fetch_global_earthquakes,
    fetch_emsc_earthquakes,
    fetch_multi_source,
    _deduplicate_quakes,
    calculate_eew_kinematics,
    SEISMIC_FEEDS,
    USGS_FEEDS
)
from i18n import get_text


class TestGeophysicsAndAttenuation:
    
    def test_haversine_distance_known_points(self):
        # Cali (3.4516, -76.5320) to Bogota (4.7110, -74.0721) ~ 300 km
        dist = haversine_distance(3.4516, -76.5320, 4.7110, -74.0721)
        assert 280.0 <= dist <= 320.0

    def test_haversine_zero_distance(self):
        dist = haversine_distance(10.0, 20.0, 10.0, 20.0)
        assert dist == 0.0

    def test_hypocentral_distance_pythagorean(self):
        # 30 km epicentral, 40 km depth -> sqrt(30^2 + 40^2) = 50 km
        hypo = hypocentral_distance(30.0, 40.0)
        assert hypo == 50.0

    def test_mmi_attenuation_clamping(self):
        # Extreme high magnitude at zero distance -> clamped at 12.0
        mmi_high = calculate_attenuation_mmi(9.5, 1.0)
        assert mmi_high <= 12.0
        
        # Tiny magnitude at huge distance -> clamped at 1.0
        mmi_low = calculate_attenuation_mmi(1.0, 5000.0)
        assert mmi_low >= 1.0

    def test_mmi_decreases_with_distance(self):
        mag = 7.0
        mmi_near = calculate_attenuation_mmi(mag, 20.0)
        mmi_far = calculate_attenuation_mmi(mag, 300.0)
        assert mmi_near > mmi_far

    def test_mmi_descriptions(self):
        desc_es = get_mmi_description(4.0, lang="es")
        assert "IV" in desc_es["roman_title"]
        assert desc_es["color_hex"] != ""

        desc_en = get_mmi_description(8.0, lang="en")
        assert "VIII" in desc_en["roman_title"]
        assert "Destructive" in desc_en["roman_title"]

    def test_zero_alarm_fatigue_filtering(self):
        # A distant small quake (M 4.2 at 350 km epicentral, 20 km depth)
        hypo_distant = hypocentral_distance(350.0, 20.0)
        mmi_distant = calculate_attenuation_mmi(4.2, hypo_distant)
        # Should be below threshold (MMI IV / 4.0), imperceptible to human occupants
        assert mmi_distant < 3.0, f"Expected imperceptible MMI < 3.0, got {mmi_distant}"

        # A severe regional quake (M 7.2 at 60 km epicentral, 15 km depth)
        hypo_severe = hypocentral_distance(60.0, 15.0)
        mmi_severe = calculate_attenuation_mmi(7.2, hypo_severe)
        # Should be high intensity (MMI >= 7.0 - Very Strong)
        assert mmi_severe >= 7.0, f"Expected severe MMI >= 7.0, got {mmi_severe}"


class TestPsychologicalFirstAid:

    def test_pap_guidance_structure_es(self):
        pap = get_pap_guidance(lang="es")
        assert "ABCDE" in pap["title"]
        assert len(pap["steps"]) == 5
        step_names = [s["step"] for s in pap["steps"]]
        assert step_names == ["A", "B", "C", "D", "E"]

    def test_pap_guidance_structure_en(self):
        pap = get_pap_guidance(lang="en")
        assert "ABCDE" in pap["title"]
        assert len(pap["steps"]) == 5
        assert "Grounding" in pap["steps"][0]["name"]


class TestATC20StructuralTriage:

    def test_red_tag_on_diagonal_crack(self):
        res = evaluate_structural_safety("elem_column", "crack_diagonal", False, lang="es")
        assert res["tag"] == "RED"
        assert "ROJA" in res["title"]

    def test_red_tag_on_gas_leak(self):
        res = evaluate_structural_safety("elem_wall", "crack_hairline", True, lang="es")
        assert res["tag"] == "RED"

    def test_yellow_tag_on_horizontal_masonry(self):
        res = evaluate_structural_safety("elem_wall", "crack_horizontal", False, lang="es")
        assert res["tag"] == "YELLOW"

    def test_green_tag_on_superficial_hairline(self):
        res = evaluate_structural_safety("elem_wall", "crack_hairline", False, lang="es")
        assert res["tag"] == "GREEN"
        assert "VERDE" in res["title"]


class TestMythBuster:

    def test_debunk_time_prediction(self):
        res = debunk_seismic_myth("Dicen que predijeron un terremoto para hoy a las 6 pm", lang="es")
        assert "FALSO" in res["verdict"]

    def test_debunk_weather_heat(self):
        res = debunk_seismic_myth("Mucho calor y bochorno hoy, seguro va a temblar", lang="es")
        assert "DESMENTIDO" in res["verdict"]

    def test_debunk_triangle_of_life(self):
        res = debunk_seismic_myth("El triangulo de la vida es lo mejor", lang="es")
        assert "TRIÁNGULO" in res["verdict"]


class TestDataIngestionFallback:

    def test_fetch_earthquakes_returns_list(self):
        quakes = fetch_global_earthquakes("day_45", timeout=5)
        assert isinstance(quakes, list)
        assert len(quakes) > 0
        q = quakes[0]
        assert "mag" in q
        assert "lat" in q
        assert "lon" in q
        assert "depth_km" in q


class TestMultiSourceIngestion:

    def test_seismic_feeds_contains_emsc(self):
        assert "emsc_recent" in SEISMIC_FEEDS
        assert "seismicportal.eu" in SEISMIC_FEEDS["emsc_recent"]

    def test_backward_compat_usgs_feeds_alias(self):
        # USGS_FEEDS must remain accessible as alias for backward compatibility
        assert USGS_FEEDS is SEISMIC_FEEDS
        assert "hour" in USGS_FEEDS
        assert "day_45" in USGS_FEEDS

    def test_fetch_emsc_returns_list(self):
        quakes = fetch_emsc_earthquakes(limit=10, min_mag=4.0, timeout=10)
        assert isinstance(quakes, list)
        # EMSC may return 0 if no recent M4+ events, but should not error
        if len(quakes) > 0:
            q = quakes[0]
            assert "mag" in q
            assert "lat" in q
            assert "lon" in q
            assert "depth_km" in q
            assert q.get("source") == "EMSC"

    def test_deduplication_removes_close_events(self):
        # Two events at nearly the same location and time should be deduplicated
        event_a = [
            {"id": "usgs-1", "lat": 3.45, "lon": -76.53, "time_epoch": 1700000000000, "mag": 5.0, "source": "USGS"}
        ]
        event_b = [
            {"id": "emsc-1", "lat": 3.46, "lon": -76.54, "time_epoch": 1700000060000, "mag": 5.1, "source": "EMSC"}
        ]
        merged = _deduplicate_quakes(event_a, event_b)
        # Should keep only 1 event (they are ~1.5 km apart and 60s difference)
        assert len(merged) == 1

    def test_deduplication_keeps_distant_events(self):
        # Two events far apart should both be kept
        event_a = [
            {"id": "usgs-1", "lat": 3.45, "lon": -76.53, "time_epoch": 1700000000000, "mag": 5.0, "source": "USGS"}
        ]
        event_b = [
            {"id": "emsc-1", "lat": 35.0, "lon": 139.0, "time_epoch": 1700000060000, "mag": 6.0, "source": "EMSC"}
        ]
        merged = _deduplicate_quakes(event_a, event_b)
        assert len(merged) == 2

    def test_multi_source_returns_list(self):
        quakes = fetch_multi_source("day_45", timeout=10)
        assert isinstance(quakes, list)
        assert len(quakes) > 0


class TestEEWKinematicsEngine:

    def test_eew_kinematics_warning_window(self):
        # M 6.5 at 120 km epicentral, 15 km depth
        user_lat, user_lon = 3.4516, -76.5320
        # Simulated epicenter ~120 km away
        eq = {
            "id": "test-eew-1",
            "lat": 4.53,
            "lon": -76.53,
            "depth_km": 15.0,
            "mag": 6.5,
            "time_epoch": int((pytest.importorskip("time").time() - 10) * 1000) # occurred 10s ago
        }
        res = calculate_eew_kinematics(user_lat, user_lon, eq)
        assert res["hypocentral_dist_km"] >= 100.0
        assert res["p_wave_travel_sec"] < res["s_wave_travel_sec"]
        assert res["warning_window_p_s_sec"] > 0
        assert res["estimated_local_mmi"] >= 4.0
        # If S-wave takes ~35s and 10s elapsed, remaining should be ~25s
        assert res["remaining_s_wave_seconds"] > 15.0
        assert res["is_hazardous"] is True

    def test_eew_kinematics_imperceptible_event(self):
        # M 3.0 at 250 km away -> Imperceptible
        user_lat, user_lon = 3.4516, -76.5320
        eq = {
            "id": "test-eew-small",
            "lat": 5.70,
            "lon": -76.53,
            "depth_km": 30.0,
            "mag": 3.0,
            "time_epoch": int((pytest.importorskip("time").time() - 2) * 1000)
        }
        res = calculate_eew_kinematics(user_lat, user_lon, eq)
        assert res["estimated_local_mmi"] < 3.0
        # Non hazardous: should not cause alarm panic
        assert res["is_hazardous"] is False


class TestSensorAndPWAArchitecture:
    """
    Unit and static analysis tests for PWA WebAPK sensor architecture,
    Chromium permissions API query, Generic Sensor fallback, Xiaomi HyperOS guidance,
    and 100% parity across pwa/, docs/, and root distributions.
    """

    @pytest.fixture(autouse=True)
    def setup_paths(self):
        self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.index_html_path = os.path.join(self.root_dir, "index.html")
        self.pwa_html_path = os.path.join(self.root_dir, "pwa", "index.html")
        self.docs_html_path = os.path.join(self.root_dir, "docs", "index.html")
        with open(self.index_html_path, "r", encoding="utf-8") as f:
            self.html_content = f.read()

    def test_hash_parity_across_distributions(self):
        import hashlib
        def sha256_file(path):
            with open(path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()

        hash_root = sha256_file(self.index_html_path)
        hash_pwa = sha256_file(self.pwa_html_path)
        hash_docs = sha256_file(self.docs_html_path)

        assert hash_root == hash_pwa == hash_docs, "Root index.html, pwa/index.html, and docs/index.html must be strictly identical"

    def test_pwa_standalone_detection_logic_present(self):
        assert "function isRunningStandalone()" in self.html_content
        assert "(display-mode: standalone)" in self.html_content
        assert "navigator.standalone" in self.html_content
        assert "android-app://" in self.html_content

    def test_permissions_api_query_implemented(self):
        assert "navigator.permissions" in self.html_content
        assert "name: 'accelerometer'" in self.html_content
        assert "checkAccelerometerPermission" in self.html_content

    def test_dual_sensor_and_generic_sensor_fallback(self):
        assert "CentinelaMotionController" in self.html_content
        assert "devicemotion" in self.html_content
        assert "new window.Accelerometer" in self.html_content or "new Accelerometer" in self.html_content
        assert "frequency: 50" in self.html_content

    def test_xiaomi_hyperos_guidance_present(self):
        assert "XIAOMI / HYPEROS / MIUI" in self.html_content
        assert "Sin restricciones" in self.html_content
        assert "Inicio automático" in self.html_content

    def test_graceful_degradation_to_network_mode(self):
        assert "sentinelMode = 'network_only'" in self.html_content
        assert "btnContinueNetworkOnly" in self.html_content
        assert "startNetworkPulse" in self.html_content
        assert "sentinelBadgeNetwork" in self.html_content

    def test_location_button_uses_synchronized_not_protected(self):
        assert "Ubicación Sincronizada" in self.html_content
        assert "Location Synchronized" in self.html_content
        assert "Ubicación Activa y Protegida" not in self.html_content
        assert "Ubicación Protegida" not in self.html_content
        assert "Radar Sísmico Protector" not in self.html_content


