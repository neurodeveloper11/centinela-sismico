"""
quakemind_engine.py - Core Geophysical, Attenuation & Psychological Engine for QuakeMind Global.
Author: Fabio Ignacio Torres Benítez (Psychologist & Data / AI Engineer)
License: MIT
"""

import math
import json
import os
import time
from typing import List, Dict, Any, Tuple, Optional
import requests

from i18n import get_text

# Cache file path for offline resilience
CACHE_FILE = os.path.join(os.path.dirname(__file__), "cache_quakes.json")

# USGS GeoJSON endpoints
USGS_FEEDS = {
    "hour": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson",
    "day_all": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson",
    "day_45": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_day.geojson",
    "month_sig": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_month.geojson",
}


# =====================================================================
# 1. GEOPHYSICAL DATA INGESTION & PARSING
# =====================================================================

def fetch_global_earthquakes(feed_key: str = "day_45", timeout: int = 8) -> List[Dict[str, Any]]:
    """
    Fetch real-time earthquakes from USGS with timeout handling and local cache fallback.
    Returns a cleaned list of earthquake dictionaries.
    """
    url = USGS_FEEDS.get(feed_key, USGS_FEEDS["day_45"])
    data = None
    
    try:
        response = requests.get(url, timeout=timeout, headers={"User-Agent": "QuakeMind-Global/1.0"})
        if response.status_code == 200:
            data = response.json()
            # Update local cache
            try:
                with open(CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f)
            except Exception:
                pass
    except Exception:
        # Fallback to local cache if network fails
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = None

    if not data or "features" not in data:
        return _get_fallback_mock_earthquakes()

    parsed_quakes = []
    for feat in data.get("features", []):
        props = feat.get("properties", {})
        geom = feat.get("geometry", {})
        coords = geom.get("coordinates", [0.0, 0.0, 0.0])
        
        mag = props.get("mag")
        if mag is None:
            continue
            
        quake_obj = {
            "id": feat.get("id", str(time.time())),
            "title": props.get("title", "Earthquake"),
            "place": props.get("place", "Unknown Location"),
            "mag": round(float(mag), 1),
            "mag_type": props.get("magType", "Mw"),
            "time_epoch": props.get("time", 0),
            "time_iso": time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(props.get("time", 0) / 1000.0)),
            "lon": float(coords[0]),
            "lat": float(coords[1]),
            "depth_km": round(float(coords[2]), 1),
            "url": props.get("url", ""),
            "alert": props.get("alert") or "none",
            "felt": props.get("felt") or 0,
            "mmi_usgs": props.get("mmi"),
            "tsunami": props.get("tsunami", 0) == 1
        }
        parsed_quakes.append(quake_obj)
        
    return parsed_quakes


def _get_fallback_mock_earthquakes() -> List[Dict[str, Any]]:
    """Safe fallback containing recent historical reference quakes in case of zero internet."""
    return [
        {
            "id": "mock-choco-2026",
            "title": "M 7.4 - San José del Palmar, Chocó, Colombia",
            "place": "12 km W of San José del Palmar, Colombia",
            "mag": 7.4,
            "mag_type": "Mw",
            "time_epoch": 1786377600000,
            "time_iso": "2026-08-10 14:32:10 UTC",
            "lon": -76.6500,
            "lat": 4.9500,
            "depth_km": 103.0,
            "url": "https://earthquake.usgs.gov",
            "alert": "orange",
            "felt": 1420,
            "mmi_usgs": 7.2,
            "tsunami": False
        },
        {
            "id": "mock-venezuela-2026",
            "title": "M 7.5 - Near San Felipe, Yaracuy, Venezuela",
            "place": "18 km E of San Felipe, Venezuela",
            "mag": 7.5,
            "mag_type": "Mw",
            "time_epoch": 1782297600000,
            "time_iso": "2026-06-24 18:45:00 UTC",
            "lon": -68.7400,
            "lat": 10.3300,
            "depth_km": 18.5,
            "url": "https://earthquake.usgs.gov",
            "alert": "red",
            "felt": 2890,
            "mmi_usgs": 8.0,
            "tsunami": False
        },
        {
            "id": "mock-japan-2024",
            "title": "M 7.5 - Noto Peninsula, Ishikawa, Japan",
            "place": "42 km NE of Anamizu, Japan",
            "mag": 7.5,
            "mag_type": "Mw",
            "time_epoch": 1704100200000,
            "time_iso": "2024-01-01 07:10:00 UTC",
            "lon": 137.2400,
            "lat": 37.5000,
            "depth_km": 10.0,
            "url": "https://earthquake.usgs.gov",
            "alert": "red",
            "felt": 3500,
            "mmi_usgs": 8.5,
            "tsunami": True
        }
    ]


