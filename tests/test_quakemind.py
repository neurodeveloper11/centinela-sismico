"""
test_quakemind.py - Comprehensive Unit Test Suite for QuakeMind Global.
Verifies geophysics calculations, MMI attenuation, PAP logic, and ATC-20 triage.
"""

import sys
import os
import re
import json
import math
import random
import shutil
import subprocess
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
    allen2012_mmi_raw,
    mmi_sigma,
    assess_event,
    normalize_emsc_feature,
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
        # Allen et al. (2012) IPE: strong shaking (MMI VI+), well above the alarm threshold
        assert mmi_severe >= 6.0, f"Expected strong MMI >= 6.0, got {mmi_severe}"


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


class _FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload


USGS_FIXTURE = {
    "type": "FeatureCollection",
    "features": [
        {"id": "us7000test", "type": "Feature",
         "properties": {"mag": 5.4, "place": "12 km W of Test, Colombia", "time": 1790000000000,
                        "title": "M 5.4 - 12 km W of Test, Colombia", "magType": "mww",
                        "url": "https://earthquake.usgs.gov/x", "alert": None, "felt": 3, "mmi": 4.1, "tsunami": 0},
         "geometry": {"type": "Point", "coordinates": [-76.65, 4.95, 103.0]}},
        {"id": "us7000nomag", "type": "Feature",
         "properties": {"mag": None, "time": 1790000000000},
         "geometry": {"type": "Point", "coordinates": [0, 0, 10]}},
    ],
}

EMSC_FIXTURE = {
    "type": "FeatureCollection",
    "features": [
        {"id": "20260923_0000277", "type": "Feature",
         "geometry": {"type": "Point", "coordinates": [-76.66, 4.96, -103.0]},
         "properties": {"time": "2026-09-23T20:55:51.8Z", "depth": 103.0, "mag": 5.3, "magtype": "mb",
                        "flynn_region": "NEAR WEST COAST OF COLOMBIA", "unid": "20260923_0000277",
                        "lat": 4.96, "lon": -76.66}},
    ],
}


@pytest.fixture
def offline_network(monkeypatch, tmp_path):
    """Deterministic network: USGS/EMSC answers come from fixtures, cache goes to tmp."""
    import quakemind_engine as engine

    def fake_get(url, *args, **kwargs):
        if "seismicportal" in url:
            return _FakeResponse(EMSC_FIXTURE)
        return _FakeResponse(USGS_FIXTURE)

    monkeypatch.setattr(engine.requests, "get", fake_get)
    monkeypatch.setattr(engine, "CACHE_FILE", str(tmp_path / "cache.json"))
    return engine


class TestDataIngestionFallback:

    def test_fetch_earthquakes_returns_list(self, offline_network):
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

    def test_fetch_emsc_returns_list(self, offline_network):
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

    def test_multi_source_returns_list(self, offline_network):
        quakes = fetch_multi_source("day_45", timeout=10)
        assert isinstance(quakes, list)
        assert len(quakes) > 0

    def test_multi_source_merges_same_quake_from_two_agencies(self, offline_network):
        # USGS (us7000test) and EMSC (20260923_0000277) describe the same event with different
        # ids; align the fixture times to check the spatio-temporal merge.
        usgs = fetch_global_earthquakes("day_45")
        emsc = fetch_emsc_earthquakes()
        emsc[0]["time_epoch"] = usgs[0]["time_epoch"] + 20000
        merged = _deduplicate_quakes(usgs, emsc)
        assert len(merged) == 1
        assert merged[0]["source"] == "USGS"

    def test_emsc_depth_is_positive(self, offline_network):
        # EMSC encodes Z as negative depth; the engine must read 103 km, not -103 (-> 1 km)
        q = fetch_emsc_earthquakes()[0]
        assert q["depth_km"] == 103.0
        assert q["source"] == "EMSC"
        assert q["time_epoch"] == 1790196951800

    def test_network_failure_uses_labeled_offline_sample(self, monkeypatch, tmp_path):
        import quakemind_engine as engine

        def boom(*a, **k):
            raise engine.requests.ConnectionError("offline")

        monkeypatch.setattr(engine.requests, "get", boom)
        monkeypatch.setattr(engine, "CACHE_FILE", str(tmp_path / "missing.json"))
        quakes = engine.fetch_global_earthquakes("day_45")
        assert quakes and all(q["source"] == engine.OFFLINE_SAMPLE_SOURCE for q in quakes)
        assert engine.fetch_emsc_earthquakes() == []

    def test_cache_used_when_network_drops(self, monkeypatch, tmp_path):
        import quakemind_engine as engine
        monkeypatch.setattr(engine, "CACHE_FILE", str(tmp_path / "cache.json"))
        monkeypatch.setattr(engine.requests, "get", lambda *a, **k: _FakeResponse(USGS_FIXTURE))
        engine.fetch_global_earthquakes("day_45")

        def boom(*a, **k):
            raise engine.requests.ConnectionError("offline")

        monkeypatch.setattr(engine.requests, "get", boom)
        quakes = engine.fetch_global_earthquakes("day_45")
        assert quakes[0]["id"] == "us7000test"
        assert quakes[0]["source"] == "USGS"


