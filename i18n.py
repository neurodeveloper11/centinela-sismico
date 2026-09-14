"""
i18n.py - Internationalization dictionary for QuakeMind Global (SismoMente Global).
Supports English (en) and Spanish (es) with plug-and-play extensible structure.
"""

TRANSLATIONS = {
    "en": {
        "title": "QuakeMind Global",
        "tagline": "Global Seismic Intelligence, Psychological First Aid (PAP) & Emergency Survival Hub",
        "author_credit": "Designed by Fabio Ignacio Torres Benítez | Open-Source & 100% Free",
        
        # Tabs
        "tab_monitor": "🌍 Live Global Seismic Monitor",
        "tab_pap": "🧠 Psychological First Aid (PAP)",
        "tab_structural": "🏗️ Structural Damage Triage (ATC-20)",
        "tab_mythbuster": "🔍 Seismic Myth-Buster",
        "tab_pwa": "📡 Zero-Network Offline Survival PWA",
        
        # Monitor Tab
        "select_timeframe": "Select USGS Seismic Feed",
        "feed_hour": "Past Hour (All magnitudes)",
        "feed_day_all": "Past Day (All magnitudes)",
        "feed_day_45": "Past Day (Magnitude 4.5+ Global)",
        "feed_month_sig": "Past Month (Significant Global Earthquakes)",
        "refresh_btn": "🔄 Refresh Real-Time Data",
        "user_location_header": "Your Coordinates (or nearest major city)",
        "user_lat": "Latitude (e.g. 3.4516 for Cali, 35.6762 for Tokyo, 40.7128 for NYC)",
        "user_lon": "Longitude (e.g. -76.5320 for Cali, 139.6503 for Tokyo, -74.0060 for NYC)",
        "calc_impact_btn": "⚡ Calculate Perceived Shaking (MMI) for Selected Earthquake",
        "select_quake_label": "Select Earthquake from Feed",
        "result_impact_header": "📊 Local Shaking & Impact Assessment",
        "mmi_label": "Estimated Modified Mercalli Intensity (MMI)",
        "perception_label": "Human Perception at Your Location",
        "structural_risk_label": "Expected Structural Behavior",
        "distance_label": "Hypocentral Distance to Epicenter",
        "depth_label": "Hypocentral Depth",
        
        # PAP Tab
        "pap_title": "Psychological First Aid (PAP) - WHO & ABCDE Protocol",
        "pap_desc": "In acute post-earthquake situations, panic, hyperventilation, and freezing cause severe secondary accidents. Follow these evidence-based cognitive-behavioral steps to regulate the autonomic nervous system.",
        "pacer_title": "🫁 60-Second Autonomic Vagal Breathing Pacer",
        "pacer_desc": "Calibrate your nervous system with Cyclic Sighing (Inhale 4s, Hold 4s, Exhale 7s). Follow the pacer below to trigger parasympathetic vagal braking and lower cortisol.",
        "pacer_btn": "Start Breathing Session",
        "abcde_title": "📋 Step-by-Step ABCDE Crisis Intervention",
        "step_a_title": "A: Active Listening & Sensory Grounding (5-4-3-2-1)",
        "step_a_desc": "Snap out of dissociation and tunnel vision:\n• Name 5 things you can SEE.\n• Name 4 things you can physically FEEL (feet on the floor, texture of clothes).\n• Name 3 things you can HEAR.\n• Name 2 things you can SMELL.\n• Name 1 positive thing you can TASTE or remember.",
        "step_b_title": "B: Breathing Retraining",
        "step_b_desc": "Deep diaphragmatic breathing prevents hyperventilation, which prevents dizziness and fainting.",
        "step_c_title": "C: Categorization of Immediate Needs",
        "step_c_desc": "Do not attempt to solve everything at once. Focus only on:\n1. Severe bleeding or physical injuries (apply direct pressure).\n2. Immediate fire or gas smell (shut valves, evacuate calmly).\n3. Structural instability (head to open ground).\n4. Everything else can wait.",
        "step_d_title": "D: Derivation to Support Networks",
        "step_d_desc": "Keep phone calls under 20 seconds or use SMS/text. Sending heavy videos jams the network for ambulances.",
        "step_e_title": "E: Psychoeducation (Normalizing Trauma Reactions)",
        "step_e_desc": "It is completely normal to experience:\n• Uncontrollable trembling or shivering (motor discharge of adrenaline).\n• Sensation that the ground is still moving ('phantom quakes').\n• Intense nausea or dry mouth.\nThis is your biological survival system discharging energy. It will subside naturally.",

        # Structural Triage Tab
        "triage_title": "ATC-20 Citizen Post-Earthquake Structural Damage Triage",
        "triage_desc": "Use this international standard decision wizard to determine whether it is safe to re-enter your building or if you must evacuate immediately.",
        "element_label": "Where is the damage located?",
        "elem_column": "Main Concrete Column or Pillar",
        "elem_beam": "Horizontal Concrete Beam / Ceiling Joint",
        "elem_wall": "Partition Wall / Brick Drywall",
        "elem_floor": "Floor / Ceiling Slab",
        "crack_type_label": "What does the crack look like?",
        "crack_hairline": "Hairline / Superficial crack (< 1-2 mm, surface plaster/paint only)",
        "crack_horizontal": "Horizontal or Vertical crack along masonry joints (2-5 mm)",
        "crack_diagonal": "Diagonal 'X' crack (45 degrees) crossing structural concrete",
        "crack_spalling": "Concrete crushing / Spalling with visible exposed reinforcing steel rebar",
        "crack_tilt": "Visible leaning or tilting of walls or structural frame",
        "gas_water_label": "Any signs of utility rupture?",
        "gas_yes": "Yes: Smell of gas, sparking wires, or burst water pipe",
        "gas_no": "No utility damage detected",
        "evaluate_triage_btn": "🛡️ Assess Building Safety Level",
        
        # Myth Buster Tab
        "myth_title": "🔍 Seismic Myth-Buster & Science Fact-Checker",
        "myth_desc": "Combat viral panic and fake news during crises. Enter a claim or rumor below to receive a rigorous geophysical verification.",
        "myth_input_placeholder": "e.g., 'A mega 9.0 earthquake was predicted for 7:00 PM tonight' or 'animals always predict earthquakes'",
        "check_myth_btn": "🔬 Verify Claim with Science",
        
        # PWA Tab
        "pwa_title": "📡 Zero-Network Offline Survival PWA",
        "pwa_desc": "During high-magnitude earthquakes, power grids and cellular towers (4G/5G) often fail completely. QuakeMind includes an ultra-lightweight Progressive Web App that works 100% WITHOUT internet once saved.",
        "pwa_feature_1": "🔊 3,500 Hz Web Audio SOS Acoustic Beacon (Pure Morse Code tone to alert rescuers without vocal exhaustion)",
        "pwa_feature_2": "🔦 High-Intensity Screen Distress Strobe for Night Signaling",
        "pwa_feature_3": "🎒 Interactive 72-Hour Survival Backpack Checklist",
        "pwa_feature_4": "💳 Emergency Family Contact Card Generator (Exports to image with zero internet)",
        "launch_pwa_btn": "🚀 Launch Offline Survival PWA"
    },
    
    "es": {
        "title": "QuakeMind Global (SismoMente Global)",
        "tagline": "Inteligencia Sísmica Global, Primeros Auxilios Psicológicos (PAP) y Supervivencia Offline",
        "author_credit": "Diseñado por Fabio Ignacio Torres Benítez | Código Abierto y 100% Gratuito",
        
        # Tabs
        "tab_monitor": "🌍 Monitor Sísmico Global en Tiempo Real",
        "tab_pap": "🧠 Primeros Auxilios Psicológicos (PAP)",
        "tab_structural": "🏗️ Triaje de Daños Estructurales (ATC-20)",
        "tab_mythbuster": "🔍 Cazador de Mitos y Desinformación",
        "tab_pwa": "📡 PWA de Supervivencia Sin Internet (Offline)",
        
        # Monitor Tab
        "select_timeframe": "Seleccionar Fuente Sísmica USGS",
        "feed_hour": "Última Hora (Todas las magnitudes)",
        "feed_day_all": "Últimas 24 Horas (Todas las magnitudes)",
        "feed_day_45": "Últimas 24 Horas (Magnitud 4.5+ Global)",
        "feed_month_sig": "Último Mes (Sismos Significativos Mundiales)",
        "refresh_btn": "🔄 Actualizar Datos en Vivo",
        "user_location_header": "Tus Coordenadas (o ciudad de referencia)",
        "user_lat": "Latitud (ej: 3.4516 para Cali, 4.7110 para Bogotá, 10.4806 para Caracas, 19.4326 para CDMX)",
        "user_lon": "Longitud (ej: -76.5320 para Cali, -74.0721 para Bogotá, -66.9036 para Caracas, -99.1332 para CDMX)",
        "calc_impact_btn": "⚡ Calcular Aceleración e Impacto Percibido (MMI)",
        "select_quake_label": "Selecciona un Sismo de la Lista",
        "result_impact_header": "📊 Evaluación de Impacto y Percepción Local",
        "mmi_label": "Intensidad Mercalli Modificada Estimada (MMI)",
        "perception_label": "Percepción Humana en tu Ubicación",
        "structural_risk_label": "Comportamiento Estructural Esperado",
        "distance_label": "Distancia Hipocentral al Epicentro",
        "depth_label": "Profundidad Hipocentral",
        
        # PAP Tab
        "pap_title": "Primeros Auxilios Psicológicos (PAP) - Estándar OMS y Protocolo ABCDE",
        "pap_desc": "En situaciones agudas post-sismo, el pánico, la hiperventilación y el bloqueo motor causan la mayoría de accidentes graves. Sigue estos pasos cognitivo-conductuales respaldados por la neurobiología para regular el sistema nervioso.",
        "pacer_title": "🫁 Marcapasos de Estimulación Vagal en 60 Segundos",
        "pacer_desc": "Calibra tu sistema nervioso con Suspiros Cíclicos (Inhala 4s, Retén 4s, Exhala 7s). Sigue el ritmo para activar el freno parasimpático y reducir el cortisol de inmediato.",
        "pacer_btn": "Iniciar Sesión de Respiración",
        "abcde_title": "📋 Intervención en Crisis Paso a Paso (Protocolo ABCDE)",
        "step_a_title": "A: Escucha Activa y Enraizamiento Sensorial (Técnica 5-4-3-2-1)",
        "step_a_desc": "Sal de la visión de túnel y la disociación:\n• Nombra 5 cosas que puedas VER a tu alrededor.\n• Nombra 4 cosas que puedas TOCAR o SENTIR (tus pies en el suelo, la textura de tu ropa).\n• Nombra 3 cosas que puedas ESCUCHAR.\n• Nombra 2 cosas que puedas OLER.\n• Nombra 1 recuerdo positivo o sabor que puedas RECORDAR.",
        "step_b_title": "B: Reentrenamiento de la Respiración",
        "step_b_desc": "La respiración diafragmática profunda evita la hiperventilación, suprimiendo los mareos, el hormigueo en las manos y los desmayos por pánico.",
        "step_c_title": "C: Categorización de Necesidades Inmediatas",
        "step_c_desc": "No intentes resolver todo al mismo tiempo. Concéntrate exclusivamente en:\n1. Hemorragias o lesiones físicas urgentes (aplica presión directa).\n2. Fugas de gas o cables con chispas (cierra llaves principales y evacúa con calma).\n3. Peligro de colapso estructural (dirígete a campo abierto).\n4. Todo lo demás puede esperar 30 minutos.",
        "step_d_title": "D: Derivación a Redes de Apoyo",
        "step_d_desc": "Limita las llamadas telefónicas a menos de 20 segundos o envía mensajes SMS/texto. No transmitas videos pesados para no bloquear el paso de llamadas de ambulancias.",
        "step_e_title": "E: Psicoeducación (Normalización de Respuestas de Estrés Agudo)",
        "step_e_desc": "Es totalmente normal y biológico experimentar:\n• Temblores incontrolables en piernas o manos (descarga motora de adrenalina).\n• Sensación de que el suelo sigue vibrando ('sismos fantasma').\n• Náuseas intensas, taquicardia o boca seca.\nEsto es tu sistema nervioso descargando la energía de supervivencia. Se calmará naturalmente en minutos.",

        # Structural Triage Tab
        "triage_title": "Triaje de Daños Estructurales en Viviendas (Estándar ATC-20)",
        "triage_desc": "Asistente de diagnóstico para determinar si es seguro permanecer dentro de tu vivienda o si debes evacuar de inmediato.",
        "element_label": "¿En qué elemento estructural está el daño principal?",
        "elem_column": "Columna o Pilar Principal de Concreto/Hormigón",
        "elem_beam": "Viga Horizontal de Concreto o Unión de Techo",
        "elem_wall": "Pared Divisoria / Muro de Ladrillo o Drywall",
        "elem_floor": "Losa de Piso o Techo",
        "crack_type_label": "¿Qué forma tiene la grieta o fisura?",
        "crack_hairline": "Fisura superficial / cabello (< 1-2 mm, solo estuco o pintura)",
        "crack_horizontal": "Grieta horizontal o vertical a lo largo de juntas de mampostería (2-5 mm)",
        "crack_diagonal": "Grieta diagonal en 'X' (45 grados) atravesando concreto estructural",
        "crack_spalling": "Desprendimiento severo de concreto con varillas de hierro expuestas o pandeadas",
        "crack_tilt": "Inclinación visible de la estructura, paredes o descuadre total de puertas",
        "gas_water_label": "¿Detectas daño en servicios públicos?",
        "gas_yes": "Sí: Olor a gas, cables con chispas o rotura de tubería de agua",
        "gas_no": "No se detecta daño en servicios",
        "evaluate_triage_btn": "🛡️ Evaluar Nivel de Seguridad de la Estructura",
        
        # Myth Buster Tab
        "myth_title": "🔍 Cazador de Mitos y Desinformación Sísmica",
        "myth_desc": "Combate el pánico viral en redes sociales. Ingresa un rumor o afirmación para obtener una respuesta geofísica rigurosa.",
        "myth_input_placeholder": "ej: 'Un sismólogo predijo un terremoto de 9.0 para hoy a las 6 pm' o 'hace mucho calor, seguro va a temblar'",
        "check_myth_btn": "🔬 Verificar Afirmación Científicamente",
        
        # PWA Tab
        "pwa_title": "📡 PWA de Supervivencia Sin Internet (Offline)",
        "pwa_desc": "En sismos de gran magnitud, la energía eléctrica y las antenas celulares 4G/5G colapsan. QuakeMind incluye una Aplicación Web Progresiva ultraligera que funciona 100% SIN internet una vez guardada.",
        "pwa_feature_1": "🔊 Silbato Acústico de Rescate SOS a 3.500 Hz (Tono puro en código Morse generado por Web Audio API para guiar a rescatistas sin fatiga vocal)",
        "pwa_feature_2": "🔦 Baliza Estroboscópica de Alto Contraste para Señalización Nocturna",
        "pwa_feature_3": "🎒 Mochila de las 72 Horas Interactiva con Guardado Local",
        "pwa_feature_4": "💳 Generador de Tarjeta Familiar de Emergencia (Exporta a imagen sin internet)",
        "launch_pwa_btn": "🚀 Abrir PWA de Supervivencia Offline"
    }
}

def get_text(key: str, lang: str = "es") -> str:
    """Retrieve translated string safely with Spanish fallback."""
    lang_dict = TRANSLATIONS.get(lang, TRANSLATIONS["es"])
    return lang_dict.get(key, TRANSLATIONS["es"].get(key, key))