# =====================================================================
# 2. GEODESIC DISTANCE & GROUND MOTION ATTENUATION (GMPE / MMI)
# =====================================================================

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points on Earth in kilometers."""
    R = 6371.0  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2.0) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 1)


def hypocentral_distance(epicentral_dist_km: float, depth_km: float) -> float:
    """Calculate 3D hypocentral slant distance: R = sqrt(D^2 + h^2)."""
    return round(math.sqrt(epicentral_dist_km ** 2 + max(depth_km, 1.0) ** 2), 1)


def calculate_attenuation_mmi(magnitude: float, hypocentral_dist_km: float) -> float:
    """
    Calculate estimated local Modified Mercalli Intensity (MMI)
    using calibrated crustal attenuation relationship (Wald et al. / Worden et al.).
    Formula: MMI = 1.5 * M - 2.5 * log10(R) + 1.2
    Clamped strictly between 1.0 (imperceptible) and 12.0 (extreme).
    """
    R = max(hypocentral_dist_km, 3.0)  # avoid singularity at R -> 0
    raw_mmi = 1.5 * magnitude - 2.5 * math.log10(R) + 1.2
    return round(max(1.0, min(12.0, raw_mmi)), 1)


def get_mmi_description(mmi_val: float, lang: str = "es") -> Dict[str, Any]:
    """
    Translate numerical MMI into clear human-centered impact and perception descriptions.
    """
    val = round(mmi_val)
    
    table_es = {
        1: ("I. Imperceptible", "No sentido. Registrado únicamente por sismógrafos sensibles.", "Sin ningún efecto sobre estructuras.", "#4CAF50"),
        2: ("II. Débil", "Sentido por muy pocas personas en reposo, especialmente en pisos altos.", "Sin daño.", "#8BC34A"),
        3: ("III. Leve", "Sentido en interiores. Muchas personas no lo reconocen como sismo. Objetos colgantes oscilan levemente.", "Sin daño alguno.", "#CDDC39"),
        4: ("IV. Moderado", "Sentido por la mayoría en interiores. Vajillas, puertas y ventanas vibran. Sensación similar al paso de un camión pesado.", "Sin daño estructural.", "#FFEB3B"),
        5: ("V. Poco Fuerte", "Sentido por casi todos; muchos se despiertan. Vajillas o vidrios se rompen; objetos inestables caen.", "Fisuras muy leves en yeso o estuco.", "#FFC107"),
        6: ("VI. Fuerte", "Sentido por todos; muchas personas se asustan y salen. Muebles pesados se desplazan; caída de revoques.", "Daño leve en estructuras ordinarias.", "#FF9800"),
        7: ("VII. Muy Fuerte", "Dificultad para mantenerse en pie. Todos corren al exterior. Daño despreciable en edificios de buen diseño sismorresistente.", "Daño moderado a considerable en construcciones deficientes.", "#FF5722"),
        8: ("VIII. Destructivo", "Pánico general. Choferes pierden control. Daño considerable en estructuras ordinarias con colapso parcial.", "Gran daño en estructuras no sismorresistentes. Caída de chimeneas y muros.", "#F44336"),
        9: ("IX. Ruinoso", "Pánico extremo. Edificios de buen diseño sufren daño considerable; estructuras de madera se desencajan.", "Colapso de muchas estructuras de mampostería. Tuberías subterráneas rotas.", "#D32F2F"),
        10: ("X. Desastroso", "Destrucción de la mayoría de obras de mampostería. Puentes destruidos; deslizamientos de tierra y diques agrietados.", "Graves daños en infraestructuras y vías.", "#B71C1C"),
        11: ("XI. Muy Desastroso", "Pocas estructuras de mampostería quedan en pie. Puentes colapsados; grietas anchas en el suelo.", "Colapso casi total de servicios.", "#880E4F"),
        12: ("XII. Catastrófico", "Destrucción total. Ondas visibles en el suelo. Objetos lanzados al aire por aceleración vertical superior a la gravedad.", "Devastación completa del paisaje.", "#4A148C")
    }
    
    table_en = {
        1: ("I. Imperceptible", "Not felt except by very few under especially favorable conditions.", "No structural effect.", "#4CAF50"),
        2: ("II. Weak", "Felt only by a few persons at rest, especially on upper floors.", "No structural damage.", "#8BC34A"),
        3: ("III. Light", "Felt indoors. Hanging objects swing. Vibration like passing of light truck.", "No damage.", "#CDDC39"),
        4: ("IV. Moderate", "Felt indoors by many, outdoors by few. Dishes, windows, doors disturbed.", "No structural damage.", "#FFEB3B"),
        5: ("V. Rather Strong", "Felt by nearly everyone; many awakened. Some dishes, windows broken.", "Very slight hairline cracks in plaster.", "#FFC107"),
        6: ("VI. Strong", "Felt by all; many frightened. Heavy furniture moved; a few instances of fallen plaster.", "Slight damage to poorly built buildings.", "#FF9800"),
        7: ("VII. Very Strong", "Everyone runs outdoors. Damage negligible in buildings of good design and construction.", "Considerable damage in poorly built structures.", "#FF5722"),
        8: ("VIII. Destructive", "Damage slight in specially designed structures; considerable in ordinary substantial buildings.", "Partial collapse in unreinforced masonry.", "#F44336"),
        9: ("IX. Violent", "Damage considerable in specially designed structures; buildings shifted off foundations.", "Well-designed frame structures thrown out of plumb.", "#D32F2F"),
        10: ("X. Very Violent", "Some well-built wooden structures destroyed; most masonry and frame structures destroyed.", "Rails bent. Landslides considerable.", "#B71C1C"),
        11: ("XI. Extreme", "Few, if any, masonry structures remain standing. Bridges destroyed. Broad fissures in ground.", "Total failure of underground utilities.", "#880E4F"),
        12: ("XII. Cataclysmic", "Total destruction. Objects thrown upward into the air. Ground surface waves seen.", "Complete landscape devastation.", "#4A148C")
    }

    ref = table_es if lang == "es" else table_en
    capped_val = max(1, min(12, val))
    title, perception, structural, color = ref[capped_val]
    
    return {
        "mmi_number": mmi_val,
        "roman_title": title,
        "perception": perception,
        "structural_impact": structural,
        "color_hex": color
    }


def compute_perceived_shaking(user_lat: float, user_lon: float, eq: Dict[str, Any], lang: str = "es") -> Dict[str, Any]:
    """Calculate full impact report for a given user location and earthquake."""
    dist_km = haversine_distance(user_lat, user_lon, eq["lat"], eq["lon"])
    hypo_km = hypocentral_distance(dist_km, eq["depth_km"])
    mmi_val = calculate_attenuation_mmi(eq["mag"], hypo_km)
    desc = get_mmi_description(mmi_val, lang=lang)
    
    return {
        "earthquake_title": eq["title"],
        "magnitude": eq["mag"],
        "depth_km": eq["depth_km"],
        "epicentral_dist_km": dist_km,
        "hypocentral_dist_km": hypo_km,
        "mmi_estimated": mmi_val,
        "mmi_title": desc["roman_title"],
        "human_perception": desc["perception"],
        "structural_risk": desc["structural_impact"],
        "color_hex": desc["color_hex"]
    }


# =====================================================================
# 3. PSYCHOLOGICAL FIRST AID (PAP) & NEUROLOGICAL CRISIS DE-ESCALATION
# =====================================================================

def get_pap_guidance(lang: str = "es") -> Dict[str, Any]:
    """
    Returns structured Psychological First Aid (PAP) protocol based on WHO/PAHO guidelines
    and the ABCDE crisis intervention model.
    """
    if lang == "es":
        return {
            "title": "Protocolo ABCDE de Primeros Auxilios Psicológicos (PAP)",
            "subtitle": "Intervención neurocognitiva para regular el sistema nervioso simpático tras un sismo",
            "steps": [
                {
                    "step": "A",
                    "name": "Escucha Activa y Enraizamiento Sensorial (Grounding 5-4-3-2-1)",
                    "objective": "Desactivar la disociación, la despersonalización y la visión de túnel del pánico.",
                    "instructions": [
                        "Dile a la persona o repítete a ti mismo con voz firme y suave: 'Estás a salvo ahora, el temblor terminó. Mírame a los ojos'.",
                        "Nombra 5 cosas visibles a tu alrededor (el color de una pared, una puerta, un zapato).",
                        "Toca 4 texturas concretas (tus pantalones, la suela de tu calzado, una mesa firme).",
                        "Escucha e identifica 3 sonidos reales en el ambiente.",
                        "Identifica 2 olores presentes.",
                        "Di 1 palabra de calma o recuerda el nombre de tu lugar seguro."
                    ]
                },
                {
                    "step": "B",
                    "name": "Reentrenamiento de la Respiración (Freno Vagal Parasimpático)",
                    "objective": "Detener la hiperventilación que causa alcalosis respiratoria, mareo, temblor muscular y desmayos.",
                    "instructions": [
                        "Realiza Suspiros Cíclicos: Inhala por la nariz en 4 segundos, haz una pausa de 4 segundos, y exhala lentamente por la boca en 7 segundos.",
                        "Repite este ciclo 6 veces seguidas (60 segundos en total).",
                        "Coloca una mano sobre el abdomen para asegurar que se infle el diafragma y no el pecho superior."
                    ]
                },
                {
                    "step": "C",
                    "name": "Categorización de Necesidades Inmediatas (Triage Operativo)",
                    "objective": "Reducir la sobrecarga cognitiva enfocando la mente en prioridades de supervivencia.",
                    "instructions": [
                        "Prioridad 1: ¿Hay hemorragias o personas atrapadas? Si sí, atiende o pide auxilio.",
                        "Prioridad 2: ¿Huele a gas o hay chispas eléctricas? Cierra las llaves de paso y no prendas fósforos ni interruptores.",
                        "Prioridad 3: ¿La estructura muestra daños severos? Evacúa a zona despejada.",
                        "Prioridad 4: Las pertenencias materiales y llamadas no urgentes quedan en pausa absoluta."
                    ]
                },
                {
                    "step": "D",
                    "name": "Derivación a Redes de Apoyo y Comunicación Responsable",
                    "objective": "Evitar la saturación de telecomunicaciones y reconectar con seres queridos.",
                    "instructions": [
                        "Envía un único mensaje de texto o SMS a tu grupo familiar: 'ESTOY BIEN en [Lugar]. Evitemos llamadas para no saturar las líneas'.",
                        "No compartas audios reenviados de pánico ni fotos sin confirmar.",
                        "Conéctate con un vecino o brigadista para actuar en comunidad y no en aislamiento."
                    ]
                },
                {
                    "step": "E",
                    "name": "Psicoeducación (Normalización de Respuestas Biológicas)",
                    "objective": "Prevenir el desarrollo de Trastorno de Estrés Postraumático (TEPT).",
                    "instructions": [
                        "Es COMPLETAMENTE NORMAL sentir temblores involuntarios en piernas o brazos durante las siguientes 2 horas. Es la descarga de adrenalina del cuerpo.",
                        "La sensación de 'mareo sísmico' o sentir que el piso se sigue moviendo es una ilusión vestibular normal del oído interno.",
                        "El llanto, el silencio o la irritabilidad son respuestas adaptativas de descarga emocional. No las reprimas."
                    ]
                }
            ]
        }
    else:
        return {
            "title": "ABCDE Protocol for Psychological First Aid (PAP)",
            "subtitle": "Neurocognitive intervention to regulate the sympathetic nervous system post-earthquake",
            "steps": [
                {
                    "step": "A",
                    "name": "Active Listening & Sensory Grounding (5-4-3-2-1 Technique)",
                    "objective": "Break dissociation, depersonalization, and panic tunnel vision.",
                    "instructions": [
                        "Tell yourself or the person firmly and calmly: 'You are safe right now, the shaking stopped. Look at me'.",
                        "Name 5 things you can clearly SEE.",
                        "Touch 4 physical textures (your clothes, the ground beneath your feet, a solid doorframe).",
                        "Identify 3 distinct sounds in your environment.",
                        "Detect 2 real smells.",
                        "Recall 1 comforting memory or say your anchor safe word."
                    ]
                },
                {
                    "step": "B",
                    "name": "Breathing Retraining (Vagal Parasympathetic Brake)",
                    "objective": "Stop hyperventilation that triggers respiratory alkalosis, trembling, and fainting.",
                    "instructions": [
                        "Practice Cyclic Sighing: Inhale through the nose for 4s, hold for 4s, exhale slowly through the mouth for 7s.",
                        "Repeat this rhythm for 6 full cycles (60 seconds total).",
                        "Place your palm over your belly to ensure deep diaphragmatic expansion."
                    ]
                },
                {
                    "step": "C",
                    "name": "Categorization of Immediate Needs (Crisis Triage)",
                    "objective": "Eliminate cognitive overload by isolating actionable survival priorities.",
                    "instructions": [
                        "Priority 1: Are there active bleeding injuries or trapped individuals? Apply direct pressure or call rescue.",
                        "Priority 2: Do you smell gas or see sparks? Turn off main valves; do not touch light switches.",
                        "Priority 3: Is there structural damage? Evacuate immediately to open ground.",
                        "Priority 4: Material belongings and social media scrolling are paused."
                    ]
                },
                {
                    "step": "D",
                    "name": "Derivation to Support Networks & Responsible Comms",
                    "objective": "Prevent cellular network congestion and re-establish safety anchors.",
                    "instructions": [
                        "Send a single brief SMS/text: 'I AM SAFE at [Location]. Keep lines open for emergency services'.",
                        "Do NOT forward unverified WhatsApp voice notes or dramatic photos.",
                        "Pair up with a neighbor or coworker to avoid isolated shock."
                    ]
                },
                {
                    "step": "E",
                    "name": "Psychoeducation (Normalizing Acute Stress Reactions)",
                    "objective": "Prevent secondary psychological trauma and somatic panic.",
                    "instructions": [
                        "It is ENTIRELY NORMAL to experience involuntary limb trembling. This is your body motor-discharging excess adrenaline.",
                        "Feeling 'phantom earthquakes' or floor sway is a common vestibular illusion of the inner ear.",
                        "Crying, sudden silence, or nausea are natural survival discharge responses. Allow them to pass without judgment."
                    ]
                }
            ]
        }


# =====================================================================
# 4. ATC-20 CITIZEN STRUCTURAL DAMAGE TRIAGE
# =====================================================================

def evaluate_structural_safety(element: str, crack_type: str, gas_water_issue: bool, lang: str = "es") -> Dict[str, Any]:
    """
    Standardized post-earthquake safety assessment based on ATC-20 (Applied Technology Council)
    and Colombian NSR-10 / Venezuelan COVENIN guidelines.
    Returns Tag (Green/Yellow/Red), safety classification, and clear instructions.
    """
    # Red Tag conditions (Immediate Unsafe Hazard)
    is_red = (
        gas_water_issue or
        crack_type in ["crack_diagonal", "crack_spalling", "crack_tilt"] or
        (element in ["elem_column", "elem_beam"] and crack_type not in ["crack_hairline"])
    )
    
    # Yellow Tag conditions (Restricted Use / Inspection Needed)
    is_yellow = (
        not is_red and
        (crack_type == "crack_horizontal" or (element in ["elem_column", "elem_beam"] and crack_type == "crack_hairline"))
    )

    if is_red:
        tag = "RED"
        color = "#D32F2F"
        if lang == "es":
            title = "🔴 ETIQUETA ROJA: ESTRUCTURA INSEGURA — EVACUACIÓN INMEDIATA"
            recommendation = (
                "NO PERMANEZCAS DENTRO DE LA EDIFICACIÓN. Existe riesgo inminente de colapso ante réplicas "
                "o peligro de explosión/asfixia por servicios públicos dañados."
            )
            actions = [
                "Evacúa a todos los ocupantes con calma y dirígete a un punto de encuentro en campo abierto.",
                "Cierra la llave de paso principal de gas y corta el interruptor general de energía eléctrica si puedes hacerlo en la ruta de salida sin arriesgarte.",
                "No uses fósforos, velas ni interruptores de luz.",
                "Coloca un aviso en la puerta: 'PELIGRO - NO INGRESAR' y notifica a los bomberos o defensa civil.",
                "No permitas que nadie ingrese a recoger pertenencias hasta que ingenieros estructurales certificados lo autoricen."
            ]
        else:
            title = "🔴 RED TAG: UNSAFE STRUCTURE — IMMEDIATE EVACUATION"
            recommendation = (
                "DO NOT REMAIN INSIDE THE BUILDING. Significant hazard of collapse during aftershocks "
                "or risk of fire/explosion from compromised utilities."
            )
            actions = [
                "Evacuate all occupants calmly to an open assembly area away from facades and power lines.",
                "Shut off main gas and electrical breakers if accessible along your exit route without delay.",
                "Do NOT ignite matches, lighters, or toggle light switches.",
                "Post a prominent warning: 'UNSAFE - DO NOT ENTER' and contact emergency emergency rescue.",
                "Do not re-enter to retrieve personal possessions until certified structural engineers clear the building."
            ]
    elif is_yellow:
        tag = "YELLOW"
        color = "#FFA000"
        if lang == "es":
            title = "🟡 ETIQUETA AMARILLA: USO RESTRINGIDO — PRECAUCIÓN"
            recommendation = (
                "La edificación presenta daños moderados o grietas no críticas que requieren inspección técnica. "
                "El acceso debe ser limitado y temporal."
            )
            actions = [
                "Puedes ingresar brevemente para retirar documentos vitales, medicamentos esenciales y mascotas.",
                "No duermas en habitaciones que tengan muros con fisuras pasantes.",
                "Mantén despejadas las rutas de escape hacia el exterior.",
                "Revisa periódicamente si las fisuras se ensanchan colocando una cinta de papel testigo sobre ellas.",
                "Solicita una evaluación de la alcaldía, gestión del riesgo o un perito estructural antes de habitar con normalidad."
            ]
        else:
            title = "🟡 YELLOW TAG: RESTRICTED USE — EXERCISE CAUTION"
            recommendation = (
                "The building sustained moderate non-critical damage. Structural integrity requires professional inspection. Entry is restricted."
            )
            actions = [
                "Brief entry is permitted only to collect vital documents, emergency prescriptions, and pets.",
                "Do not sleep in rooms displaying through-wall cracking.",
                "Keep all exit corridors completely unobstructed.",
                "Place a paper tape gauge across cracks to monitor if aftershocks cause crack widening.",
                "Request a municipal civil defense or structural engineering evaluation before full reoccupancy."
            ]
    else:
        tag = "GREEN"
        color = "#388E3C"
        if lang == "es":
            title = "🟢 ETIQUETA VERDE: EDIFICACIÓN SEGURA — HABITABLE"
            recommendation = (
                "No se detectan daños estructurales significativos. Las fisuras observadas son de carácter superficial "
                "(acabados, estuco o pintura) y no comprometen la estabilidad del inmueble."
            )
            actions = [
                "La edificación es segura para ser habitada.",
                "Inspecciona con cuidado si cayeron vidrios rotos o adornos pesados.",
                "Verifica que el calentador y tuberías de gas no presenten micro-fugas usando agua con jabón.",
                "Conserva lista la mochila de 72 horas por precaución ante posibles réplicas.",
                "Puedes reparar las fisuras estéticas cuando las autoridades declaren superada la emergencia."
            ]
        else:
            title = "🟢 GREEN TAG: INSPECTED — SAFE TO OCCUPY"
            recommendation = (
                "No apparent structural hazard found. Cracking is superficial (paint or plaster finish) and does not threaten building stability."
            )
            actions = [
                "The structure is safe for ordinary occupancy.",
                "Carefully sweep away broken glassware and secure unstable wall hangings.",
                "Confirm no minor gas leaks exist around appliances using a soap-water bubble test.",
                "Keep your 72-hour survival backpack within arm's reach as a precaution for aftershocks.",
                "Cosmetic repairs can be completed once the active seismic sequence subsides."
            ]

    return {
        "tag": tag,
        "title": title,
        "color_hex": color,
        "recommendation": recommendation,
        "action_steps": actions
    }


# =====================================================================
# 5. SEISMIC MYTH-BUSTER & SCIENCE FACT-CHECKER
# =====================================================================

def debunk_seismic_myth(claim: str, lang: str = "es") -> Dict[str, Any]:
    """
    NLP keyword-based science fact-checker debunking viral earthquake rumors and hoaxes.
    """
    text = claim.lower()
    
    # Myth 1: Deterministic prediction of date/time
    if any(k in text for k in ["predij", "predict", "hora", "hour", "mañana", "tomorrow", "hoy a las", "today at", "fecha"]):
        if lang == "es":
            return {
                "verdict": "❌ FALSO / DESINFORMACIÓN",
                "myth_topic": "Predicción determinista de hora y día de un sismo",
                "scientific_fact": (
                    "La ciencia actual y la física geofísica NO pueden predecir el día, hora exacta ni minuto de un terremoto. "
                    "Las fallas tectónicas acumulan tensión de forma elástica a lo largo de décadas o siglos, pero el punto "
                    "de ruptura inicial es un proceso estocástico no lineal y caótico a kilómetros bajo tierra. Ninguna entidad "
                    "científica oficial (USGS, SGC, FUNVISIS, JMA) emite predicciones horarias. Cualquier mensaje que afirme "
                    "que 'a las 5 PM habrá un terremoto' es un bulo malintencionado que debe ser borrado."
                ),
                "action": "No reenvíes el mensaje. Advierte al remitente con calma para evitar crisis de pánico innecesarias."
            }
        else:
            return {
                "verdict": "❌ FALSE / MISINFORMATION",
                "myth_topic": "Deterministic hour and date earthquake prediction",
                "scientific_fact": (
                    "Neither the USGS nor any global seismological agency can predict the date and time of an earthquake. "
                    "Tectonic faults store elastic strain over centuries, but the microscopic slip nucleation is a non-linear, "
                    "chaotic process miles deep within the crust. Any post or WhatsApp audio claiming an earthquake is scheduled "
                    "for a specific hour is a fabricated hoax."
                ),
                "action": "Do not forward the message. Calmly reassure the sender that deterministic time prediction is physically impossible."
            }

    # Myth 2: Earthquake weather / heat
    if any(k in text for k in ["calor", "heat", "clima", "weather", "temperatura", "bochorno", "sol"]):
        if lang == "es":
            return {
                "verdict": "❌ MITO POPULAR DESMENTIDO",
                "myth_topic": "El calor o bochorno atmosférico produce terremotos",
                "scientific_fact": (
                    "El clima atmosférico ocurre en los primeros kilómetros de la troposfera. Los terremotos se originan "
                    "a profundidades de entre 10 y 600 kilómetros dentro de la litosfera terrestre, donde la temperatura "
                    "supera los 500°C y la presión es inmensa. Los cambios de temperatura ambiental, viento o sol no tienen "
                    "la menor influencia física en los esfuerzos tectónicos de las placas continentales. Los sismos ocurren "
                    "en verano, invierno, lluvia, nieve o sequía por igual."
                ),
                "action": "El bochorno no es señal de temblor. Prepárate siempre teniendo tu plan familiar sin asociarlo al clima."
            }
        else:
            return {
                "verdict": "❌ BUSTED POPULAR MYTH",
                "myth_topic": "Hot or muggy weather causes earthquakes ('Earthquake Weather')",
                "scientific_fact": (
                    "Earthquakes originate kilometers deep inside the rigid lithosphere under thousands of atmospheres of pressure, "
                    "completely isolated from tropospheric weather. Surface air temperature, sun, or rain have zero physical effect "
                    "on tectonic fault friction. Earthquakes occur with equal frequency across all seasons, weather conditions, and climates."
                ),
                "action": "Weather is not a seismic precursor. Keep your emergency preparedness up to date year-round."
            }

    # Myth 3: Animals predicting hours in advance
    if any(k in text for k in ["animal", "perro", "dog", "gato", "cat", "ave", "bird"]):
        if lang == "es":
            return {
                "verdict": "⚠️ VERDAD A MEDIAS / MALINTERPRETADO",
                "myth_topic": "Los animales predicen terremotos con horas de anticipación",
                "scientific_fact": (
                    "Los animales NO tienen un 'sexto sentido' místico para predecir sismos con horas de anticipación. Lo que ocurre "
                    "es que un sismo emite ondas Primarias (ondas P, longitudinales y más rápidas) que viajan a ~6 km/s pero causan poco daño, "
                    "seguidas por las ondas Secundarias (ondas S, transversales y destructivas) que viajan a ~3.5 km/s. Los perros y gatos "
                    "tienen una audición de alta frecuencia mucho más sensible y sienten la onda P unos segundos antes de que los humanos "
                    "perciban la onda S. La ventaja temporal es de apenas unos pocos segundos, nunca horas o días."
                ),
                "action": "Si tu mascota se alarma repentinamente, ponte en alerta, pero no asumas comportamientos cotidianos como alarmas sísmicas."
            }
        else:
            return {
                "verdict": "⚠️ PARTIAL TRUTH / COMMONLY MISUNDERSTOOD",
                "myth_topic": "Animals sensing earthquakes hours in advance",
                "scientific_fact": (
                    "Animals do not possess mystical foresight hours before a quake. Earthquakes emit fast Primary (P) waves "
                    "followed by slower, more destructive Secondary (S) waves. Dogs and cats have high-frequency sensory thresholds "
                    "capable of detecting the P-wave a few seconds before humans feel the heavy shaking of the S-wave. The warning "
                    "window is seconds, never hours or days."
                ),
                "action": "Do not interpret normal pet agitation as a confirmed earthquake forecast."
            }

    # Myth 4: Triangle of Life vs. Drop, Cover and Hold On
    if any(k in text for k in ["triangulo", "triangle", "vida", "life", "agacharse", "drop"]):
        if lang == "es":
            return {
                "verdict": "⚠️ MITO PELIGROSO: EL 'TRIÁNGULO DE LA VIDA' NO ES EL ESTÁNDAR",
                "myth_topic": "El llamado 'Triángulo de la Vida' de Doug Copp",
                "scientific_fact": (
                    "Los organismos internacionales de protección civil (Cruz Roja, FEMA, UNGRD, Protección Civil) desaconsejan el 'Triángulo de la Vida'. "
                    "En edificaciones modernas, la gran mayoría de lesiones y muertes ocurren por objetos pesados que caen (lámparas, vidrios, estantes) "
                    "y por personas arrojadas al suelo mientras intentan correr. El protocolo científicamente validado es: "
                    "AGÁCHATE (Drop), CÚBRETE debajo de un mueble o mesa resistente (Cover) y SUJÉTATE firme hasta que cese el movimiento (Hold On)."
                ),
                "action": "Aplica 'Agáchate, Cúbrete y Sujétate'. Solo si no hay mesas firmes, protégete junto a un muro estructural cubriendo cabeza y cuello."
            }
        else:
            return {
                "verdict": "⚠️ DANGEROUS MYTH: 'TRIANGLE OF LIFE' IS NOT RECOMMENDED",
                "myth_topic": "The 'Triangle of Life' theory",
                "scientific_fact": (
                    "Major disaster agencies worldwide (Red Cross, FEMA, USGS) actively discourage the 'Triangle of Life'. "
                    "In real earthquakes, the overwhelming majority of injuries are caused by falling debris, flying glass, and toppled furniture. "
                    "The universally validated survival protocol is: DROP to your hands and knees, COVER your head and neck under a sturdy table, "
                    "and HOLD ON until shaking ceases."
                ),
                "action": "Follow 'Drop, Cover, and Hold On'. It prevents you from being knocked over and shields you from lethal falling objects."
            }

    # Default scientific answer
    if lang == "es":
        return {
            "verdict": "ℹ️ PRINCIPIO CIENTÍFICO UNIVERSAL",
            "myth_topic": "Física y Geofísica Sísmica",
            "scientific_fact": (
                "La Tierra es un planeta tectónicamente activo. Los sismos son la liberación natural de energía elástica acumulada "
                "por la interacción de las placas litosféricas. No existe tecnología humana ni fenómeno astrológico capaz de detonar "
                "terremotos masivos a voluntad. La única defensa real de la humanidad es la construcción sismorresistente, la educación "
                "comunitaria y la preparación serena."
            ),
            "action": "Verifica siempre la información en fuentes autorizadas (Servicio Geológico Colombiano, FUNVISIS, USGS, Protección Civil)."
        }
    else:
        return {
            "verdict": "ℹ️ UNIVERSAL SCIENTIFIC PRINCIPLE",
            "myth_topic": "Seismic Geophysics & Preparedness",
            "scientific_fact": (
                "Earthquakes are the natural release of accumulated elastic strain along tectonic boundaries. "
                "There is no human technology or planetary alignment that can trigger or predict massive earthquakes at will. "
                "The only proven defense is seismic-resistant building codes, community drills, and composed psychological preparedness."
            ),
            "action": "Always corroborate seismic reports through recognized geological authorities (USGS, EMSC, local geological services)."
        }