@pytest.mark.skipif(os.environ.get("RUN_NETWORK_TESTS") != "1", reason="live API smoke test (set RUN_NETWORK_TESTS=1)")
class TestLiveFeedsSmoke:

    def test_live_usgs_and_emsc(self):
        assert fetch_global_earthquakes("day_45", timeout=10)
        live = fetch_emsc_earthquakes(limit=5, min_mag=2.0, timeout=10)
        assert all(q["depth_km"] >= 0 for q in live)


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


class TestDynamicLocationTabAndRadialSpeed:
    """Verifies the dynamic user location tab and radial micro-query alerting."""

    @classmethod
    def setup_class(cls):
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        with open(os.path.join(repo_root, "pwa", "index.html"), "r", encoding="utf-8") as f:
            cls.html_content = f.read()
        with open(os.path.join(repo_root, "pwa", "sw.js"), "r", encoding="utf-8") as f:
            cls.sw_content = f.read()

    def test_dynamic_tab_functions_present_in_html(self):
        assert "function updateUserLocationTab" in self.html_content
        assert "function fetchLocalRadialAlerts" in self.html_content
        assert "function startLocalRadialPolling" in self.html_content
        assert "function stopLocalRadialPolling" in self.html_content
        assert "pillMyLocation" in self.html_content

    def test_my_location_i18n_strings_present(self):
        assert "pulseRegMyZone" in self.html_content
        assert "pulseMyZoneCalm" in self.html_content
        assert "📍 Mi Zona" in self.html_content
        assert "📍 My Zone" in self.html_content

    def test_radial_query_url_and_drift_correction(self):
        assert "fdsnws/event/1/query?format=geojson" in self.html_content
        assert "maxradiuskm=750" in self.html_content
        assert "serverTimeDriftMs" in self.html_content

    def test_my_location_region_filtering_logic(self):
        # Test simulated logic: user in Cali (3.4516, -76.5320)
        user_lat, user_lon = 3.4516, -76.5320
        user_country = "colombia"

        # Quake in Popayan (~110 km from Cali)
        popayan_dist = haversine_distance(user_lat, user_lon, 2.4419, -76.6063)
        assert popayan_dist <= 750.0  # within radial threshold

        # Quake in Tokyo (~14,000 km)
        tokyo_dist = haversine_distance(user_lat, user_lon, 35.6762, 139.6503)
        assert tokyo_dist > 750.0
        assert user_country not in "japan, tokyo".lower()

    def test_service_worker_bypasses_usgs_and_radial_feeds(self):
        assert "event.request.url.includes('earthquake.usgs.gov')" in self.sw_content
        assert "event.request.url.includes('seismicportal.eu')" in self.sw_content
        assert re.search(r"centinela-cache-v\d+", self.sw_content)
        assert "./seismic-core.js" in self.sw_content




class TestIntensityPredictionEquation:
    """Allen, Wald & Worden (2012) Rhypo IPE — values checked against the OpenQuake formula."""

    @pytest.mark.parametrize("mag,rhypo,expected", [
        (7.0, 10.0, 8.0293), (7.0, 100.0, 5.6632), (5.0, 20.0, 5.0182), (6.0, 50.0, 5.1604),
    ])
    def test_reference_values(self, mag, rhypo, expected):
        assert abs(allen2012_mmi_raw(mag, rhypo) - expected) < 0.01

    def test_sigma_decreases_with_distance(self):
        assert abs(mmi_sigma(0.0) - 1.19) < 1e-9
        assert mmi_sigma(10) > mmi_sigma(300) > 0.82

    def test_deep_event_is_less_intense(self):
        shallow = calculate_attenuation_mmi(6.0, hypocentral_distance(20, 10))
        deep = calculate_attenuation_mmi(6.0, hypocentral_distance(20, 150))
        assert shallow - deep > 1.5

    def test_perceived_shaking_reports_uncertainty(self):
        eq = {"title": "t", "mag": 6.0, "depth_km": 30.0, "lat": 3.6, "lon": -76.5}
        rep = compute_perceived_shaking(3.4516, -76.5320, eq, lang="es")
        lo, hi = rep["mmi_range"]
        assert lo < rep["mmi_estimated"] < hi


