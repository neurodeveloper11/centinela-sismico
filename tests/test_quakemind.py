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
    fetch_global_earthquakes
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