class TestAlertDecision:
    NOW = 1_800_000_000_000

    def test_incoming(self):
        eq = {"lat": 4.53, "lon": -76.53, "depth_km": 15.0, "mag": 6.5, "time_epoch": self.NOW - 10_000}
        a = assess_event(eq, 3.4516, -76.5320, now_ms=self.NOW)
        assert a["level"] == "incoming"
        assert 20 < a["remaining_sec"] < 30

    def test_felt_after_wave_passed(self):
        eq = {"lat": 3.6, "lon": -76.5, "depth_km": 20.0, "mag": 6.0, "time_epoch": self.NOW - 180_000}
        assert assess_event(eq, 3.4516, -76.5320, now_ms=self.NOW)["level"] == "felt"

    def test_calm_and_none(self):
        small = {"lat": 5.7, "lon": -76.53, "depth_km": 30.0, "mag": 3.0, "time_epoch": self.NOW}
        tokyo = {"lat": 35.68, "lon": 139.65, "depth_km": 30.0, "mag": 6.8, "time_epoch": self.NOW}
        assert assess_event(small, 3.4516, -76.5320, now_ms=self.NOW)["level"] == "calm"
        assert assess_event(tokyo, 3.4516, -76.5320, now_ms=self.NOW)["level"] == "none"

    def test_emsc_websocket_payload_normalization(self):
        feat = {"geometry": {"coordinates": [-76.6, 4.9, -60.0]},
                "properties": {"time": "2026-09-23T20:55:51", "mag": "4.8", "unid": "u1", "flynn_region": "COLOMBIA"}}
        q = normalize_emsc_feature(feat)
        assert q["depth_km"] == 60.0 and q["mag"] == 4.8 and q["id"] == "u1"
        assert q["time_epoch"] == 1790196951000


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js not installed")
class TestPythonJavaScriptParity:
    """The PWA (seismic-core.js) and the Python engine must produce identical science."""

    def test_random_cases_match(self):
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        rng = random.Random(42)
        now = 1_800_000_000_000
        cases = []
        for i in range(200):
            ulat, ulon = rng.uniform(-60, 60), rng.uniform(-180, 180)
            near = i < 100  # half the cases near the user so every alert level is exercised
            cases.append({
                "lat": ulat + rng.uniform(-3, 3) if near else rng.uniform(-60, 60),
                "lon": ulon + rng.uniform(-3, 3) if near else rng.uniform(-180, 180),
                "depth": rng.uniform(0, 300), "mag": rng.uniform(2.0, 9.0),
                "time": now - rng.randint(0, 1_200_000), "ulat": ulat, "ulon": ulon,
            })

        script = (
            "const core=require(process.argv[1]);let d='';process.stdin.on('data',c=>d+=c);"
            "process.stdin.on('end',()=>{const out=JSON.parse(d).map(c=>{"
            "const a=core.assessEvent({lat:c.lat,lon:c.lon,depth:c.depth,mag:c.mag,time:c.time},c.ulat,c.ulon,{nowMs:%d});"
            "return [a.mmi,a.hypoKm,a.remainingSec,a.level,a.mmiSigma];});process.stdout.write(JSON.stringify(out));});" % now
        )
        res = subprocess.run(["node", "-e", script, os.path.join(repo_root, "pwa", "seismic-core.js")],
                             input=json.dumps(cases), capture_output=True, text=True, encoding="utf-8", check=True)
        levels = set()
        for c, (mmi, hypo, rem, level, sigma) in zip(cases, json.loads(res.stdout)):
            py = assess_event({"lat": c["lat"], "lon": c["lon"], "depth_km": c["depth"], "mag": c["mag"],
                               "time_epoch": c["time"]}, c["ulat"], c["ulon"], now_ms=now)
            assert math.isclose(py["mmi"], mmi, abs_tol=1e-9)
            assert math.isclose(py["hypo_km"], hypo, abs_tol=1e-6)
            assert math.isclose(py["remaining_sec"], rem, abs_tol=1e-6)
            assert math.isclose(py["mmi_sigma"], sigma, abs_tol=1e-12)
            assert py["level"] == level
            levels.add(level)
        assert {"incoming", "felt", "calm", "none"} <= levels
